import json
import mimetypes
import xml.etree.ElementTree as etree
import requests
from requests import HTTPError
from requests.adapters import HTTPAdapter
from azurepython3.service import AzureService


class Container:
    def __init__(self, name, url = None, properties = None, metadata = None):
        self.name = name
        self.url = url
        self.properties = properties if properties != None else {}
        self.metadata = metadata if metadata != None else {}

    @classmethod
    def from_element(cls, element : etree.Element):
        url = element.find('Url').text
        properties = dict([(p.tag, p.text) for p in element.find('Properties')])

        if element.find('Metadata') != None:
            metadata = dict([(e.tag, e.text) for e in element.find('Metadata')])
        else:
            metadata = {}

        container = Container(element.find('Name').text, url, properties, metadata)
        return container


class Blob:
    def __init__(self, name, url = None, properties = None, metadata = None):
        self.name = name
        self.url = url
        self.properties = properties if properties != None else {}
        self.metadata = metadata if metadata != None else {}
        self.content = None

    def content_length(self):
        """ Returns the size of the blob's content in bytes """
        return int(self.properties['Content-Length'])

    def download_text(self, encoding = None):
        """
        Downloads the blob context as text. If no encoding is provided it is determined automatically  based
        on the content-encoding header of the response. Alternatively a specific content encoding can be
        specified through the second argument.
        """
        response = requests.get(self.url)

        if encoding != None:
            response.encoding = encoding
        elif encoding is None and 'Content-Encoding' in self.properties:
            response.encoding = self.properties['Content-Encoding']

        return response.text

    def download_bytes(self):
        """
        Downloads the binary content of the file.
        """
        return requests.get(self.url).content


    @classmethod
    def from_element(cls, element : etree.Element):
        name = element.find('Name').text
        url = element.find('Url').text
        properties = dict([(p.tag, p.text) for p in element.find('Properties')])

        if element.find('Metadata') != None:
            metadata = dict([(e.tag, e.text) for e in element.find('Metadata')])
        else:
            metadata = {}

        return Blob(name, url, properties, metadata)

    def __str__(self):
        return self.url


class BlobService(AzureService):

    def __init__(self, account_name, account_key):
        super().__init__(account_name, account_key)

    @classmethod
    def from_config(self, filename):
        with open(filename, "r") as file:
            credentials = json.load(file)

        # create the blob service
        return BlobService(credentials['account_name'], credentials['account_key'])

    @classmethod
    def discover(cls):
        """
        Searches for an Azure configuration file to take the credentials from. The file must be located within the
        current work directory's subtree and be called 'azurecredentials.json', with contents suitable for the
        BlobService.from_config method.
        """
        import os
        for root, dirs, files in os.walk('.'):
          for file in files:
            if file == 'azurecredentials.json':
              return BlobService.from_config(os.path.join(root, file))

        return None

    def create_container(self, name, access = None):
        """
        :param name: name containing only letters, numbers and dashes
        :param access: container|blob|None
        """
        query = { 'restype': 'container', 'timeout': self.timeout }
        headers = { 'x-ms-blob-public-access': access }
        response = self._request('put', '/' + name, headers, query)
        return response.status_code == 201 # Created

    def delete_container(self, name):
        response = self._request('delete', '/' + name, params = {'restype': 'container'})
        return response.status_code == 202 # Accepted?

    def list_containers(self, prefix=None, metadata=False):
        query = {
            'comp': 'list',
            'prefix': prefix,
            'include': 'metadata' if metadata else None
        }

        response = self._request('get', '/', params=query)
        root = etree.fromstring(response.text)
        assert root.tag == 'EnumerationResults'
        assert root[0].tag == 'Containers'

        # list containers
        # TODO: handle <NextMarker> for paginated results
        return [Container.from_element(x) for x in root.iter('Container')]

    def list_blobs(self, container, prefix = None):
        """
        Lists blobs in a container. This implementation does not yet consider markers and maxresults
        for paginated lists of more than 5000 entries.
        :param container: container name
        :param prefix: common blob name prefix
        """

        query = {
            'restype': 'container',
            'comp': 'list',
            'prefix': prefix if prefix else None
        }

        response = self._request('get', '/' + container, params = query)
        root = etree.fromstring(response.text)

        return [Blob.from_element(x) for x in root.iter('Blob')]

    def create_blob(self, container, name, content, content_encoding = None):
        """
        Creates a new blob in the destination container (which must exist). Content is expected to be an iterable
        of bytes, such as a bytearray.
        :param container: container name
        :param name: blob name
        :param content: byte content
        """
        name = self._sanitize_blobname(name)
        headers = { 'x-ms-blob-type': "BlockBlob", 'Content-Encoding': content_encoding }

        content_type = mimetypes.guess_type(name)[0]
        if content_type != None:
            headers['Content-Type'] = content_type

        response = self._request('put', '/%s/%s' % (container, name), headers=headers, content = content)
        return response.status_code == 201 # Created

    def delete_blob(self, container, name):
        name = self._sanitize_blobname(name)
        response = self._request('delete', '/%s/%s' % (container, name))
        return response.status_code == 202 # Accepted

    def get_blob_url(self, container, name, protocol=None):
        """
        Returns the URL that refers to the blob by this name in the given container.
        """
        return self.get_url('/%s/%s' % (container, name), protocol=protocol)

    def get_blob(self, container, name, with_content = True):
        """
        Gets a blob including its properties and metadata.
        :param with_content: Determines whether the content should be fetched along with the properties and metadata
        """
        name = self._sanitize_blobname(name)

        try:
            response = self._request('get' if with_content else 'head', "/%s/%s" % (container, name))
        except HTTPError as e:
            if e.response.status_code == 404:
                return None
            else:
                raise e

        if response.status_code != 200: # Error
            response.raise_for_status()

        metadata = { key.replace("x-ms-meta-", ""): value for key, value in response.headers.items() if key.startswith('x-ms-meta-')}
        blob = Blob(name, self.get_blob_url(container, name), properties = response.headers, metadata=metadata)

        if with_content:
            blob.content = response.content

        return blob

    def blob_exists(self, container, name):
        url = self.get_blob_url(container, name, protocol='http')
        session = requests.session()
        session.mount('http://', HTTPAdapter(max_retries=5))
        resp = session.head(url)
        return resp.status_code == 200

    def get_blob_content(self, container, name, text = False):
        """
        Directly downloads the content of a blob and by default returns the content as bytes.
        If text is set to True it will return the content as encoded text instead.
        """
        name = self._sanitize_blobname(name)
        blob = Blob(name, self.get_url('/%s/%s' % (container, name)))
        if text:
            return blob.download_text()
        else:
            return blob.download_bytes()

    def enable_cors(self, origins, allowed_methods = None, max_age_seconds = None):
        """
        Enables CORS for all files on the BlobService.
        :param origins: allowed origin domains. Set '*' to allow all domains.
        :type origins: string|list|tuple
        :param allowed_methods: allowed HTTP methods
        :type allowed_methods: string|list|tuple
        :param max_age_seconds: how long to cache preflight answers
        """

        if not allowed_methods:
            allowed_methods = ['GET', 'PUT']

        if not max_age_seconds:
            max_age_seconds = 500

        headers = {
            'x-ms-version': '2013-08-15'
        }

        params = {
            'restype': 'service',
            'comp': 'properties'
        }

        if type(origins) is list or type(origins) is tuple:
            origins = ",".join(origins)

        if type(allowed_methods) is list or type(allowed_methods) is tuple:
            allowed_methods = ",".join(allowed_methods)

        content = '''<?xml version="1.0" encoding="utf-8"?>
            <StorageServiceProperties>
                <Cors>
                    <CorsRule>
                        <AllowedOrigins>{origins}</AllowedOrigins>
                        <AllowedMethods>{methods}</AllowedMethods>
                        <MaxAgeInSeconds>{age}</MaxAgeInSeconds>
                        <ExposedHeaders>x-ms-meta-data*,x-ms-meta-customheader</ExposedHeaders>
                        <AllowedHeaders>x-ms-meta-target*,x-ms-meta-customheader</AllowedHeaders>
                    </CorsRule>
                </Cors>
                <DefaultServiceVersion>{version}</DefaultServiceVersion>
            </StorageServiceProperties>'''.format(origins=origins, age=max_age_seconds,
                                                  methods=allowed_methods, version=headers['x-ms-version'])

        try:
            response = self._request('put', '/', headers, params, content)
        except HTTPError as e:
            raise e

        return response.status_code == 202 # ACCEPTED

    def _sanitize_blobname(self, blobname):
        # on windows paths use backslashes, which is not compatible to URLs. So convert them to slashes.
        return blobname.replace("\\", "/")