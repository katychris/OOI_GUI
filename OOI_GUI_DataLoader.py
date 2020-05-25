"""
This code:
1. loads the downloaded netcdf data into a nice pandas dataframe.
2. creates a new output folder if one does not exist
3. saves the pandas dataframe as a pickle file in that folder
4. Maybe there should be a use input for the file and folder names?
It should probably get merged with the DataGrabber later on (once it's done).
HEG (5/25/2020)
"""


# imports
import numpy as np
import netCDF4 as nc 
import sys, os
import ooi_mod # module with the directory creation function
from datetime import datetime, timedelta

# # get the current working directory:
# dir_path = pwd

# # make an output directory for the data, one level up
# a = dir_path.split('/') # makes a list out of the path name
# a[-1] = 'ooi_data' # change final directory to be the output data directory
# out_dir = '/'.join(a) # remerge name

# # make the output directory, if it does not exist
# ooi_mod.make_dir(out_dir)

# # load the netcdf data:
# fname = out_dir + selected_datasets
# ds = nc.Dataset(fnames)

# # save as a pickle file:
# out_y = out_dir + '.p'
# pickle.dump(y, open(out_y, 'wb')) # 'wb' is for write binary

fname = '../../../output/ocn506/test.nc'
ds=nc.Dataset(fname)

x = ds['lon'][:]
if x.max() > 180:
    x = x - 360 # convert to -180:180 format
y = ds['lat'][:]