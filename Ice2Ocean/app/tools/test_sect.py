"""
Test of making a section plot.

This relies on having also run test_z.m and specifying
the same data to extract (e.g. which vertical profile)

Parker MacCready
Modified by Nels Oscar
"""

# SETUP

# USER: set paths
pytools_path = '../pytools'
tracks_path = ''
which_track = 'jdf2psTrack'
fn = 'ocean_his_4000.nc' # history file to plot
coast_file = 'pnw_coast_combined.mat'

# imports
import os; import sys
import zfun
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import netCDF4 as nc 
import scipy.io
import builder as b

# GET DATA
G, S, T = zfun.get_basic_info(fn)
  
ds = b.fetch_ds(fn)

h = G['h']
zeta = ds.variables['zeta'][:]
zeta = zeta.squeeze()
zr = zfun.get_z(h, zeta, S, only_rho=True)
salt = ds.variables['salt'][:]
salt = salt.squeeze()

L = G['L']
M = G['M']
N = S['N']

lon = G['lon_rho']
lat = G['lat_rho']
mask = G['mask_rho']
maskr = mask.reshape(1, M, L).copy()
mask3 = np.tile(maskr, [N, 1, 1])
zbot = -h

# make sure fields are masked
zeta[mask==False] = np.nan
zbot[mask==False] = np.nan
salt[mask3==False] = np.nan

# get the coastline
cmat = scipy.io.loadmat(coast_file)
clon = cmat['lon'].squeeze()
clat = cmat['lat'].squeeze()

# INTERPOLATION

# get the track to interpolate onto
mat = scipy.io.loadmat(tracks_path + which_track + '.mat')
x = mat['x'].squeeze()
y = mat['y'].squeeze()
name = mat['name']
if 'along_dist' in mat.keys():
    dist = mat['along_dist']
else:
    pass # need to make dist by hand  


distr = dist.reshape(1, len(dist)).copy()
dista = np.tile(distr, [N, 1]) # array

# pack fields to process in dicts
d2 = dict()
d2['zbot'] = zbot
d2['zeta'] = zeta
d2['lon'] = lon
d2['lat'] = lat
d3 = dict()
d3['zr'] = zr
d3['salt'] = salt

# get vectors describing the (plaid) grid
xx = lon[1,:]
yy = lat[:,1]
xit = zfun.get_interpolant(x, xx)
yit = zfun.get_interpolant(y, yy)

# and prepare them to do the bilinear interpolation
xita = np.array(xit)
yita = np.array(yit)
col0 = xita[:, 0].astype(int)
col1 = xita[:, 1].astype(int)
colf = xita[:, 2]
colff = 1 - colf
row0 = yita[:, 0].astype(int)
row1 = yita[:, 1].astype(int)
rowf = yita[:, 2]
rowff = 1 - rowf

# now actually do the interpolation

# 2-D fields
v2 = dict()
for fname in d2.keys():
    fld = d2[fname]
    fldi = rowff*(colff*fld[row0, col0] + colf*fld[row0, col1]) + rowf*(colff*fld[row1, col0] + colf*fld[row1, col1])
    if type(fldi) == np.ma.core.MaskedArray:
        fldi = fldi.data # just the data, not the mask
    v2[fname] = fldi

# 3-D fields
v3 = dict()
for fname in d3.keys():
    fld = d3[fname]
    fldi = rowff*(colff*fld[:, row0, col0] + colf*fld[:, row0, col1]) + rowf*(colff*fld[:, row1, col0] + colf*fld[:, row1, col1])
    if type(fldi) == np.ma.core.MaskedArray:
        fldi = fldi.data # just the data, not the mask
    v3[fname] = fldi
v3['dist'] = dista

# make "full" fields by padding top and bottom
#
nana = np.nan * np.ones((N + 2, len(dist))) # blank array
v3['zrf'] = nana.copy()
v3['zrf'][0,:] = v2['zbot']
v3['zrf'][1:-1,:] = v3['zr']
v3['zrf'][-1,:] = v2['zeta']
# 
v3['saltf'] = nana.copy()
v3['saltf'][0,:] = v3['salt'][0,:]
v3['saltf'][1:-1,:] = v3['salt']
v3['saltf'][-1,:] = v3['salt'][-1,:]
#
v3['distf'] = nana.copy()
v3['distf'][0,:] = v3['dist'][0,:]
v3['distf'][1:-1,:] = v3['dist']
v3['distf'][-1,:] = v3['dist'][-1,:]
# NOTE: should make this a function (but note that it is specific to each variable)

# PLOTTING
plt.close()
fig = plt.figure(figsize=(20, 8))


# map
ax = fig.add_subplot(131)
cmap = plt.get_cmap(name='Set3')
ax.contourf(lon, lat, zbot, 50, vmin=-3000, vmax=0, cmap=cmap)
plt.rcParams['contour.negative_linestyle'] = 'solid'
ax.contour(lon, lat, zbot, [-2000, -1000, -500, -200, -100], colors='g')
ax.set_xlim(lon.min(), lon.max())
ax.set_ylim(lat.min(), lat.max())
ax.plot(x, y, '-r', linewidth=2)
# test the interpolation routine
#ax.plot(v2['lon'], v2['lat'], '*k') # RESULT: it works
# add coastline
ax.plot(clon, clat, '-k', linewidth=.5)
ax.set_aspect(1/np.sin(np.pi*46/180))
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Bathymetry and Section Track')

# section
ax = fig.add_subplot(1, 3, (2, 3))
ax.plot(dist, v2['zbot'], '-k', linewidth=2)
ax.plot(dist, v2['zeta'], '-b', linewidth=1)
ax.set_xlim(dist.min(), dist.max())
ax.set_ylim(v3['zr'].min(), 5)
cmap = plt.get_cmap(name='rainbow')
cs = ax.contourf(v3['distf'], v3['zrf'], v3['saltf'], 50, vmin=28, vmax=34, cmap=cmap)
# for some reason the vmin/max are overridden on the plot
fig.colorbar(cs)
cs = ax.contour(v3['distf'], v3['zrf'], v3['saltf'], np.arange(0, 40, .25), colors='k')
ax.set_xlabel('Distance (km)')
ax.set_ylabel('Z (m)')
ax.set_title('{0} Salinity'.format(name[0]))

fig.savefig("temp.png", transparent=True)
b.upload_images_on_list([{'path': 'temp.png','name':'depth_test.png'}])