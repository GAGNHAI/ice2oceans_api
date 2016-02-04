'''
Data Postprocessing Library

Functions for 
* interacting with blob storage, 
* constructing plots from netCDF files
* Working with azure tables

Nels Oscar
'''

import socket
# Set a long timeout (to handle slow blob transfers).
timeout = 1000
socket.setdefaulttimeout(timeout)

# Bring in important information
from azure.storage import *
from app.settings import * #  The connection settings.
import sys,re, string, json, os, subprocess, tempfile

# Note this import ordering is significant.
import matplotlib
matplotlib.use('Agg')
# The matplotlib backend must be changed before importing pyplot.
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
from drawing import *
import psycopg2 as DBase # PostgreSQL Connection
from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
import pandas as pd

# database connection string
host = connection_properties["DATABASE_HOST"]
base = connection_properties["DATABASE_NAME"]
user = connection_properties["DATABASE_USER"]
word = connection_properties["DATABASE_PASSWORD"]

# Model Output Storage Information
p_blob_store     = connection_properties["MODEL_OUTPUT_STORAGE_ACCOUNT_NAME"]
p_blob_key       = connection_properties["MODEL_OUTPUT_STORAGE_ACCOUNT_KEY"]
p_blob_container = connection_properties["MODEL_OUTPUT_STORAGE_CONTAINER"]
p_naming_format  = connection_properties["NAME_FORMAT"]

p_blob_service   = BlobService(p_blob_store, p_blob_key)

# Metadata Storage Information 
#metadata_blob_store = connection_properties["METADATA_STORAGE_ACCOUNT_NAME"]
#metadata_blob_key = connection_properties["METADATA_STORAGE_ACCOUNT_KEY"]
#metadata_blob_service = BlobService(metadata_blob_store, metadata_blob_key)
#metadata_blob_container = connection_properties["METADATA_STORAGE_CONTAINER"]
#table_service = TableService(account_name=metadata_blob_store, account_key=metadata_blob_key)

def fetch_to_process():
    '''
    Get the unprocessed datasets from the observed datastore.
    '''
    bs = p_blob_service.list_blobs(p_blob_container, include='metadata')
    res = []
    for b in bs.blobs:
        if b.metadata.has_key('ProcessingStage') and b.metadata['ProcessingStage'] == 'Started':
            res.append(b)
    return res

def _label(name, state, msg=None):
    '''
    Apply the given state label and optional message to the blob in 
    the observed datastore. 

    name: Name of the blob to fetch.

    state: The label to apply (Not strictly human readable)

    msg: An optional message. Intended to be human readable.
    '''
    m = {'ProcessingStage': state, 'Message': '{0}'.format(msg)}
    p_blob_service.set_blob_metadata(p_blob_container,name,m)

def label_in_process(name):
    '''
    Label the blob as being processed by a worker.

    name: Name of the blob to fetch.
    '''
    _label(name, 'Processing')

def label_processed(name):
    '''
    Label the blob completed. No further processing required.

    name: Name of the blob to fetch.
    '''
    _label(name, 'Completed')

def label_error(name):
    '''
    Label the blob as failed to process.

    name: Name of the blob to fetch.
    '''
    _label(name, 'Error')

def naming(year, month, day):
    return p_naming_format.format(year, month, day)

def fetch_query(query):
    '''
    Returns a query result from the relational database

    query: SQL query formatted for PostgreSQL

    '''
    print('in fetchquery')
    # Create database connection
    try:
        engine = create_engine('postgresql://arendta:glA$iEr1@ice2o.csya4zsfb6y4.us-east-1.rds.amazonaws.com:5432/spatial_database')
        #with SSHTunnelForwarder(("pscuw.cloudapp.net",22),
        #ssh_username = "arendta",
        #ssh_password = "Sa$2rUg^",
        #remote_bind_address=("localhost",5432)) as server:
        #   print server.local_bind_port
        #   engine = create_engine('postgresql://arendta:glA$iEr1@localhost:'+ str(server.local_bind_port) + '/spatial_database')
        result =  pd.read_sql(query,engine)
        #result = [data[i] for i in range(len(data))]
        return result
     
        #connection  = DBase.connect(" host='%s' dbname='%s' user='%s' password='%s'" %(host, base, user, word))
        #cursor = connection.cursor() # Cursor object
    except:
        print 'connection error'

    #try: 
        #cursor.execute(query)
        #data = cursor.fetchall()
        #result = [data[i] for i in range(len(data))]
        #return result
        #cursor.close()
        #connection.close()
    #except:
    #    return None
    #    cursor.close()
    #    connection.close()

def fetch_ds2(param, callback=None):
    name = param + '.dat'
    # The local path to the file (may not exist), based on the system temp directory
    fpath = '{0}\{1}'.format(tempfile.gettempdir(),name)
    fexists = os.path.exists(fpath)
    if fexists:
        # Try to open the file
        return np.fromfile(fpath,dtype=np.float32)
    else:
        # Failing that we should fetch it from blob storage. 
        
        # First get the blob properties.
        props = p_blob_service.get_blob_properties(p_blob_container, name)
        
        # Then attempt to fetch the blob, attempt no more than 4 times.
        p_blob_service.get_blob_to_path(p_blob_container, name, fpath, progress_callback=callback)
        # Keep track of how many times we've tried. 
        attempt = 0
        # Keep up with the int-ized version of the correct file size.
        size = int(props['content-length'])
        
        # Try to download the blob repeatedly, checking each time that the 
        # transfer hasn't finished or run out of attempts.
        #
        #   Kilroy notes that this test is problematic
        #    A blob will pass this test if the downloaded size 
        #                           and the reported blob size 
        #                                            are equal.
        #    
        #    This does not correctly identify blobs that have 
        #                             been partially uploaded.
        while not (size == os.path.getsize(fpath)) and attempt < 3 :
            p_blob_service.get_blob_to_path(p_blob_container, name, fpath, progress_callback=callback)
            attempt = attempt + 1

        # Now try to open the ds as it has ostensibly been downloaded.
        try:
            return np.fromfile(fpath,dtype=np.float32)
        except:
            # This could do something more intelligent, like raise an 
            #  appropriate exception.
            return None

def fetch_ds(param, time, callback=None):
    '''
    Returns a readonly netCDF dataset from the specified name if it exists in the blobstore.

    name: Name of the blob to fetch.
    '''
    # construct the blob name from the year, month and day.
    year, month, day = time
    name = p_naming_format.format(param,year,month,day)
    
    # The local path to the file (may not exist), based on the system temp directory
    fpath = '{0}\{1}'.format(tempfile.gettempdir(),name)
    fexists = os.path.exists(fpath)

    if fexists:
        # Try to open the file
        return nc.Dataset(fpath, 'r')
    else:
        # Failing that we should fetch it from blob storage. 
        
        # First get the blob properties.
        props = p_blob_service.get_blob_properties(p_blob_container, name)
        
        # Then attempt to fetch the blob, attempt no more than 4 times.
        p_blob_service.get_blob_to_path(p_blob_container, name, fpath, progress_callback=callback)
        # Keep track of how many times we've tried. 
        attempt = 0
        # Keep up with the int-ized version of the correct file size.
        size = int(props['content-length'])
        
        # Try to download the blob repeatedly, checking each time that the 
        # transfer hasn't finished or run out of attempts.
        #
        #   Kilroy notes that this test is problematic
        #    A blob will pass this test if the downloaded size 
        #                           and the reported blob size 
        #                                            are equal.
        #    
        #    This does not correctly identify blobs that have 
        #                             been partially uploaded.
        while not (size == os.path.getsize(fpath)) and attempt < 3 :
            p_blob_service.get_blob_to_path(p_blob_container, name, fpath, progress_callback=callback)
            attempt = attempt + 1

        # Now try to open the ds as it has ostensibly been downloaded.
        try:
            return nc.Dataset(fpath, 'r')
        except:
            # This could do something more intelligent, like raise an 
            #  appropriate exception.
            return None

def retrieveRow(PartitionKey,RowKey):
    ''' 
    returns a row from table storage
    '''
    try:
        row = table_service.get_entity(metadata_blob_container,PartitionKey,RowKey)
        return json.dump(row.Conditions,row.Instruments,row.Investigators,row.Notes)
    except:
        return None

def list_local_cache():
    td = tempfile.gettempdir()
    return [ {"file": f, "size": os.path.getsize("{0}\\{1}".format(td,f))} 
                for f in os.listdir(td) 
                    if f.endswith(".nc") ];

def list_blob_cache():
    return p_blob_service.list_blobs(p_blob_container, include='metadata')

def list_by_status(status):
    '''
    List blobs with the supplied status in the observed container.
    '''
    blobs = p_blob_service.list_blobs(p_blob_container, include='metadata')
    ps = []
    for blob in blobs:
        if status is None or blob.metadata['ProcessingStage'] == status:
            ps.append(blob)
    return ps

def label_by_status(oldlabel, newlabel):
    items = list_by_status(oldlabel);
    for i in items:
        _label(i.name,newlabel)

def list_p():
    containers = p_blob_service.list_containers()
    for c in containers:
        print '{0}'.format(c.name)
        blobs = p_blob_service.list_blobs(c.name, include='metadata')
        for b in blobs:
            print '|--> {0}: {1}'.format(b.name, b.metadata)
        print ""

def newRow(table_service, table_name, name, fromparam, lname, units, cmap, color_min, color_max):
    properties = {\
        'PartitionKey':name,\
        'RowKey': fromparam,\
        'long_name': lname,\
        'units': units,\
        'cmap': cmap,\
        'color_max': color_min,\
        'color_min': color_max,\
        }
    print properties
    table_service.insert_entity(table_name, properties)

def table_exists(tableName):
    if tableName in map((lambda x: x.name), table_service.query_tables()):
        return True
    else:
        return False

def table_builder(t):
    '''
    Several thoughts on how to make this go.
    The key idea is that we have points,
    parameters, and derived values. All of
    these bits need to be available in the 
    azure table. (Note that the azure table 
    is one of several ways of implementing 
    this; it has been chosen because the dev
    time is short) 
    
    In order to make that happen the table 
    schema needs to be organized around the 
    spatial temporal attributes.

    Question: Table name level metaprogramming?
    Answer: Maybe
    
    Need to get the locations and parameters 
    and derived parameters into a table.

    Then we can worry about fast.


    Two keys. PartitionKey -- Time (hour)
              RowKey       -- Location (lon,lat)
    '''
    ds = fetch_ds(t)
    xs = ds.variables['lon_rho'][0, :]
    ys = ds.variables['lat_rho'][:, 0]

    cx = len(xs)
    cy = len(ys)

    print 'x: {0} entries\ny: {1} entries'.format(cx, cy)

    # Surface only
    vals = geo_vars(ds)
    tname = 'lo{0}'.format(t.split('.')[0].split('_')[2])
    print tname
    table_service.create_table(tname,False)

    table_service.begin_batch()

    i = 0
    for x in range(0, cx):
        print x
        for y in range(0, cy):
            d = {}
            d["PartitionKey"] = '{0}'.format(x)
            d["RowKey"] = '{0}'.format(y)
            d["Longitude"] = '{0}'.format(xs[x])
            d["Latitude"] = '{0}'.format(ys[y])
            for val in vals:
                v = ds.variables[val][0, 39, y, x]
                d[val] = '{0}'.format(v)
            table_service.insert_entity(tname, d)
            if i % 100 is 0:
                table_service.commit_batch()
                table_service.begin_batch()
    table_service.commit_batch()
    