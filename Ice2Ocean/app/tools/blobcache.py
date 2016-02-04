'''
Utility functions for caching request responses to an Azure blob store.
'''
import string
from azure.storage import BlobService

def str2blobname(str):
    '''
    Convert a string into a valid blob name consisting of letters, numbers, 
    and dashes.
    
    Note that blob names _are_ case sensitive.

    This could be replaced by any decent hashing strategy; here it is used to
    ease debugging. The resulting blob names are human (roughly, and for some 
    definition of human) readable.
    '''
    whitelist = string.letters + string.digits + '-'
    s = str.replace('.','-')
    return ''.join(c for c in s if c in whitelist)


class BlobCache:
    '''
    Simplistic cache toolkit targetting an Azure Blob Service.

    name:      the name of a storage account.
    key:       the access key for the storage account.
    container: the name of the container to use.
    '''

    def __init__(self, name, key, container):
        self.container = container
        self.blobstore = BlobService(name, key)
        self.blobstore.create_container(self.container)

    def getresponse(self, cachekey):
        '''
        Get a value from the cache.

        cachekey: The key.

        Kilroy notes that this throws an exception rather than returning a 
        value on failure.
        '''
        return self.blobstore.get_blob_to_text(self.container,str2blobname(cachekey))

    def putresponse(self, cachekey, value):
        '''
        Put a value in the cache with the given key.

        cachekey: The key.

        value: The value to associate with the key.
        '''
        return self.blobstore.put_block_blob_from_text(self.container, str2blobname(cachekey), value)

    def invalidate(self, cachekey):
        '''
        Invalidate a value in the cache. Immediate. Permanent.

        cachekey: The key.
        '''
        self.blobstore.delete_blob(self.container, str2blobname(cachekey))