"""
This module implements a custom Django storage based on the BlobService.
"""
import os
from tempfile import SpooledTemporaryFile
from requests import HTTPError
from azurepython3.blobservice import BlobService

try:
    from django.core.files.storage import Storage
    from django.conf import settings
except ImportError:
    class Storage:
        pass

    class Settings:
        CUSTOM_STORAGE_OPTIONS = {}

    settings = Settings()

class AzureStorage(Storage):

    def __init__(self, container = None, account_name = None, account_key = None):
        """
        Creates a new AzureStorage. The container is not automatically created and therefore must already exist.
        """
        if container is None:
            if hasattr(settings, 'AZURE_DEFAULT_CONTAINER'):
                self.container = settings.AZURE_DEFAULT_CONTAINER
            else:
                self.container = "$root"
        else:
            self.container = container

        if account_name and account_key:
            self.service = BlobService(account_name, account_key)
        else:
            self.service = BlobService(settings.AZURE_ACCOUNT_NAME, settings.AZURE_ACCOUNT_KEY)

    def _transform_name(self, name):
        return name.replace("\\", "/")

    def _open(self, name, mode = 'rb'):
        name = self._transform_name(name)
        content = self.service.get_blob_content(self.container, name)
        file = SpooledTemporaryFile()
        file.write(content)
        file.seek(0) # explicitly reset to allow reading from the beginning afterwards as-is
        return file

    def _save(self, name, content):
        name = self._transform_name(name)
        content.open(mode='rb')
        data = bytearray(content.read())
        self.service.create_blob(self.container, name, data)
        return name

    def delete(self, name):
        name = self._transform_name(name)
        self.service.delete_blob(self.container, name)
        return name

    def exists(self, name):
        name = self._transform_name(name)
        return self.service.blob_exists(self.container, name)

    def listdir(self, path = None):
        path = self._transform_name(path)
        blobs = self.service.list_blobs(self.container, prefix = path)
        paths = [os.path.split(blob.name) for blob in blobs]
        dirs = [path[0] for path in paths]
        files = [path[1] for path in paths]
        return (dirs, files)

    def size(self, name):
        name = self._transform_name(name)
        blob = self.service.get_blob(self.container, name, with_content=False)
        return blob.content_length() if blob != None else 0

    def url(self, name):
        name = self._transform_name(name)
        return self.service.get_blob_url(self.container, name)


