"""
This code plots a measured CTD parameter (T, S, P, rho) in depth v time space.
Meant to be run immediately after 'OOI_GUI_DataLoader.py' script
Dependencies: sys, os, numpy, pandas, matplotlib.pyplot, cmocean
TLW - 06/01/2020
"""

# Imports
import sys, os
import numpy as np
import pandas as pd
from datetime import datetime, date
import cmocean

# atuo-sense what machine you're working on and make suitable plotting choices
# i.e. what kind of matplotlib import if on remote machine or not
# copied all of this from Parker's 'remote_printing.py' script
host = os.getenv('HOSTNAME')
if host == None:
    save_fig = False
    print('Printing to screen')
elif 'fjord' in host:
    print('Printing to file')
    import matplotlib as mpl
    mpl.use('Agg')
    save_fig = True
else:
    print('What machine is this?')
    sys.exit()
import matplotlib.pyplot as plt

# get the current working directory then only keep name up 2 levels
# this will be used as the root for /code, /ooi_data, /ooi_output:
dir_path = os.getcwd()
a = dir_path.split('/') # makes a list out of the path name
dir_name = a[-1]
del a[-1:]# remove last two directories
dir_path = '/'.join(a)

# make an output data directory:
out_dir = dir_path+'/'+dir_name+'_output'
ooi_mod.make_dir(out_dir)

# read in pickle file
fname1 = input("Station File Name")
df.read_pickle(fname1)

# make a figure object with axes of pressure v time
# time is stored as index of DataFrame df
x = df.index
y = df['pressure']
temp = df['temp']
ps = df['practical_salinity']
rho = df['density']

# make figure with three subplots for three variables
plt.close('all')
fig, (ax1, ax2, ax3) = plt.subplots(1,3, sharey=True)
cm_temp = cmocean.cm.tempo  # assign a colormap to temperature
cm_ps = cmocean.cm.haline  # assign a colormap to practical salinity
cm_rho = cmocean.cm.dense  # assign a colormap to density
t_utc = 'Time (UTC)'  #assign variable to time label

# plot temperature as a function of pressure and time
sc1 = ax1.scatter(x, y, c=temp, vmin=np.nanmin(temp), vmax=np.nanmax(temp), cmap=cm_temp)
ax1.tick_params(axis='x', direction='in', labelrotation=70)
ax1.tick_params(axis='y', direction='in')
ax1.invert_yaxis()
ax1.set_title('Temperature $(C)$')
ax1.set_xlabel(t_utc)
ax1.set_ylabel('Pressure (dbar)')
cbar1 = fig.colorbar(sc1, ax=ax1)

# plot practical salinity as a function of pressure and time
sc2 = ax2.scatter(x, y, c=ps, vmin=np.nanmin(ps), vmax=np.nanmax(ps), cmap=cm_ps)
ax2.tick_params(axis='x', direction='in', labelrotation=70)
ax2.tick_params(axis='y', direction='in')
ax2.invert_yaxis()
ax2.set_title('Salinity $(PSU)$')
ax2.set_xlabel(t_utc)
cbar2 = fig.colorbar(sc2, ax=ax2)

# plot density as a function of pressure and time
sc3 = ax3.scatter(x, y, c=rho, vmin=np.nanmin(rho), vmax=np.nanmax(rho), cmap=cm_rho)
ax3.tick_params(axis='x', direction='in', labelrotation=70)
ax3.tick_params(axis='y', direction='in')
ax3.invert_yaxis()
ax3.set_title('Density $(kg/m^{3})$')
ax3.set_xlabel(t_utc)
cbar3 = fig.colorbar(sc3, ax=ax3, use_gridspec=True)

# save and show figures
fig_name = fname1.replace('.p','.png')
plt.tight_layout()
if save_fig:
	plt.savefig(out_dir)
elif not save_fig:
	plt.show()