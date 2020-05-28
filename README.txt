This code package is for selecting and downloading OOI Cabled Array, profiling CTD data and then plotting that data.

======================================================================
* OOI_GUI_DataGrabber.py does a series of tasks to prepare data for plotting:
First it brings up a map of OOI Cabled Array stations with profiling CTD data. The user selects one of the stations and the date range. If no matching request exists then a data request is created through the OOI Data Portal. The data is then downloaded locally, loaded into a DataFrame, and saved as a pickle file.


Input: station names, date range

Output: map of station locations and pickle file with CTD DataFrame

DataFrame structure:
index = Time (UTC)	Pressure (dbar)	Temperature (C)	Salinity (PSU)	Density (kg/m3)

Station Location Options:

Dependencies: numpy, datetime, netCDF4, pandas, sys, os, ooi_mod, matplotlib.pyplot, cmocean

Written by: Katy Christensen, Hannah Glover, Susanna Michael, and Theresa Whorley
======================================================================
* ooi_mod.py is a module containing the functions for OOI_GUI_DataGrabber.py 

Dependencies: numpy, datetime, sys, os
======================================================================
* OOI_GUI_DataPlotter
The user can plot the data using OOI_GUI_DataPlotter.py. The script first checks if the user is running on a remote machine and then plots each variable in depth vs. time space.

Dependencies: numpy, sys, os, pandas, matplotlib.pyplot, cmocean
