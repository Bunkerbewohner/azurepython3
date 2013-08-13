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
            self.container = settings.AZURE_DEFAULT_CONTAINER
        else:
            self.container = container

        if account_name and account_key:
            self.service = BlobService(account_name, account_key)
        else:
            self.service = BlobService(settings.AZURE_ACCOUNT_NAME, settings.AZURE_ACCOUNT_KEY)

    def _open(self, name, mode = 'rb'):
        content = self.service.get_blob_content(self.container, name)
        file = SpooledTemporaryFile()
        file.write(content)
        return file

    def _save(self, name, content):
        content.open(mode='rb')
        data = content.read()
        self.service.create_blob(self.container, name, data)
        return name

    def delete(self, name):
        self.service.delete_blob(self.container, name)
        return name

    def exists(self, name):
        try:
            blob = self.service.get_blob(self.container, name, with_content=False)
            return blob != None
        except HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                raise e

    def listdir(self, path = None):
        blobs = self.service.list_blobs(self.container, prefix = path)
        paths = [os.path.split(blob.name) for blob in blobs]
        dirs = [path[0] for path in paths]
        files = [path[1] for path in paths]
        return (dirs, files)

    def size(self, name):
        blob = self.service.get_blob(self.container, name, with_content=False)
        return blob.content_length()

    def url(self, name):
        blob = self.service.get_blob(self.container, name, with_content=False)
        return blob.url

        


