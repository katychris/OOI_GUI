"""
This code:
1. Loads the downloaded netcdf data
2. Converts the OOI time into Python time
3. Creates a pandas dataframe with time, pressure, temperature, salinity, and density
4. Saves the dataframe as a pickle file in the output folder
Dependencies: numpy, datetime, netCDF4, pandas, sys, os, ooi_mod
HEG (5/26/2020)
"""


# imports
import numpy as np
import netCDF4 as nc 
import pandas as pd
import sys, os
import ooi_mod # module with the directory creation function
from datetime import datetime, timedelta, date

# get the current working directory then only keep name up 2 levels
# this will be used as the root for /code, /ooi_data, /ooi_output:
dir_path = os.getcwd()
a = dir_path.split('/') # makes a list out of the path name
del a[-2:]# remove last two directories
dir_path = '/'.join(a)

# make an output directory for the data
out_dir = dir_path + '/ooi_output'
ooi_mod.make_dir(out_dir)


####

# relevant fields from netcdf file
flds = ['time','pressure','practical_salinity','temp','density']
units = []
for jj in range (0,len(flds)):
    units.append(ds[flds[jj]].units)

# fix the time stamp:
t_ooi = ds[flds[0]][:] # pull out the time from the netcdf
if '1900' in units[0]: # there are two options for the reference year for the OOI time: 1900,1970
    t0=datetime.toordinal(date(1900,1,1))
elif '1970' in units[0]:
    t0=datetime.toordinal(date(1970,1,1))

# use this function to convert to a python datetime
tt =[]
for jj in range(0,len(t_ooi)):
    tt.append(ooi_mod.ooi_to_datetime(t_ooi[jj],t0))


# put the data into a pandas data frame for convenient storage
df = pd.DataFrame(data=tt,columns=[flds[0]])
for jj in range (1,len(flds)):
     df.insert(jj,flds[jj],ds[flds[jj]][:])

# set the time (first col) as index:
df.set_index('time',inplace=True)

# replace fill values with nans:
df[df==-9999999.0]=np.nan

# write a name for the output pickle file:
fname = #user inputs
save_name = out_dir + fname + '.p'
# save the dataframe as a pickle file
df.to_pickle(save_name)

# # save the metadata as a pickle file:
# pickle.dump(units, open('meta_'+save_name, 'wb')) # 'wb' is for write binary

