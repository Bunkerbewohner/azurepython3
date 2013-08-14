azure-python3
=============

**azurepython3** is a Python 3.3 compatible library for Windows Azure. This package is still in an early development phase. Right now only the essential functions of the Azure REST API are implemented, so that it can be used as a custom Django Storage provider.

The project is hosted on GitHub: https://github.com/Bunkerbewohner/azurepython3
It can also be found on PyPI: https://pypi.python.org/pypi/azurepython3

The development status of this package is "alpha". While it works and I'm successfully using the AzureStorage for my Django project, there are probably still bugs around and scenarios that I hadn't tested. So any help in that regard is welcome, if you are trying to use Azure in your Python 3 project and want to use this library.

Installation and Usage
----------------------

You can download the package from GitHub or soon will be able to install it from PyPI using **easy_install** or **pip**, e.g. ```pip install azurepython3```. Currently I'm still figuring out how this whole PyPI thing works, and my ```setup.py upload``` is not working yet.

The important classes of this package are **azurepython3.blobservice.BlobService**, which offers essential functions for Windows Azure blob storage, and **azurepython3.djangostorage.AzureStorage**, which implements a custom Django storage based on Azure's blob storage.

Examples
--------

Here are a couple of examples of how to use this library.

 * Using Blob Services 	
 	* [Get BlobService](#get-blobservice)
 	* Containers
 		* [Create Container](#create-container)
 		* [List Containers](#list-containers)
 		* [Delete Container](#delete-container)
	* Blobs
 		* [Create Blob](#create-blob)
 		* [List Blobs](#list-blobs)
 		* [Get Blob](#get-blob)
 		* [Delete Blob](#delete-blob)
 * [Using AzureStorage in Django](#using-azurestorage-in-django)

### Get BlobService

The interface to all Blob storage related functions is the class BlobService. It requires the Windows Azure account name and an access key to work. These credentials can be passed directly as parameters. Additionally the helper method BlobService.from_config can read the values from a JSON file that contains an object with the properties "account_name" and "account_key".

```python
from azurepython3.blobservice import BlobService

# create from JSON config, containing "account_name" and "account_key"
svc = BlobService.from_config("credentials.json")

# or specifiy account credentials explicitly
svc = BlobService("myaccountname", "myaccountkey")

# or attempt to discover an "azurecredentials.json" file in the local filetree
svc = BlobService.discover()
```

### Create Container

This example shows how to create containers with different public access rights, determined by the second parameter of ```BlobService.create_container(name, access)```. The following values are possible:

* ```None``` - the container will be private
* ```'container'``` - container: Specifies full public read access for container and blob data. Clients can enumerate blobs within the container via anonymous request, but cannot enumerate containers within the storage account. 
* ```'blob'``` - Specifies public read access for blobs. Blob data within this container can be read via anonymous request, but container data is not available. Clients cannot enumerate blobs within the container via anonymous request.

```python
from azurepython3.blobservice import BlobService
svc = BlobService("myaccountname", "myaccountkey")

svc.create_container("new-private-container", access = None)
svc.create_container("new-public-container", access = "container")
svc.create_container("new-protected-container", access = "blob")
```

**Remarks:** The method will return True if the container was successfully created. Errors will cause appropriate exceptions. Specifically, if the container already exists an HTTPError with the status code 409 (Conflict) will be raised.

### List Containers

This example shows how to list containers of an account. The method ```BlobService.list_containers()``` will return a list of ```Container``` instances, consisting of name, url, properties and metadata.

```python
from azurepython3.blobservice import BlobService
svc = BlobService.from_config("azurecredentials.json")
containers = svc.list_containers()

for c in containers:
	print("%s (%s)" % (c.name, c.url))
	print(c.properties)
```

### Delete a Container

```python
from azurepython.blobservice import BlobService
svc = BlobService.discover()

if svc.delete_container('containername'):
	print("Container was deleted")
```

### Create Blob

The following code example uses the BlobService to upload a file to an existing container. The content is expected to be an iterable of bytes, such as a bytearray. Optionally the content encoding can be passed an argument. If not provided none will be specified.

```python
from azurepython3.blobservice import BlobService
svc = BlobService("myaccountname", "myaccountkey")

with open("path/to/somefile.ext") as file:
	svc.create_blob('containername', 'blobname', file.read())

```		

### List Blobs

To list blobs in a container use the method ```BlobService.list_blobs(container, prefix=None)```. You can use ```prefix``` to filter blobs whose names start with that prefix. The blobs returned only contain properties and metadata, not the contents. Contents can be downloaded separately either by using ```BlobService.get_blob(container,name,with_content=True)``` or calling ```Blob.download_bytes()``` on the Blob instance.

```python3
from azurepython3.blobservice import BlobService
svc = BlobService.discover()

blobs = svc.list_blobs('container-name', prefix = None)
for b in blob:
	print("%s (%s)" % (b.name, b.url))
	print(b.properties)
```

### Get Blob

Single blobs can be fetched with or without their contents.

```python
from azurepython3.blobservice import BlobService
svc = BlobService.discover()

# Get blob properties, metadata and content in one request
blob = svc.get_blob('container-name', 'file.ext', with_content = True)
print(blob.content)

# Or fetch only the properties and metadata, then the content optionally in a second request
blob = svc.get_blob('container-name', 'file.ext', with_content = False)
if print_content:
	print(blob.download_bytes())
```
 

### Delete Blob

```python
from azurepython.blobservice import BlobService
svc = BlobService.discover()

if svc.delete_blob('containername', 'blobname'):
	print("Blob was deleted")
```

### Using AzureStorage in Django

To use Windows Azure Blob Storage as a custom storage provider in Django you can simply use the **AzureStorage** class, as in the following example.

```python 
from django.db import models
from azurepython3.djangostorage import AzureStorage

class Posting(models.Model):
	title = models.CharField()
	image = models.ImageField(max_length=255, storage=AzureStorage(),
							  upload_to="images/postings")
```

This will store images as Blobs in the configurated container, whereas ```upload_to``` will be used as a prefix for the blob names, and therefore serve as a pseudo-directory. 

For the AzureStorage to work you have to configure the Azure credentials in your ```settings.py``` as follows, using your actual credentials (account name and access key) and the name of an existing container in your storage:

```python
# put this into your settings.py
AZURE_ACCOUNT_NAME = "myaccountname"
AZURE_ACCOUNT_KEY = "myaccountkey"
AZURE_DEFAULT_CONTAINER = "containername"
```

Alternatively these properties can be passed to the AzureStorage instance explicitly:

```python
storage=AzureStorage(account_name='myaccountname',
					 account_key='myaccountkey',
					 container='containername'))
```

UnitTests
---------

The package contains unittests. Since no storage emulation has been implemented yet, an actual Windows Azure storage account is required to test the functionality. They must be provided by creating a file "azurecredentials.json" in the ```azurepython3/tests``` directory, looking like the following example:

```json
{
	"account_name": "myaccountname",
	"account_key": "myaccountkey"
}
```