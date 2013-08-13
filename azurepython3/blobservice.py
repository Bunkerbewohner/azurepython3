import json
import xml.etree.ElementTree as etree
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

    def list_blobs(self, container, prefix = None, delimiter = None):
        """
        Lists blobs in a container. This implementation does not yet consider markers and maxresults
        for paginated lists of more than 5000 entries.
        :param container: container name
        :param prefix: common blob name prefix
        :param delimiter: allows structuring blobs by delimiters (default: '/')
        """

        query = {
            'restype': 'container',
            'comp': 'list',
            'prefix': prefix,
            'delimiter': delimiter
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
        headers = { 'x-ms-blob-type': "BlockBlob", 'Content-Encoding': content_encoding }
        response = self._request('put', '/%s/%s' % (container, name), headers=headers, content = content)
        return response.status_code == 201 # Created

    def delete_blob(self, container, name):
        response = self._request('delete', '/%s/%s' % (container, name))
        return response.status_code == 202 # Accepted