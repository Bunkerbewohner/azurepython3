import os
import traceback
from django.core.management.base import BaseCommand, CommandError, NoArgsCommand
from django.conf import settings
from azurepython3.blobservice import BlobService


class Command(NoArgsCommand):
    help = """Migrate from an existing FileSystemStorage to AzureStorage.
When executing the command "azuremigrate" it will scan for media files in MEDIA_ROOT
and upload all the files to the configured default container."""

    def handle_noargs(self, **options):
        # ensure that project has required configuration
        if not os.path.exists(settings.MEDIA_ROOT):
            raise CommandError('Cannot migrate files from non existing MEDIA_ROOT (%s)' % settings.MEDIA_ROOT)
        if not hasattr(settings, 'AZURE_ACCOUNT_NAME'):
            raise CommandError('AZURE_ACCOUNT_NAME setting missing')
        if not hasattr(settings, 'AZURE_ACCOUNT_KEY'):
            raise CommandError('AZURE_ACCOUNT_KEY setting missing')
        if not hasattr(settings, 'AZURE_DEFAULT_CONTAINER'):
            raise CommandError('AZURE_DEFAULT_CONTAINER settings missing')

        # get service interface
        service = BlobService(settings.AZURE_ACCOUNT_NAME, settings.AZURE_ACCOUNT_KEY)

        self.stdout.write('Starting migration from "%s" to '
                          'Cloud Storage container "%s"' % (settings.MEDIA_ROOT, settings.AZURE_DEFAULT_CONTAINER))

        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            for file in files:
                path = os.path.join(root, file)
                blobname = os.path.relpath(path, settings.MEDIA_ROOT).replace('\\', '/')
                self.stdout.write(blobname + "...", ending='')
                try:
                    with open(path, 'rb') as f:
                        if service.create_blob(settings.AZURE_DEFAULT_CONTAINER, blobname, bytearray(f.read())):
                            self.stdout.write('ok')
                        else:
                            self.stdout.write('fail')
                except Exception as e:
                    self.stdout.write('fail')
                    traceback.print_exc()
                    self.stdout.write('aborted migration.')
                    return

        self.stdout.write('migration complete')

