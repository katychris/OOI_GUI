"""
OOI_GUI_DataGrabber
Written by: Katy Christensen, Hannah Glover, Susanna Michael, and Theresa Whorley

Last Updated: June 8th, 2020

Git: https://github.com/katychris/OOI_GUI.git

This code is used for grabbing and formatting OOI Data.
First it brings up a map of OOI Cabled Array stations with profiling CTD data. 
The user selects one of the stations and the date range. 
If no matching request exists on the requesting platform then a data request is created through the OOI Data Portal. 
The data is then downloaded locally, loaded into a DataFrame, and saved as a pickle file.

Input: 
- API Username/Token: each user is issued a unique username and token when they register for an account with the OOI Data Portal (https://ooinet.oceanobservatories.org/) 
- Station Names: there are 6 options available
- Date Range: there are a few pre-made suggestions as well as a custom selection option
- (Optional argparse) -f True/False: if f_update is turned on (True) the file will reload regardless of if it is already a file that exists

Output: map of station locations, netcdf file with CTD data, and pickle file with CTD data in a pandas DataFrame

DataFrame structure:
index = Time (UTC)	Pressure (dbar)	Temperature (deg_C)	Salinity (PSU)	Density (kg/m3)

Station Location Options: Oregon Offshore, Slope Base, Axial Base with shallow/deep for each

Dependencies: numpy, datetime, time, netCDF4, xarray, pandas, sys, os, matplotlib.pyplot, cmocean, ooi_mod*
* ooi_mod: custom package contained in Github

"""


# imports
import os,sys
import numpy as np
import netCDF4 as nc
import xarray as xr
import pandas as pd
import requests, argparse
import time
from datetime import datetime,timedelta, date
import matplotlib as mpl
import matplotlib.pyplot as plt
import cmocean
import ooi_mod # our very own module!

# atuo-sense what machine you're working on and make suitable plotting choices
# i.e. what kind of matplotlib import if on remote machine or not
# copied all of this from Parker's 'remote_printing.py' script
host = os.getenv('HOSTNAME')
if host == None:
    save_fig = False
elif 'fjord' in host:
    mpl.use('Agg')
    save_fig = True
else:
    print('What machine is this?')
    sys.exit()

# Create an arparse argument
# If f_update is turned on (True) the fil will reload 
# regardless of if it is already a file that exists
# This is useful if there is a timeout or error while loading
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file_update', default=False, type=ooi_mod.boolean_string)
args = parser.parse_args()
f_update=args.file_update

# # Please insert your API Username and Token here
print('An account with for OOI data portal is required to access this data. '+
	'To create an account, visit: https://ooinet.oceanobservatories.org/ ')
API_USERNAME = input('API Username: ')
API_TOKEN = input('API Token: ')
API_USERNAME = API_USERNAME.strip()
API_TOKEN = API_TOKEN.strip()

# Create an error if there is no username or token
class LoginError(Exception):
	pass
if len(API_USERNAME)==0 or len(API_TOKEN)==0:
	print()
	raise LoginError('Please input your API Username and Token')

# Create an error if the time selected by the user is not useable
class TimeError(Exception):
	pass

# get the current working directory then only keep name up 2 levels
# this will be used as the root for /code, /ooi_data, /ooi_output:
dir_path = os.getcwd()
a = dir_path.split('/') # makes a list out of the path name
dir_name = a[-1]
del a[-1:]# remove last two directories
dir_path = '/'.join(a)

# make an input data directory:
in_dir = dir_path+'/'+dir_name+'_data'
ooi_mod.make_dir(in_dir)

# make an output data directory:
out_dir = dir_path+'/'+dir_name+'_output'
ooi_mod.make_dir(out_dir)

# Instrument Information
#---------------------------------------------------------------------------------------------------
# This is all of the info for the CTDs at our stations
# I have hard coded it here, but I am looking for a way to grab this from the web instead?
# I might just pickle this dataframe and have it readable in the git repo
station_info = {'Oregon_Offshore_Deep':
                ['CE04OSPD','DP01B','01-CTDPFL105','recovered_inst','dpc_ctd_instrument_recovered',
                '2014-08-16T23:30:00.000Z','2019-08-30T22:07:54.328Z','44.36829','-124.9528'],
                
                'Oregon_Offshore_Shallow':
                ['CE04OSPS','SF01B','2A-CTDPFA107','streamed','ctdpf_sbe43_sample',
                '2014-11-05T21:30:49.640Z','2019-11-13T19:54:41.760Z','44.37415','-124.95648'],
                
                'Slope_Base_Deep':
                ['RS01SBPD','DP01A','01-CTDPFL104','recovered_inst','dpc_ctd_instrument_recovered',
                '2015-07-22T21:19:34.153Z','2019-07-02T07:46:00.000Z','44.52757','-125.38075'],
                
                'Slope_Base_Shallow':
                ['RS01SBPS','SF01A','2A-CTDPFA102','streamed','ctdpf_sbe43_sample',
                '2014-10-06T22:05:23.269Z','2019-09-27T18:41:52.175Z','44.52897','-125.38966'],
                
                'Axial_Base_Deep':
                ['RS03AXPD','DP03A','01-CTDPFL304','recovered_inst','dpc_ctd_instrument_recovered',
                '2014-08-09T21:00:00.000Z','2020-01-17T19:32:36.920Z','45.82972','-129.75904'],
                
                'Axial_Base_Shallow':
                ['RS03AXPS','SF03A','2A-CTDPFA302','streamed','ctdpf_sbe43_sample',
                '2014-10-07T21:32:53.602Z','2020-05-09T05:15:48.072Z','45.83049','-129.75326']}

st_df = pd.DataFrame.from_dict(station_info, orient='index',
	columns=['Site','Node','Instrument','Method','Stream','Start_Date','End_Date','Lat','Lon'])
st_df.to_pickle('./Station_Info.p')

# Mapping
#---------------------------------------------------------------------------------------------------
#Set formatting variables to use in the whole code
fs = 12 #Font size

#Code to grab gebco bathymetry data
# Set the maximum and minimum lats and lons
lat_min = 43; lat_max = 48
lon_min = -131; lon_max = -120

# This gets the index values for the lats and lons selected above
# 3600 arc seconds per degree, GEBCO is 15 arc second resolution, indexing starts at -180 lon and -90 lat
lat_min_index = (lat_min + 90) * 240; lat_max_index = (lat_max + 90) * 3600/15 
lon_min_index = (lon_min + 180) * 240; lon_max_index = (lon_max + 180) * 3600/15

# This is the link to select out just the data we want, lot of string formatting :)
print('\nGetting bathymetry/topography data...')
url = 'http://tds.marine.rutgers.edu/thredds/dodsC/other/bathymetry/GEBCO_2019/GEBCO_2019.nc?lat[%d:1:%d],lon[%d:1:%d],elevation[%d:1:%d][%d:1:%d]'%(lat_min_index,lat_max_index,lon_min_index,lon_max_index,lat_min_index,lat_max_index,lon_min_index,lon_max_index)

# Read in the data using netCDF4
gebco = nc.Dataset(url)

#Code based off of https://stackoverflow.com/questions/38246282/contour-data-with-cartopy
g_lon = gebco.variables['lon'][:]
g_lat = gebco.variables['lat'][:]
z = gebco.variables['elevation'][:]
z_max = z.max()
z_min = z.min()
gebco.close()

print('Making a map!')
plt.close('all')
fig = plt.figure(figsize=(10, 8))  #set figure size and projection                    
ax = fig.add_subplot(111)

cmap = cmocean.tools.crop(cmocean.cm.topo, vmin = z_min, vmax = z_max, pivot = 0) #Adjust color bar to show land and ocean
cs = ax.pcolormesh(g_lon, g_lat, z, cmap = cmap)
cbar = fig.colorbar(cs,pad=0.1) #Show color bar
cbar.set_label('Elevation (m)', rotation=270)  #Label color bar
ax.xaxis.tick_top()
ax.set_xlabel('Longitude', size=fs,fontweight='bold')
ax.xaxis.set_label_position('top') 
ax.set_ylabel('Latitude', size=fs,fontweight='bold')
ax.tick_params(labelsize=fs)
ooi_mod.dar(ax)

#Load in pickle file of station locations
st_df = pd.read_pickle('./Station_Info.p')
st_df['Station'] = st_df.index.copy()
st_lat = st_df['Lat'].astype(float)
st_lon = st_df['Lon'].astype(float)

# add station locations and labels
ax.plot(st_lon,st_lat , '#652666', marker = 'o', markersize=7, linewidth = 0)
ax.text(st_lon['Oregon_Offshore_Shallow'], st_lat['Oregon_Offshore_Shallow']-0.3,'Oregon Offshore', weight = 'bold', horizontalalignment='right',
    bbox=dict(facecolor='w', edgecolor='None', alpha=0.3))  
ax.text(st_lon['Slope_Base_Shallow']-0.4, st_lat['Slope_Base_Shallow']+ 0.205,'Slope Base', weight = 'bold',
    bbox=dict(facecolor='w', edgecolor='None', alpha=0.3))
ax.text(st_lon['Axial_Base_Shallow'], st_lat['Axial_Base_Shallow']+0.18,'Axial Base', weight = 'bold',
    bbox=dict(facecolor='w', edgecolor='None', alpha=0.3))

# Save the plot by calling plt.savefig() BEFORE plt.show()
fig_name = 'OOI_GUI_Bathymetry.png'
if save_fig:
	plt.savefig(out_dir+'/'+fig_name)
	print('Map Saved!')
elif not save_fig:
	plt.savefig(out_dir+'/'+fig_name)
	plt.show()
	print('Map displayed!')


# User Selections - Stations and time range
#---------------------------------------------------------------------------------------------------
# Print out the stations numbered for user selection
st_sel = st_df.index
my_choice1 = ooi_mod.list_picker('Station Selection',st_sel)
Station = st_sel[int(my_choice1)-1]

# Get all of the info for that station
site = st_df.loc[Station]['Site']
node = st_df.loc[Station]['Node']
instrument = st_df.loc[Station]['Instrument']
method = st_df.loc[Station]['Method']
stream = st_df.loc[Station]['Stream']
tst = st_df.loc[Station]['Start_Date']
ted = st_df.loc[Station]['End_Date']

# Have the min and max times as datetime format for that station
station_start_time = datetime.strptime(tst[0:19],'%Y-%m-%dT%H:%M:%S')
station_end_time = datetime.strptime(ted[0:19],'%Y-%m-%dT%H:%M:%S')

# Set up start and end times for a few supplied options
tos = [[station_end_time - timedelta(days=90),station_end_time],
[station_end_time - timedelta(days=183),station_end_time],
[station_start_time,station_start_time + timedelta(days=183)],
[station_start_time, station_end_time]]

# Create a list for our pre-supplied options and print it to the screen for user selection
opts = [tos[0][0].strftime('%Y-%m-%d')+' to '+tos[0][1].strftime('%Y-%m-%d')+' (Last 90 Days)',
		tos[1][0].strftime('%Y-%m-%d')+' to '+tos[1][1].strftime('%Y-%m-%d')+' (Last 6 Months)',
		tos[2][0].strftime('%Y-%m-%d')+' to '+tos[2][1].strftime('%Y-%m-%d')+' (First 6 Months)',
		tos[3][0].strftime('%Y-%m-%d')+' to '+tos[3][1].strftime('%Y-%m-%d')+' (Entire Time Series)',
		'Custom Date Range']

# Print out the time options numbered for user selection
if 'Deep' in Station:
	my_choice = ooi_mod.list_picker('Time Selection',opts[3:])
	ini = int(my_choice)+3
else:
	my_choice = ooi_mod.list_picker('Time Selection',opts)
	ini = int(my_choice)



# Go through the user's option saving the start and end times
if (ini < len(opts)-1) and (ini>0):
	start_time = tos[ini-1][0]
	end_time = tos[ini-1][1]
	time_diff = end_time-start_time

# Since loading the entire dataset is slow, I have put a warning in here
elif ini == len(opts)-1:
	print('\nWarning: Using the entire time series can be slow! (Particularly for shallow stations)')
	checky = input('Are you sure you want to continue y(enter)/n?')
	if checky.lower().startswith('y') or len(checky)==0:
		start_time = tos[ini-1][0]
		end_time = tos[ini-1][1]
		print('Full Time Selected')
	else:
		print('\nExiting!')
		sys.exit()
	time_diff = end_time-start_time

# Allow for users to put in a custom date range
elif ini == len(opts):
	print('\nPossible Time Range: ',station_start_time,' to ',station_end_time,'\n')
	print('Input Format: YYYY-mm-dd HH:MM:SS')
	print('Date (YYYY-mm-dd) is required; Time (HH:MM:SS) is optional, default 00:00:00')

	# User input
	st_time = input('Start Time: ')
	ed_time = input('End Time: ')

	# Make inputs into datetime objects
	if len(st_time)< 10 or len(ed_time)< 10:
		raise TimeError('No time selected. Please try again!')
	elif len(st_time)==10:
		start_time = np.max([datetime.strptime(st_time[0:10].strip(),'%Y-%m-%d'),station_start_time])
	elif len(st_time) == 19:
		start_time = datetime.strptime(st_time.strip(),'%Y-%m-%d %H:%M:%S')

	if len(ed_time)==10:
		end_time = np.min([datetime.strptime(ed_time[0:10].strip(),'%Y-%m-%d'),station_end_time])
	elif len(ed_time) == 19:
		end_time = datetime.strptime(ed_time.strip(),'%Y-%m-%d %H:%M:%S')

	time_diff = end_time-start_time

	# If the input date range is outside of the given instrument, give an error
	if ((start_time-station_start_time).days < 0) or ((end_time-station_end_time).days>0):
		raise TimeError('Please select a time within the given range.')
	print('\nTime Range: ',start_time,' to ',end_time,'\n')

if not save_fig:
	plt.close('all')

# Retrieving Data
#---------------------------------------------------------------------------------------------------
# Make the start and end times into useable strings
start_time = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
end_time = end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')

# Create a file name where the data will be saved
fname = in_dir+'/'+Station+'_'+'_'.join([start_time,end_time])+'.nc'

# If this file already exists (and the user does not want to update), pull from there!
if os.path.isfile(fname) and not f_update:
	print('\nUsing saved netCDF file...')
	ds = nc.Dataset(fname)
	
# Otherwise pull from the THREDDS server
else:
	# Set up the parameters used in the data grab
	params = {'beginDT':start_time,'endDT':end_time,
	  'format':'application/netcdf','include_provenance':'true','include_annotations':'true'}

	# Create the request URL
	api_base_url = 'https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv'
	data_request_url ='/'.join((api_base_url,site,node,instrument,method,stream))

	# Set up changeable variables
	url = []
	fdep = False

	# Get the THREDDS server link either from our pre-made file or from the API request
	# Find if our THREDDS file exists already
	if os.path.isfile(out_dir+'/THREDDS_Servers.txt'):
		# Open the file and go through each line
		with open(out_dir+'/THREDDS_Servers.txt','r') as f:
			loads = f.readlines()
		del_line = ''
		for l in range(0,len(loads)):
			l_list = loads[l].split(',')
			# If the station, the start time, and end time are the same as user input
			# Also, if it has been genereated within the past 2 weeks
			# Use the url we already created, saved in the file
			if (site==l_list[1]) and (start_time==l_list[2]) and (end_time==l_list[3]):
				if (datetime.now()<datetime.strptime(l_list[4][:-1],'%Y-%m-%dT%H:%M:%S.000Z')+timedelta(days=14)):
					url = l_list[0]
					fdep = True
					print('\nTHREDDS Server URL:',url)
				# Remove the line if the link has been active for longer than 2 weeks
				else:
					del_line = loads[l]
		# Resave the file without the old links
		with open(out_dir+'/THREDDS_Servers.txt', 'w') as f:
			for line in loads:
				if line != del_line:
					f.write(line)

	# If the file does not exist or the url is still unfilled, get the THREDDS server using API
	if not os.path.isfile(out_dir+'/THREDDS_Servers.txt') or not fdep:
		r = requests.get(data_request_url, params=params, auth=(API_USERNAME, API_TOKEN))
		data = r.json()
		# If there is a message, something has gone wrong
		if 'message' in data:
			# Error code 404 means that there is no data for the selected time range
			if 'code' in data['message'] and data['message']['code']==404:
				print('Uh oh! No data available for this time period. Please try again!\n')
				sys.exit()
			# Authentication failure means they typed in passcode wrong
			elif 'Authentication failed' in data['message']:
				print('Authentication failed: Please check your login credentials for typos.')
				sys.exit()
		# Get the THREDDS link
		url = data['allURLs'][0]
		with open(out_dir+'/THREDDS_Servers.txt',"a+") as f:
			f.write(','.join([url,site,start_time,end_time, datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')])+'\n')
			print('\nTHREDDS Server URL:',url)
	# Get the datasets
	# We have to wait for the data to appear on the server, try every 15 seconds until it is there
	# Timeout after 10 minutes if they picked one of the premade options (not ful time-series)
	print('\nWaiting for data...')
	selected_datasets = ooi_mod.get_data(url)
	tic = time.time()
	while len(selected_datasets) == 0:
		time.sleep(15)
		print('Waiting...')
		selected_datasets = ooi_mod.get_data(url)
		# Save the amount of time that has passed
		toc = time.time() - tic
		if int(my_choice) < len(opts)-1 and toc > 600:
			# This is out timeout error
			print('Something is wrong... Exiting now.')
			print('Possible malfunction with THREDDS server: try again or use browser to see if the data is available.')
			with open(out_dir+'/THREDDS_Servers.txt','r') as f:
				loads = f.readlines()
			del_line = ''
			for l in range(0,len(loads)):
				l_list = loads[l].split(',')
				if url==l_list[0]:
					del_line = loads[l]
			# Resave the file without the old links
			with open(out_dir+'/THREDDS_Servers.txt', 'w') as f:
				for line in loads:
					if line != del_line:
						f.write(line)
			sys.exit()

	if not fdep:
		# If the time series is relatively short (or if there isn't much data - Deep)
		# We wait 60 extra seconds to let the data all settle in the server
		if time_diff.days<=730 or 'Deep' in Station:
			print('Initializing Dataset...')
			time.sleep(90)
			selected_datasets = ooi_mod.get_data(url)
		# If the time series is long (>1000 days) for a shallow station
		# We wait 15 minutes for the data to settle in the server
		elif (time_diff.days>730) and ('Shallow' in Station):
			print('Waiting...')
			time.sleep(30)
			print('Initializing dataset for shallow station (15 minutes)...')
			time.sleep(900)
			selected_datasets = ooi_mod.get_data(url)

	# Print statements!
	print('Data is loaded!')
	print('\nExtracting and Saving... This will take a moment.')	

	# We should now be able to get all of the data into a structure using netCDF4
	# if len(selected_datasets) == 1:
	if 'Shallow' in Station:
		# Open the dataset and ignore the variables we don't need (there are a lot!)
		ds1 = xr.open_mfdataset(selected_datasets,combine='nested',concat_dim='obs',drop_variables=
			['corrected_dissolved_oxygen','density_qc_executed','driver_timestamp',
			'seawater_pressure_qc_results','practical_salinity_qc_results','provenance',
			'corrected_dissolved_oxygen_qc_executed','corrected_dissolved_oxygen_qc_results',
			'seawater_temperature_qc_results','internal_timestamp','seawater_conductivity_qc_results', 
			'ext_volt0','ingestion_timestamp','port_timestamp','seawater_pressure_qc_executed',
			'deployment','preferred_timestamp','practical_salinity_qc_executed','seawater_temperature_qc_executed', 
			'density_qc_results', 'seawater_conductivity_qc_executed','pressure_temp','temperature','pressure',
			'seawater_conductivity','conductivity','id'])

		# Reformat the coordinates and rename the variables so it matches the deep stations
		ds1 = ds1.reset_coords(['seawater_pressure','lon','lat'])
		ds1 = ds1.rename({'seawater_pressure':'pressure','seawater_temperature':'temp'})

	elif 'Deep' in Station:
		# Open the dataset and ignore the variables we don't need (there are a lot!)
		ds1 = xr.open_mfdataset(selected_datasets,combine='nested',concat_dim='obs',drop_variables=
			['dpc_ctd_seawater_conductivity','conductivity_millisiemens','density_qc_executed',
			'driver_timestamp','id','practical_salinity_qc_results','provenance','internal_timestamp',
			'raw_time_microseconds','ingestion_timestamp','conductivity_millisiemens_qc_executed',
			'port_timestamp','raw_time_seconds','deployment','pressure_qc_results','pressure_qc_executed',
			'preferred_timestamp','temp_qc_executed','dpc_ctd_seawater_conductivity_qc_results',
			'practical_salinity_qc_executed','temp_qc_results','conductivity_millisiemens_qc_results',
			'density_qc_results','dpc_ctd_seawater_conductivity_qc_executed'])

	# Make subsample the data into 10min chunks to cut down on data
	# Reformat the data so that it is easier to save and reload
	del ds1.attrs['_NCProperties'] # This is to deal with a bug with xarray
	ds1 = ds1.swap_dims({'obs':'time'})
	ds1 = ds1.resample(time='10Min',keep_attrs=True).mean(keep_attrs=True)
	ds1 = ds1.swap_dims({'time':'obs'}) 
	ds1 = ds1.assign_coords({'obs':np.arange(0,len(ds1['time']))})
	ds1 = ds1.reset_coords(['time'])
	
	# Save the file, removing if it already exists
	if os.path.isfile(fname):
		os.remove(fname)
	ds1.to_netcdf(fname, mode='w',format='netCDF4')

	# Open the file that we just saved
	ds = nc.Dataset(fname)
	
	

# Manipulating data
#---------------------------------------------------------------------------------------------------
"""
This code:
1. Loads the downloaded netcdf data
2. Converts the OOI time into Python time
3. Creates a pandas dataframe with time, pressure, temperature, salinity, and density
4. Saves the dataframe as a pickle file in the output folder
Dependencies: numpy, datetime, netCDF4, pandas, sys, os, ooi_mod
HEG (5/26/2020)
"""

# switch the .nc name to a pickle name and save in the output directory:
fname1=fname.replace('.nc','.p')

if os.path.isfile(fname1) and not f_update:
	print('\nUsing saved pickle file...')
	print('\nUse the following path as the input to OOI_GUI_DataPlotter.py:')
	print(fname1)
	print('\nDone!')

else:
	print('\nConverting netCDF to pandas dataframe...')
	# relevant fields from netcdf file
	flds = ['time','pressure','practical_salinity','temp','density']
	units = []
	fillval = [np.nan]
	for jj in range (0,len(flds)):
		units.append(ds[flds[jj]].units)
		if jj>0:
			fillval.append(ds[flds[jj]]._FillValue)

	print('Fixing timestamp...')
	# fix the time stamp:
	t_ooi = ds[flds[0]][:] # pull out the time from the netcdf
	t00 = datetime.strptime(units[0].split()[-2]+' '+units[0].split()[-1], '%Y-%m-%d %H:%M:%S')
	t01 = datetime.toordinal(t00)
	H0 = t00.hour/24; M0 = t00.minute/(24*60); S0 = t00.second/(24*3600)
	t0 = t01+H0+M0+S0

	# use this function to convert to a python datetime
	tt =[]
	for jj in range(0,len(t_ooi)):
	    tt.append(ooi_mod.ooi_to_datetime(t_ooi[jj]*60,t0))

	# put the data into a pandas data frame for convenient storage
	df = pd.DataFrame(data=tt,columns=[flds[0]])
	for jj in range (1,len(flds)):
	    temp = ds[flds[jj]][:] #pull out data
	    temp[temp==fillval[jj]]=np.nan # nan any bad vals
	    df.insert(jj,flds[jj],ds[flds[jj]][:])

	# set the time (first col) as index:
	df.set_index('time',inplace=True)
	if os.path.isfile(fname1):
		os.remove(fname1)
	# save the dataframe as a pickle file
	df.to_pickle(fname1)
	print('\nSaving pickle file of pandas dataframe...')
	print('\nUse the following path as the input to OOI_GUI_DataPlotter.py:')
	print(fname1)
	print('\nDone!\n')
