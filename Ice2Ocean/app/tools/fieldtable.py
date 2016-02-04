'''
The field table manages the valid parameter list, as well as blob metadata.
Note that this interacts with the BlobCache to invalidate stale data.

-Nels
'''

class FieldManager:

    def __init__(self, table_service, table):
        self.table_service = table_service
        self.table = table

    def getInfo(self, param):
        '''
        Return all known information about the supplied parameter as a dictionary.
        '''
        result = self.table_service.query_entities(self.table, "PartitionKey eq '{0}'".format(param))
        return result[0].__dict__

    def getAll(self):
        '''
        Return all known information about *every* parameter.
        '''
        result = self.table_service.query_entities(self.table)
        return [r.__dict__ for r in result]
        
