'''
The Ice2Ocean service api.

Built from LiveOcean API designed by Nels Oscar 

modified for Gulf of Alaska runoff applications by Anthony Arendt  

copyright 20141007 Microsoft Research

'''

#### Django modules
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, Http404, HttpResponseServerError, HttpResponseNotFound
from django.template import RequestContext
from django.views.decorators.cache import cache_control
from django.conf import settings

#### External modules
from io import BytesIO
import datetime
import json
import numpy as np
import numpy.ma as ma
from scipy.interpolate import interp1d
from matplotlib import mlab
from azure.storage import BlobService, TableService
import pyproj
# from pygeoif import geometry # for WKT to lat/lon connversions
import csv 
import matplotlib.pyplot as plt

#### Internal modules
import tools.builder as b
from settings import *
import cannedresponses as cr
from tools.drawing import *
from tools.blobcache import BlobCache
from tools.fieldtable import FieldManager
from app.settings import *

# Storage for computed results
# Each time consuming computation stores its results here, 
#  -- keyed by the request that generated the result.

# AAA changed to ice2ocean blob storage:
cache = BlobCache(connection_properties["STORAGE_ACCOUNT_NAME"], 
                  connection_properties["STORAGE_ACCOUNT_KEY"], 
                  connection_properties["STORAGE_CONTAINER"])

# Data Parameters (if we want to get at them directly)
table_service = TableService(connection_properties["STORAGE_ACCOUNT_NAME"], 
                             connection_properties["STORAGE_ACCOUNT_KEY"])

# Data parameters wrapped in a more specific (and prefered) interface
fieldManager = FieldManager(table_service,connection_properties["FIELD_TABLE"])

# Projection for bing maps
bingProjection = pyproj.Proj("+init=EPSG:3857")

# time details...

# AAA: modified to handle month/day data

def extract_time(request, default_value=None):
    '''
    How to ask for a time?
    Direct: give me julian hour h from year y
    
    ### AAA 
    OR
    Direct: give me day d, month m and year y 
    NOTE: day is day of the month, not Julian day
    ### AAA
    
    Relative: give me now +- h hours

    Returns None if there is no recognizable time spec.

    Returns (year, julian hours) otherwise. 

    May raise a TypeError if the hour or year values are non-integer.
    '''
    hour = request.GET.get('hour',default_value)
    
    year = request.GET.get('year',default_value)
    
    ### AAA
    month = request.GET.get('month',default_value)
    day = request.GET.get('day',default_value)

    if day and month and year:
        return (int(year),int(month),int(day))
    ### AAA

    elif hour and year:
        return (int(year), int(hour))
    elif hour:
        t0 = datetime.datetime.now()
        year = t.replace(month=1,day=1,hour=0,minute=0,second=0)
        dt = datetime.timedelta(seconds=hour*3600)
        tr = t0 + dt
        if not tr.year == year.year:
            return default_value
        return (year.year, int((tr - year).total_seconds() / 3600))
    else:
        return default_value

# Note the use of builder.fetch_ds(...) ( or b.fetch_ds(...) in this file)
#  as opposed to nc.Dataset(...) This is critical for use in azure -- 
#  local files are not persistent.
#
#  The blob store is great, but we must download the blobs to local files 
#  and open the datasets via file handle.
#  
#  builder.fetch_ds(...) handles the process of acquiring the netCDF files 
#  from blob storage, and attempts (Kilroy!!!) to do so intelligently.

# Caching results is always the same. Its written down here so steps don't 
# accidentally get skipped.
#   - serialize the key to json
#   - associate the key with the value in the blob cache.
# If someone were feeling ambitious: 
#    an azure blob storage cache driver for Django would be interesting.
def cacheResult(key, value):
    '''
    Wrapper to formalize caching steps (so 'I' don't forget to serialize)

    key: any json serializable object
    value: something for the blob store.
    '''
    reqstr = json.dumps(key)
    cache.putresponse(reqstr, value)

def music(request):
    '''
    Quote The Music Man

    Expects an integer argument to message, not less than 0 not more than TIAS
    '''
    assert isinstance(request, HttpRequest)
    try:
        index = int(request.GET.get("message"))
        Quotes=["Folks we have trouble right here in River City and that starts with T and that rhymes with P and that stands for POOL!!!!", "That's not right. That's not even wrong.", "It takes a while before you sound like yourself.", "That's Adler's problem."]
        return HttpResponse(Quotes[index])
    except:
        return HttpResponseNotFound(content="You must provide a valid argument (ex. message=1) in your query string. Either the index was out of range, wasn't an integer, or it was omitted entirely.")

@cache_control(must_revalidate=False, max_age=3600)
def getvector(request):
    assert isinstance(request, HttpRequest)
    json_request = json.dumps(request.GET)
    try:
        table = request.GET.get('table',None)
        glName = request.GET.get('name',None)
        glName += " Glacier"
        body = cache.blobstore.get_blob_to_bytes('ice2ocean',json_request)
        response = HttpResponse(body,'text/xml')
    except:
        try:
            if 'moderncenterlines' in table:
                query = """SELECT ST_AsText(ST_Transform(geom,4246)) FROM %s WHERE glimsid IN (SELECT glimsid FROM modern WHERE name = '%s')""" %(table, glName)
            else:
                query = """SELECT ST_AsText(ST_Transform(geom,4246)) FROM %s WHERE name = '%s'""" %(table, glName)
            ds = b.fetch_query(query)
            # Kilroy: switch to shapely
            # AAA: this is to accommodate 
 #           poly = geometry.from_wkt(ds[0][0])
 #           for p in poly.geoms:
 #               e = p.exterior
 #               for i in range(0,len(e.coords),20):
 #                   lat = e.coords[i][1]
 #                   lon = e.coords[i][0]
 #           response = HttpResponse(ds[0][0],content_type = "text/plain")
 #           print 'past response'
 #           return response
        except:
            print ""
            a.message
            return cr.invalid_parameter()

@cache_control(must_revalidate=False, max_age=3600)
def gettimeseries(request):
    assert isinstance(request, HttpRequest)
    json_request = json.dumps(request.GET)
    try:
        table = request.GET.get('table',None)
        mascon = request.GET.get('mascon',None)
        location = request.GET.get('location',None)
        version = request.GET.get('version',None) 
        region = request.GET.get('region',None)
        glacier = request.GET.get('glacier',None)
        body = cache.blobstore.get_blob_to_bytes('ice2ocean',json_request)
        response = HttpResponse(body,'text/xml')
    except:
        try:
            if 'GRACE' in table:
                if mascon <> None:
                    query = """SELECT main.date, SUM(main.values_filter1d * cf.correction) FROM
                        (SELECT mascon, (area_km2 / 1e5) AS correction FROM mascon_fit WHERE mascon=%s) as cf LEFT JOIN
                        (SELECT mascon, date, values_filter1d from mascon_solution where version = %s) as main
                        ON cf.mascon = main.mascon GROUP BY date ORDER BY date;""" %(mascon,version)
                else:
                    query = """SELECT main.date, SUM(main.values_filter1d * cf.correction) FROM
                        (SELECT mascon, (area_km2 / 1e5) AS correction FROM mascon_fit WHERE region=%s) as cf LEFT JOIN
                        (SELECT mascon, date, values_filter1d from mascon_solution where version = %s) as main
                        ON cf.mascon = main.mascon GROUP BY date ORDER BY date;""" %(region,version)
                ds = b.fetch_query(query)
                response = HttpResponse(mimetype = 'text/csv')
                writer = csv.writer(response)
                for (d, m) in ds:
                    writer.writerow([d.strftime("%m/%d/%Y"), m])
            elif 'streamgauges' in table:
                query = """SELECT date, gaugeid, discharge FROM streamgauge_data WHERE gaugeid IN (SELECT gaugeid from streamgauges where name ~ '%s') ORDER BY date""" %(location)
            elif 'pointbalances' in table:
                query = """SELECT start_date, end_date, stake, elevation, balance, ST_AsText(ST_Transform(geom,4246)) FROM point_balances WHERE name = %s ORDER BY start_date""" %(glacier)
                ds = b.fetch_query(query)
                response = HttpResponse(mimetype = 'text/csv')
                ds.to_csv(response)
            print 'past response'
            return response
        except:
            print ""
            a.message
            return cr.invalid_parameter()


@cache_control(must_revalidate=False, max_age=3600)
def gettimeseries_metadata(request):
    assert isinstance(request, HttpRequest)
    json_request = json.dumps(request.GET)
    try:
        table = request.GET.get('table',None)
        location = request.GET.get('location',None)
        body = cache.blobstore.get_blob_to_bytes('ice2ocean',json_request)
        response = HttpResponse(body,'text/xml')
    except:
        try:
            if 'streamgauges' in table:
                metatext = b.retrieveRow('snowradar','test')
            response = HttpResponse(metatext,content_type = "text/plain")
            print 'past response'
            return response
        except:
            print ""
            a.message
            return cr.invalid_parameter()

@cache_control(must_revalidate=False, max_age=3600)
def getraster(request):
    assert isinstance(request, HttpRequest)
    json_request = json.dumps(request.GET)
    try:
        rparm = request.GET.get('param', None)
        rtime = extract_time(request)
        cmap = request.GET.get('cmap','binary')
        body = cache.blobstore.get_blob_to_bytes('ice2ocean',json_request)
        response = HttpResponse(body,'image/png')
        return response
    except:
        try:
            ### AAA new method of extracting an image based on param 
            if rparm in ('roff','prec'):
                control = fieldManager.getInfo(rparm)
                # ds = b.fetch_ds(rparm,rtime) 
                ds = b.fetch_ds2(rparm)
                print ds
                #lats = ds.variables['latitude'][:]
                #lons = ds.variables['longitude'][:]
                #dataField = ds.variables[control["RowKey"]][:].reshape(len(lats),len(lons))
                #ds.close()
                
                # AAA leave out the reprojection for now
                #plons,plats = bingProjection(lons,lats)
                #plons = plons[0,:]
                #plats = plats[:,0]
                #print plons, plats
               # x = np.arange(xMin, xMin + cellSize * fh.nx, cellSize)
               # y = np.arange(yMin, yMin + cellSize * fh.ny, cellSize)

                #for aRow in parfile:
                #    if (aRow[0] != '!'):
                #        t = aRow.split('=')[0].strip()
                #    try:
                #        exec(t + " = " + aRow.split('=')[1].strip())
                #    except:
                #        a = 1

                nx = 1810
                ny = 900
                d = ds.reshape(-1,ny,nx)
                subset = d[0,:,:]
                img = subset*(subset > 0)
                y, x = np.mgrid[0:ny,0:nx]
                buf = BytesIO()
                plt.imshow(img)
                #plot_to_bytes(lons,lats,dataField,buf,float(control["color_min"]), float(control["color_max"]), cmap_name=cmap)
                plot_to_bytes(x,y,img,buf,float(control["color_min"]), float(control["color_max"]), cmap_name=cmap)
                buf.seek(0)
                data = buf.read()
                buf.close()

                cache.blobstore.put_block_blob_from_bytes('ice2ocean',json_request,data)
        
                response = HttpResponse(data,'image/png')

            else:
                control = fieldManager.getInfo(rparm)

                ds = b.fetch_ds(rtime)
                if not ds:
                    oops = HttpResponseServerError()
                    oops.content = "Unable to retrieve data for request {0}".format(json_request)
                    return oops
                lats = ds.variables['lat_psi'][:]
                lons = ds.variables['lon_psi'][:]

                plons,plats = bingProjection(lons,lats)

                plons = plons[0,:]
                plats = plats[:,0]

                slab = depthSliceOnly(rtime,float(rdepth),control["RowKey"])[1:,1:]
                ds.close()

                buf = BytesIO()
                plot_to_bytes(plons,plats,slab,buf,float(control["color_min"]), float(control["color_max"]),cmap_name=cmap)
                buf.seek(0)
                data = buf.read()
                buf.close()

                cache.blobstore.put_block_blob_from_bytes('liveocean', json_request, data)
        
                response = HttpResponse(data,'image/png')
         
            return response
        except Exception as a:
            try:
                ds.close()
            except:
                print ""
            a.message
            return cr.invalid_parameter()

@cache_control(must_revalidate=True, max_age=3600)
def getinfo(request):
    '''
    Returns parameter metadata.

    If the param argument is present it returns only that parameter's information.
    
    or

    The information about all of the parameters.
    '''
    assert isinstance(request, HttpRequest)
    try:
        param = request.GET.get("param",None)
        if param:
            resp = fieldManager.getInfo(param)
        else:
            resp = fieldManager.getAll()

        return HttpResponse(json.dumps(resp),'application/json')
    except:
        raise Http404()

def clearservercache(request):
    '''
    This is a debug request. It is dangerous. Cassandra!!
    '''
    assert isinstance(request, HttpRequest)
    import tempfile, os
    td = tempfile.gettempdir()
    # Potential disaster here...
    files = [ f for f in os.listdir(td) if f.endswith(".nc") ]
    resp = []

    desiredSize = request.GET.get("size", None)

    try:
        desiredSize = int(desiredSize)
    except:
        desiredSize = None

    for f in files:
        path = "{0}\\{1}".format(td,f)
        i = {
                "file": f,
                "size": os.path.getsize(path),
                "deleted": "Nope."
            }
        try:
            if desiredSize and i["size"] < desiredSize :
                # and another one right here....
                os.remove(path)
                i["deleted"] = "Yes"
        except Exception as a:
            i["deleted"] = "No, {0}".format(a.message)
        
        resp.append(i)

    return HttpResponse(json.dumps(resp),'application/json')

def listcache(request):
    assert isinstance(request, HttpRequest)
    import tempfile, os
    td = "{0}".format(tempfile.gettempdir())
    files = [ {"file": f, "size": os.path.getsize("{0}\\{1}".format(td,f))} 
                for f in os.listdir(td) 
                    if f.endswith(".nc") ]

    return HttpResponse(json.dumps(files),'text/html')