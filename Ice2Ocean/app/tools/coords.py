import builder as b
ds = b.fetch_ds('ocean_his_4000.nc')
x = ds.variables['lon_rho'][:]
y = ds.variables['lat_rho'][:]
x = ds.variables['lon_rho'][:]
y = ds.variables['lat_rho'][:]
north = y.max()
south = y.min()
east    = x.max()
west  = x.min()
print "{0}, {1}     {2}, {3}".format(north, west, south, east)