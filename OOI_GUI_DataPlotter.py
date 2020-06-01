"""
This code plots a measured CTD parameter (T, S, P, rho) in depth v time space.
Meant to be run immediately after 'OOI_GUI_DataLoader.py' script
Dependencies: sys, os, numpy, pandas, matplotlib.pyplot, cmocean
TLW - 5/29/2020
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


# ONLY FOR TESTING  -- read in test pickle file
#data_dir = '/Users/theresawhorley/effcomp/OOI_GUI_data/'
#fname = data_dir + 'testfortheresa.p'
#df = pd.read_pickle(fname)

# read in pickle file
df.read_pickle(save_name)

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
sc1 = ax1.scatter(x, y, c=temp, vmin=0, vmax=35, cmap=cm_temp)
ax1.tick_params(axis='x', direction='in', labelrotation=70)
ax1.tick_params(axis='y', direction='in')
ax1.invert_yaxis()
ax1.set_title('Tempterature (C)')
ax1.set_xlabel(t_utc)
ax1.set_ylabel('Pressure (dbar)')
cbar1 = fig.colorbar(sc1, ax=ax1)

# plot practical salinity as a function of pressure and time
sc2 = ax2.scatter(x, y, c=ps, vmin=30, vmax=35, cmap=cm_ps)
ax2.tick_params(axis='x', direction='in', labelrotation=70)
ax2.tick_params(axis='y', direction='in')
ax2.invert_yaxis()
ax2.set_title('Salinity (PSU)')
ax2.set_xlabel(t_utc)
cbar2 = fig.colorbar(sc2, ax=ax2)

# plot density as a function of pressure and time
sc3 = ax3.scatter(x, y, c=rho, vmin=1024, vmax=1030, cmap=cm_rho)
ax3.tick_params(axis='x', direction='in', labelrotation=70)
ax3.tick_params(axis='y', direction='in')
ax3.invert_yaxis()
ax3.set_title('$Density (kg/m^{3})$')
ax3.set_xlabel(t_utc)
cbar3 = fig.colorbar(sc3, ax=ax3, use_gridspec=True)

# save and show figures
fig_title = fig.suptitle('test01')  # work on how to make this a text string of Station and Node from DataGrabber.py inputs
#fig_name = out_dir + fig_title + '.png'
fig_name = 'test01.png'
plt.tight_layout()
plt.savefig(out_dir)
plt.show()