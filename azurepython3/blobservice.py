import json
import xml.etree.ElementTree as etree
from azurepython3.service import AzureService


class Container:
    def __init__(self, name, url = None, properties = None, metadata = None):
        self.name = name
        self.url = url
        self.properties = properties
        self.metadata = metadata

    @classmethod
    def from_element(self, element : etree.Element):
        container = Container(element.find('Name').text)
        return container


class BlobService(AzureService):

    def __init__(self, account_name, account_key):
        super().__init__(account_name, account_key)

    @classmethod
    def from_config(self, filename):
        with open(filename, "r") as file:
            credentials = json.load(file)

        # create the blob service
        return BlobService(credentials['account_name'], credentials['account_key'])

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

        return [x for x in root.iter('Blob')]

    def create_blob(self, container, name, content):
        """
        Creates a new blob in the destination container (which must exist). Content is expected to be an iterable
        of bytes, such as a bytearray.
        :param container: container name
        :param name: blob name
        :param content: byte content
        """
        headers = { 'x-ms-blob-type': "BlockBlob" }
        response = self._request('put', '/%s/%s' % (container, name), headers=headers, content = content)
        return response.status_code == 201
