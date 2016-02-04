'''
Plotting wrappers.

Nels
'''
# Note that this import ordering is significant.
# the matplotlib.use(..) must occur before importing pyplot.
#   Otherwise it will try to use the defualt rendering engine, 
#     which doesn't work
import matplotlib
matplotlib.use('Agg')
# The matplotlib backend must be changed before importing pyplot.
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np

def plot_to_bytes(x,y,c,buf, cmin=None, cmax=None, cmap_name='binary'):

    if not cmin: cmin = c.min()
    if not cmax: cmax = c.max()

    plt.close()
    # fig = plt.figure(figsize=(float(len(y))/100.0, float(len(x))/100.0), dpi=100)
    fig = plt.figure(figsize=(float(len(x))/100.0, float(len(y))/100.0), dpi=100)
    p1 = plt.pcolormesh(x, y, c, vmin=cmin, vmax=cmax, clip_on=False,)
    # use dir(p1) to get list of methods
    p1.set_cmap(plt.get_cmap(name=cmap_name))
    # Turn off the axes and the margins and the borders
    # so the image can be spatially aligned.
    ax = fig.gca()
    ax.set_frame_on(False)
    ax.set_axis_off()
    ax.margins(0, 0)
    plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
    fig.savefig(buf, transparent=True)