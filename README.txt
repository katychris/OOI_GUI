This code package is for selecting and downloading OOI Cabled Array, profiling CTD data and then plotting that data.

======================================================================
* OOI_GUI_DataGrabber.py does a series of tasks to prepare data for plotting:
First it brings up a map of OOI Cabled Array stations with profiling CTD data. The user selects one of the stations and the date range. If no matching request exists on the requesting platform then a data request is created through the OOI Data Portal. The data is then downloaded locally, loaded into a DataFrame, and saved as a pickle file.

Input: 
- API Username/Token: each user is issued a unique username and token when they register for an account with the OOI Data Portal (https://ooinet.oceanobservatories.org/) 
- Station Names: there are 6 options available
- Date Range: there are a few pre-made suggestions as well as a custom selection option

Output: map of station locations, netcdf file with CTD data, and pickle file with CTD data in a pandas DataFrame

DataFrame structure:
index = Time (UTC)	Pressure (dbar)	Temperature (deg_C)	Salinity (PSU)	Density (kg/m3)

Station Location Options:

Dependencies: numpy, datetime, time, netCDF4, xarray, pandas, sys, os, matplotlib.pyplot, cmocean, ooi_mod*

Written by: Katy Christensen, Hannah Glover, Susanna Michael, and Theresa Whorley
======================================================================
* ooi_mod.py is a module containing the functions for OOI_GUI_DataGrabber.py 

make_dir(dirname,clean=False) - creates a directory if it does not exist, use clean=True to remove and recreate the directory
get_data(url) - function to grab all data from specified THREDDS server given as a url
ooi_to_datetime(datenum,t0) - fix the OOI time stamp and convert to python
list_picker() - prints out a list and saves the selection number from the user input
boolean_string(s) - this function helps with getting Boolean input to be used with the argparse capabilities in OOI_GUI_DataGrabber.py

Dependencies: numpy, datetime, sys, os
======================================================================
* OOI_GUI_DataPlotter
The user can plot the data using OOI_GUI_DataPlotter.py. The script first checks if the user is running on a remote machine and then plots each variable in depth vs. time space.

Dependencies: numpy, sys, os, pandas, matplotlib.pyplot, cmocean
