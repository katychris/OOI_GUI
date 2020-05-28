"""
This code plots a measured CTD parameter (T, S, P, rho) in depth v time space.
Meant to be run immediately after 'OOI_GUI_DataLoader.py' script
Dependencies: sys, os, numpy, pandas, matplotlib.pyplot
TLW - 5/28/2020
"""

# Imports
import sys, os
import numpy as np
import pandas as pd
from datetime import datetime, date

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


# read in pickle file
df.read_pickle(save_name)

# make a figure object with axes of pressure v time
# time is stored as index of DataFrame df
x = df['time']
y = df['pressure']
temp = df['temp']
ps = df['practical_salinity']
rho = df['density']

# make figure with three subplots for three variables
plt.close('all')
f = plt.figure()
f, (ax1, ax2, ax3) = plt.subplots(1,3)
cm_temp = 'coolwarm'  # assign a colormap to temperature
cm_ps = 'YiGnBu'  # assign a colormap to practical salinity
cm_rho = 'cividis'  # assign a colormap to density
t_utc = 'Time (UTC)'  #assign variable to time label

# plot temperature as a function of pressure and time
ax1.scatter(x, y,linewidth=3, label='Temperature', edgecolor='k', c=temp, cmap=cm_temp)
ax1.invert_yaxis()
ax1.legend(loc='lower left')
ax1.set_title('Tempterature by depth, time')
ax1.set_xlabel(t_utc)
ax1.set_ylabel('Pressure (dbar)')

# plot practical salinity as a function of pressure and time
ax2.scatter(x, y, linewidth=3, label='Practical Salinity', edgecolor='k', c=ps, cmap=cm_ps)
ax2.legend(loc='lower left')
ax2.set_title('Salinity by depth, time')
ax2.set_xlabel(t_utc)
ax2.set_ylabel('Practical Salinity (PSU)')

# plot density as a function of pressure and time
ax3.scatter(x, y, linewidth=3, label='Density', edgecolor=='k', c=rho, cmap=cm_rho)
ax3.invert_yaxis()
ax3.legend(loc='lower left')
ax3.set_title('Density by depth, time')
ax3.set_xlabel(t_utc)
ax3.set_ylabel('$Density (kg/m^{3}$')  #note to self: double-check this later

# save and show figures
fig_title = plt.plot('')
fig_name = out_dir + fig_title + '.png'
plt.savefig(out_dir)