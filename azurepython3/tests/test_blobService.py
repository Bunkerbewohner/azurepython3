import json
import os
from random import random
from unittest import TestCase
from azurepython3.blobservice import BlobService


class TestBlobService(TestCase):

    # expecting a JSON file with credentials ("account_name" and "account_key") in test directory
    CREDENTIALS_PATH =  os.path.dirname(os.path.abspath(__file__)) + '/azurecredentials.json'

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
        self.container_names = ["azurepython3-test-%d" % i for i in range(5)]

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