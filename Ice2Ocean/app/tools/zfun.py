"""
This module contains functions for extracting data from ROMS history files.

Parker MacCready
"""

import numpy as np
import numpy.ma as ma
import warnings
import netCDF4 as nc
import builder as b
import datetime

def get_interpolant(x, xvec):
    """
    Returns info to allow fast interpolation (I hope).
    
    Input: data point(s) x and coordinate vector xvec
    (both must be 1-D numpy arrays)
    
    Output: indices into xvec that surround x,
    and the fraction 'a' into that segment to find x
    which I call "interpolants"
    returned as a list of three-element tuples,
    with each tuple containing (index below, index above, fraction)
    """
    # input error checking
    if type(x) != np.ndarray or type(xvec) != np.ndarray:
        warnings.warn('get_interpolant(): Inputs must be numpy arrays')
        ind0 = ind1 = a = np.nan
        return zip(ind0, ind1, a)       
    if not np.all(np.diff(xvec) > 0):
        warnings.warn('WARNING from get_interpolant(): xvec must be monotonic and increasing')
        ind0 = ind1 = a = np.nan
        return zip(ind0, ind1, a)

    # some preconditioning of the input
    x = x.flatten()
    xvec = xvec.flatten()
    # xvec.sort()  # not needed because we check above  
    
    # make array of indices
    ind = np.arange(len(xvec))
    
    # preallocate results vectors
    N = len(x)
    ind0 = np.zeros(N)
    ind1 = np.zeros(N)
    a = np.zeros(N)
    
    # calculate results
    n = 0 # a counter
    for xx in x:
        # calculate indices, with some choices about edge and out-of-bounds values
        if xx <= xvec[0]:
            ind0[n] = 0; ind1[n] = 1; a[n] = 0.
        elif xx >= xvec[-1]:
            ind0[n] = len(xvec) - 1; ind1[n] = len(xvec); a[n] = 1.
        else:
            mask = xvec < xx               
            ind0[n] = ind[mask][-1]           
            ind1[n] = ind0[n] + 1       
            # calculate fraction 
            dx = xvec[ind1[n]] - xvec[ind0[n]] 
            dxp = xx - xvec[ind0[n]]
            a[n] = dxp / dx
        
        n += 1
    
    return zip(ind0, ind1, a)
    
def get_basic_info(fn):
    """
    Gets grid, vertical coordinate, and time info from a ROMS NetCDF
    history file with full name 'fn'
    
    Input: the filename
    
    Output: dicts G, S, and T
    
    Notes: I should add some keyword arguments to allow the user to just get
    G or S or T (onlyG=False)
    """
    
    
    
    ds = b.fetch_ds(fn)
    
    # get grid and bathymetry info
    g_varlist = ['h', 'lon_rho', 'lat_rho', 'lon_u', 'lat_u', 'lon_v', 'lat_v',
    'lon_psi', 'lat_psi', 'mask_rho', 'mask_u', 'mask_v', 'pm', 'pn',]
    G = dict()
    for vv in g_varlist:
        G[vv] = ds.variables[vv][:]    
    G['DX'] = 1/G['pm']
    G['DY'] = 1/G['pn']
    G['M'], G['L'] = np.shape(G['lon_rho']) # M = rows, L = columns
    # make the masks boolean
    G['mask_rho'] = G['mask_rho'] == 1
    G['mask_u'] = G['mask_u'] == 1
    G['mask_v'] = G['mask_v'] == 1
    
    # get vertical sigma-coordinate info (vectors are bottom to top)
    s_varlist = ['s_rho', 's_w', 'hc', 'Cs_r', 'Cs_w', 'Vtransform']
    S = dict()
    for vv in s_varlist:
        S[vv] = ds.variables[vv][:]
    S['N'] = len(S['s_rho']) # number of vertical levels
    
    # get time info
    t_varlist = ['ocean_time', 'dstart']
    T = dict()
    for vv in t_varlist:
        T[vv] = ds.variables[vv][:]
    #
    # find  time reference    
    dstart = ds.variables['dstart']
    tu = dstart.units
    import re
    isdash = [m.start() for m in re.finditer('-', tu)]
    iscolon = [m.start() for m in re.finditer(':', tu)]
    #
    year = int(tu[isdash[0]-4:isdash[0]])
    month = int(tu[isdash[1]-2:isdash[1]])
    day = int(tu[isdash[1]+1:isdash[1]+3])
    #
    hour = int(tu[iscolon[0]-2:iscolon[0]])
    minute = int(tu[iscolon[1]-2:iscolon[1]])
    second = int(tu[iscolon[1]+1:iscolon[1]+3])
    #
    tt = datetime.datetime(year, month, day, hour, minute, second)
    delta = datetime.timedelta(0, int(T['ocean_time']))
    T['tm0'] = tt
    T['tm'] = tt + delta
    
    return G, S, T
    
def get_z(h, zeta, S, only_rho=False, only_w=False):
    """
    Used to calculate the z position of fields in a ROMS history file
    
    Input: arrays h (bathymetry depth) and zeta (sea surface height)
    which must be the same size, and dict S created by get_basic_info()
        
    Output: 3-D arrays of z_rho and z_w
    
    NOTE: one foible is that if you input arrays of h and zeta that are
    vectors of length VL, the output array (e.g. z_rho) will have size (N, VL)
    (i.e. it will never return an array with size (N, VL, 1), even if (VL, 1) was
    the input shape).  This is a result of the initial and final squeeze calls.
    """
    
    # input error checking (seems clumsy)
    if type(h) != np.ndarray or type(zeta) not in [np.ndarray, np.ma.core.MaskedArray] or type(S) != dict:
        warnings.warn('WARNING from get_z(): Inputs must be numpy arrays')
           
    # number of vertical levels
    N = S['N']
    
    # remove singleton dimensions    
    h = h.squeeze()
    zeta = zeta.squeeze()
    # ensure that we have enough dimensions
    h = np.atleast_2d(h)
    zeta = np.atleast_2d(zeta)
    # check that the dimensions are the same
    if h.shape != zeta.shape:
        warnings.warn('WARNING from get_z(): h and zeta must be the same shape')
    M, L = h.shape
       
    if not only_w:
        # rho
        # create some useful arrays
        csr = S['Cs_r']
        csrr = csr.reshape(N, 1, 1).copy()
        Cs_r = np.tile(csrr, [1, M, L])
        H_r = np.tile(h.reshape(1, M, L).copy(), [N, 1, 1])
        Zeta_r = np.tile(zeta.reshape(1, M, L).copy(), [N, 1, 1])
        if S['hc'] == 0: # if hc = 0 the transform is simpler (and faster)
            z_rho = H_r*Cs_r + Zeta_r + Zeta_r*Cs_r    
        elif S['hc'] != 0: # need to calculate a few more useful arrays
            sr = S['s_rho']
            srr = sr.reshape(N, 1, 1).copy()
            S_rho = np.tile(srr, [1, M, L])
            Hc_r = np.tile(S['hc'], [N, M, L])      
            if S['Vtransform'] == 1:            
                zr0 = (S_rho - Cs_r) * Hc_r + Cs_r*H_r
                z_rho = zr0 + Zeta_r * (1 + zr0/H_r)         
            elif S['Vtransform'] == 2:        
                zr0 = (S_rho*Hc_r + Cs_r*H_r) / (Hc_r + H_r)
                z_rho = Zeta_r + (Zeta_r + H_r)*zr0
        z_rho = z_rho.squeeze()      
    
    if not only_rho:
        # w
        # create some useful arrays
        csw = S['Cs_w']
        csww = csw.reshape(N+1, 1, 1).copy()
        Cs_w = np.tile(csww, [1, M, L])
        H_w = np.tile(h.reshape(1, M, L).copy(), [N+1, 1, 1])
        Zeta_w = np.tile(zeta.reshape(1, M, L).copy(), [N+1, 1, 1])    
        if S['hc'] == 0: # if hc = 0 the transform is simpler (and faster)
            z_w = H_w*Cs_w + Zeta_w + Zeta_w*Cs_w    
        elif S['hc'] != 0: # need to calculate a few more useful arrays
            sw = S['s_w']
            sww = sw.reshape(N+1, 1, 1).copy()
            S_w = np.tile(sww, [1, M, L])    #
            Hc_w = np.tile(S['hc'], [N+1, M, L])      
            if S['Vtransform'] == 1:            
                zw0 = (S_w - Cs_w) * Hc_w + Cs_w*H_w
                z_w = zw0 + Zeta_w * (1 + zw0/H_w)      
            elif S['Vtransform'] == 2:        
                zw0 = (S_w*Hc_w  + Cs_w*H_w) / (Hc_w + H_w)
                z_w = Zeta_w + (Zeta_w + H_w)*zw0
        z_w = z_w.squeeze()
                
    # return results
    if (not only_rho) and (not only_w):
        return z_rho, z_w
    elif only_rho and (not only_w):
        return z_rho
    elif (not only_rho) and only_w:
        return z_w
        
def dar(ax):
    """
    Fixes the aspect ratio to be locally Cartesian.
    
    Input: axes object
    
    Output: none (but it alters the plot)
    """
    import numpy as np
    yl = ax.get_ylim()
    yav = (yl[0] + yl[1])/2
    ax.set_aspect(1/np.sin(np.pi*yav/180))
    
def get_layer(fld, zr, which_z):
    """
    Creates a horizontal slice through a 3D ROMS data field.  It is very fast
    because of the use of "choose"

    Kilroy says: "The geoid as a zero vertical reference plays an important 
        role in surface data. This should be handled explicitly and explained 
        excrutiating detail in this code; so that a complete newcomer can 
        completely understand and modify it."
    
    Input:
        fld (3D ndarray) of the data field to slice
        z (3D ndarray) of z values
        which_z (ndarray of length 1) of the z value for the layer
        
    Output:
        lay (2D ndarray) fld on z == which_z, with np.nan where it is not 
        defined
    """
    N, M, L = fld.shape # updates N for full fields
    Nmax = 30
    ii = range(0,N,Nmax)
    ii.append(N)
    
    fld0 = np.nan * np.zeros((M, L), dtype=int)
    fld1 = np.nan * np.zeros((M, L), dtype=int)
    z0   = np.nan * np.zeros((M, L), dtype=int)
    z1   = np.nan * np.zeros((M, L), dtype=int)
    
    # NOTE: need fewer than 32 layers to use "choose"
    # so we split the operation into steps in this loop
    j = 0
    while j < len(ii)-1:
        i_lo = ii[j]
        i_hi = min(ii[j+1] + 1, ii[-1]) # overlap by 1
            
        NN = i_hi - i_lo # the number of levels in this chunk
        
        this_zr = zr[i_lo:i_hi].copy()
        this_fld = fld[i_lo:i_hi].copy()
        
        zm = this_zr < which_z
        
        ind0 = np.zeros((M, L), dtype=int)
        ind1 = np.zeros((M, L), dtype=int)
        
        ind0 = (zm == True).sum(0) - 1 # index of points below which_z
        ind1 = ind0 + 1                # index of points above which_z
        
        # dealing with out-of-bounds issues
        # note 0 <= ind0 <= NN-1
        # and  1 <= ind1 <= NN
        # make ind1 = ind0 for out of bounds cases
        ind0[ind0 == -1] = 0    # fix bottom case
        ind1[ind1 == NN] = NN-1 # fix top case
        # and now cells that should be masked have equal indices
        
        this_mask = ind0 != ind1
        
        this_fld0 = ind0.choose(this_fld)
        this_fld1 = ind1.choose(this_fld)
        
        this_z0 = ind0.choose(this_zr)
        this_z1 = ind1.choose(this_zr)
        
        fld0[this_mask] = this_fld0[this_mask]
        fld1[this_mask] = this_fld1[this_mask]
        z0[this_mask] = this_z0[this_mask]
        z1[this_mask] = this_z1[this_mask]
        
        j += 1
    
    # do the interpolation
    dz = z1 - z0
    dzf = which_z - z0
    dz[dz == 0] = np.nan
    fr = dzf / dz
    lay = fld0*(1 - fr) + fld1*fr

    # Mask the results
    lay = ma.masked_where(np.isnan(lay),lay)
    return lay
    
def make_full(flt):
    """
    Adds top and bottom layers to array fld. This is intended for 3D ROMS data
    fields that are on the vertical rho grid, and where we want (typically for
    plotting purposes) to extend this in a smart way to the sea floor and the
    sea surface.
    
    Input:
        flt is a tuple with either 1 ndarray (fld_mid),
        or 3 ndarrays (fld_bot, fld_mid, fld_top)
        
    Output:
        fld is the "full" field
    """
    
    if len(flt)==3:
       fld = np.concatenate(flt, axis=0) 
    
    elif len(flt)==1:
        fld_mid = flt[0]
        N, M, L = fld_mid.shape
        fld_bot = fld_mid[0].copy()
        fld_bot = ma.masked_array(fld_bot.reshape(1, M, L).copy(), fld_mid[0]._mask)
        fld_top = fld_mid[-1].copy()
        fld_top = ma.masked_array(fld_top.reshape(1, M, L).copy(),fld_mid[-1]._mask)
        fld = np.concatenate((fld_bot, fld_mid, fld_top), axis=0)
        
    return fld