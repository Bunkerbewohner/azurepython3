azure-python3
=============

**azurepython3** is a Python 3.3 compatible library for Windows Azure. While in the beginning I had a general purpose Azure library in mind I eventually only implemented the parts that I needed so far, namely BlobStorage related functionalities. The library includes a fully functional custom storage for Django 1.6+.

The project is hosted on GitHub: https://github.com/Bunkerbewohner/azurepython3
It can also be found on PyPI: https://pypi.python.org/pypi/azurepython3

The development status of this package is "alpha". While it works and I'm successfully using the AzureStorage for my Django project, there are probably still bugs around and scenarios that I hadn't tested. So any help in that regard is welcome, if you are trying to use Azure in your Python 3 project and want to use this library.

Installation and Usage
----------------------

You can download the package from GitHub or install it from PyPI using **easy_install** or **pip**, e.g. ```pip install azurepython3```.

The important classes of this package are **azurepython3.blobservice.BlobService**, which offers essential functions for Windows Azure blob storage, and **azurepython3.djangostorage.AzureStorage**, which implements a custom Django storage based on Azure's blob storage.

Examples
--------

Here are a couple of examples of how to use this library.

 * Using Blob Services 	
 	* [Get BlobService](#get-blobservice)
 		* [Enable CORS](#enable-cors)
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
 * [Migrate from Django's FileSystemStorage to AzureStorage](#migrate-from-djangos-filesystemstorage-to-azurestorage)

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

### Enable Cors

If you want to use the files on your BlobStorage with Cross-Origin Resource Sharing (CORS), you can enable it using the BlobService instance:

```python
svc = BlobService.discover()
svc.enable_cors('http://mydomain.com')
```

Check the docstring for more advanced options such as specifying multiple domains, allowed HTTP methods and a maximum age for preflight answers. If you use AzureStorage, you can access the BlobService instance through its "service" property:

```python
storage = AzureStorage()
storage.service.enable_cors('http://mydjangowebsite.com')
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

If previously you have been using the default FileSystemStorage, you can use the ```azuremigrate``` command to migrate all your files into the cloud storage, as described in the next example.

### Migrate from Django's FileSystemStorage to AzureStorage

The default storage used by Django is FileSystemStorage which stores all user uploads in the user defined ```MEDIA_ROOT``` directory. Add azurepython3 to ```INSTALLED_APPS``` to gain access to the ```azuremigrate``` command, which will automatically upload all those files to the AZURE_DEFAULT_CONTAINER. This is not required for using the AzureStorage itself, it merely provides the admin command. 

```python
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    #...

    # include azurepython3 app to get "azuremigrate" command
    'azurepython3'
)
```

Once the app is available execute the command to upload the media files:

```python
python manage.py azuremigrate
Starting migration from "<project_dir>/media" to Cloud Storage container "$root"

folder1/image1.jpg...ok
folder1/image2.jpg...ok
...
migration complete
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
