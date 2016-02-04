'''
Azure Storage
Connections, communication, and related details.
'''

connection_properties = {
    ##########################################################################
    # The storage account to be used for storing ice2ocean views, responses, 
    # and configuration

    'STORAGE_ACCOUNT_NAME': 'ice2oceans',
    'STORAGE_ACCOUNT_KEY': 'Hj2jbmS4eR1EYCfGO5d7EgEDdAbxfFIiYKk7DlG7nn5L0dmcIBlsL8bWYnVcXuFax03wjj9BBr7IxagBS14K8g==',
    
    # The container prefix. Containers will be created if they do not 
    # currently exist (Kilroy)
    'STORAGE_CONTAINER': 'ice2oceans',
    
    # The name of the azure table for view configurations. The table will be 
    # created (but not populated) if it doesn't exist. See the admin interface
    # http://{your host name}/admin/settings/   (Kilroy; that is a stub)
    # to populate this table on a first run                       
    'FIELD_TABLE': 'ice2oceanfields',                        

    ##########################################################################
         
    # The blob storage with the netcdf snowmodel output
    
    'MODEL_OUTPUT_STORAGE_ACCOUNT_NAME': 'snowmodel',
    'MODEL_OUTPUT_STORAGE_ACCOUNT_KEY': 'lgu1UL16tCeclZUj2AH1MaI67nmD/HPZfNSa86hXFvnLU+nrAh2/9YOi5IyVO93qJgy1CIJndeEEdIFNfxsdAA==',

    # The name of the container where the netcdf files live.

    'MODEL_OUTPUT_STORAGE_CONTAINER': 'snowmodel',
    
    # {0} is the parameter name
    # {1} is year
    # {2} is month
    # {3} is day

    'NAME_FORMAT': '{0}_{1}_{2}_{3}.nc',

    # A note on model runs; they should be stored as snapshots of the same 
    #  blob. This simplifies most data access, and reduces the number of 
    #  storage api calls required to serve a request in the worst case.
    
   
    ##########################################################################

    # The blob storage with metadata for postgreSQL tables

    #'METADATA_STORAGE_ACCOUNT_NAME' : 'i2ometadata',
    #'METADATA_STORAGE_ACCOUNT_KEY' : 'UwBaaBMPGowCCbv0ajHps8wHYrgqSCvvzSposvCD9uInAFrxG5+9tvy4yavnUD6J8Pq0yHS4m5zxtHYnYiiG5Q==',
    #'METADATA_STORAGE_CONTAINER' : 'i2ometadata',

    
    # Database Connection String
    'DATABASE_HOST' : 'pscuw.cloudapp.net',
    'DATABASE_NAME' : 'spatial_database',
    'DATABASE_USER' : 'arendta',
    'DATABASE_PASSWORD' : 'glA$iEr1',

}