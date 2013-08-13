import json
import os
from random import random
from tempfile import TemporaryFile
from unittest import TestCase
from requests import HTTPError
from azurepython3.blobservice import BlobService


class TestBlobService(TestCase):

    # expecting a JSON file with credentials ("account_name" and "account_key") in test directory
    CREDENTIALS_PATH =  os.path.dirname(os.path.abspath(__file__)) + '/azurecredentials.json'

    CONTAINER_PREFIX = 'azurepython3-test'

    def setUp(self):
        # find azure credentials for testing. expects them in cwd
        if not os.path.exists(self.CREDENTIALS_PATH):
            raise Exception('Azure Credentials file at "%s" does not exist' % os.path.abspath(self.CREDENTIALS_PATH))

        # read json formatted credentials ("account_name" and "account_key")
        with open(self.CREDENTIALS_PATH, "r") as file:
            self.credentials = json.load(file)

        # create the blob service
        self.service = BlobService(self.credentials['account_name'], self.credentials['account_key'])

        # generate names for the test containers
        self.container_names = ["%s-%d" % (self.CONTAINER_PREFIX, i) for i in range(5)]

    def create_container(self, name):
        # create a test container
        try:
            self.service.create_container(name)
        except HTTPError as e:
            if e.response.status_code != 409:
                raise e

    def tearDown(self):
        # delete the test containers
        for name in self.container_names:
            self.service.delete_container(name)

    def list_containers(self):
        containers = self.service.list_containers()
        for name in self.container_names:
            self.assertIn(name, [x.name for x in containers])

    def test_create_and_list_containers(self):
        for name in self.container_names:
            self.assertTrue(self.service.create_container(name, 'container'))

        self.list_containers()

    def test_create_blob(self):
        container = '%s-test1' % self.CONTAINER_PREFIX

        try:
            self.assertTrue(self.service.create_container(container, 'container'))
        except HTTPError as e:
            # there will be a HTTP 409 error if the container already exists
            if e.response.status_code != 409:
                self.fail("Failed to create test container")

        # attempt to upload the file
        data = bytearray(b'test byte string 11.5.2.7.3.14.59.2013.08.12')
        self.assertTrue(self.service.create_blob(container, 'somefile.ext', data))

        # delete the container
        self.service.delete_container(container)

    def test_delete_blob(self):
        container = '%s-test2' % self.CONTAINER_PREFIX

        # create a test container
        self.create_container(container)

        # create a file
        self.service.create_blob(container, 'file-to-delete.ext', bytearray(b'THIS FILE SHOULD BE DELETED'))

        # delete the file
        self.assertTrue(self.service.delete_blob(container, 'file-to-delete.ext'))

        # delete the container again
        self.service.delete_container(container)

    def test_list_blobs(self):
        container = '%s-test3' % self.CONTAINER_PREFIX
        self.create_container(container)

        self.service.create_blob(container, 'folder1/file1.ext', bytearray(b'THIS FILE SHOULD BE LISTED'))
        self.service.create_blob(container, 'folder1/file2.ext', bytearray(b'THIS FILE SHOULD BE LISTED'))
        self.service.create_blob(container, 'folder2/file3.ext', bytearray(b'THIS FILE SHOULD BE LISTED'))
        self.service.create_blob(container, 'file4.ext', bytearray(b'THIS FILE SHOULD BE LISTED'))

        blobs1 = self.service.list_blobs(container)
        self.assertSetEqual({'folder1/file1.ext', 'folder1/file2.ext', 'folder2/file3.ext', 'file4.ext'},
                             set([blob.name for blob in blobs1]))

        blobs2 = self.service.list_blobs(container, prefix = 'folder1')
        self.assertSetEqual({'folder1/file1.ext', 'folder1/file2.ext'}, set([blob.name for blob in blobs2]))

        blobs3 = self.service.list_blobs(container, prefix = 'folder2')
        self.assertSetEqual({'folder2/file3.ext'}, set([blob.name for blob in blobs3]))

        self.service.delete_container(container)