import os,sys,re
import numpy as np
import netCDF4 as nc
import pandas as pd
import requests
import time
from datetime import datetime,timedelta, date
import matplotlib.pyplot as plt
import ooi_mod # module with the directory creation function

# # Please insert your API Username and Token here
# API_USERNAME = ''
# API_TOKEN = ''
API_USERNAME = 'OOIAPI-YMXPV7NOB6V80B'
API_TOKEN = 'C5UE5NIZ8UK'

# Create an error if there is no username or token
class LoginError(Exception):
    pass
if len(API_USERNAME)==0 or len(API_TOKEN)==0:
    raise LoginError('Please input your API Username and Token')

# Create an error if the time selected by the user is not useable
class TimeError(Exception):
  pass

# get the current working directory then only keep name up 2 levels
# this will be used as the root for /code, /ooi_data, /ooi_output:
dir_path = os.getcwd()
a = dir_path.split('/') # makes a list out of the path name
dir_name = a[-2]
del a[-2:]# remove last two directories
dir_path = '/'.join(a)

# make an input data directory:
out_dir = dir_path+'/'+dir_name+'_output/ooi_output'
ooi_mod.make_dir(out_dir)

st_df = pd.read_pickle('./Station_Info.pkl')


# Mapping
#---------------------------------------------------------------------------------------------------
# # Read the map data
# # Set the maximum and minimum lats and lons
# lat_min = 43
# lat_max = 48
# lon_min = -131
# lon_max = -120

# # This gets the index values for the lats and lons selected above
# # 3600 arc seconds per degree, GEBCO 15 arc second res, indexing starts -180 lon and -90 lat
# lat_min = (lat_min + 90) * 240; lat_max = (lat_max + 90) * 3600/15 
# lon_min = (lon_min + 180) * 240; lon_max = (lon_max + 180) * 3600/15

# # This is the link to select out just the data we want, lot of string formatting :)
# url1 = 'http://tds.marine.rutgers.edu/thredds/dodsC/other/bathymetry/GEBCO_2019/GEBCO_2019.nc?'
# url = url1+'lat[%d:1:%d],lon[%d:1:%d],elevation[%d:1:%d][%d:1:%d]'%(
# 	lat_min,lat_max,lon_min,lon_max,lat_min,lat_max,lon_min,lon_max)

# # Read in the data using netCDF4
# topography = nc.Dataset(url)

# Put Map here!


# User Selections 
#---------------------------------------------------------------------------------------------------
# Print out the numbered stations
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
[station_end_time - timedelta(days=365),station_end_time],
[station_start_time,station_start_time + timedelta(days=365)],
[station_start_time, station_end_time]]

# Create a list for our pre-supplied options and print it to the screen for user selection
opts = [tos[0][0].strftime('%Y-%m-%d')+' to '+tos[0][1].strftime('%Y-%m-%d')+' (Last 90 Days)',
		tos[1][0].strftime('%Y-%m-%d')+' to '+tos[1][1].strftime('%Y-%m-%d')+' (Last 1 Year)',
		tos[2][0].strftime('%Y-%m-%d')+' to '+tos[2][1].strftime('%Y-%m-%d')+' (First 1 Year)',
		tos[3][0].strftime('%Y-%m-%d')+' to '+tos[3][1].strftime('%Y-%m-%d')+' (Entire Time Series)',
		'Custom Date Range']
my_choice = ooi_mod.list_picker('Time Selection',opts)
ini = int(my_choice)

# Go through the user's option saving the starts and ends
if (ini < 4) and (ini>0):
	start_time = tos[ini-1][0]
	end_time = tos[ini-1][1]

# Since loading the entire dataset is slow, I have put a warning in here
elif ini == 4:
	print('\nWarning: Using the entire time series can be slow! (Particularly for shallow stations)')
	checky = input('Are you sure you want to continue y(enter)/n?')
	if checky.lower().startswith('y') or len(checky)==0:
		start_time = tos[ini-1][0]
		end_time = tos[ini-1][1]
	else:
		print('\nExiting!')
		sys.exit()

# Allow for users to put in a custom date range
elif ini == len(opts):
	print('Possible Time Range: ',station_start_time,' to ',station_end_time,'\n')
	st_time = input('Start Time (YYYY-mm-dd HH:MM:SS):')
	ed_time = input('End Time (YYYY-mm-dd HH:MM:SS):')

	# Make input into datetime object
	start_time = datetime.strptime(st_time,'%Y-%m-%d %H:%M:%S')
	end_time = datetime.strptime(ed_time,'%Y-%m-%d %H:%M:%S')

	# If the input date range is outside of the given instrument, give an error
	if ((start_time-station_start_time).days < 0) or ((end_time-station_end_time).days>0):
		raise TimeError('Please select a time within the given range.')
	print('\nTime Range: ',start_time,' to ',end_time,'\n')



# Retrieving Data
#---------------------------------------------------------------------------------------------------
# Make the start and end times into useable strings
start_time = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
end_time = end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')

# Set up the parameters used in the data grab
params = {'beginDT':start_time,'endDT':end_time,
  'format':'application/netcdf','include_provenance':'true','include_annotations':'true'}

# Create the request URL
api_base_url = 'https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv'
data_request_url ='/'.join((api_base_url,site,node,instrument,method,stream))

# Get the THREDDS server link either from our pre-made file or from the API request
url = []
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
				print('\nTHREDDS Server URL:',url)

			# Remove the line if the link has been active for longer than 2 weeks
			else:
				del_line = loads[l]
	with open(out_dir+'/THREDDS_Servers.txt', 'w') as f:
		for line in loads:
			if line != del_line:
				f.write(line)

# If the file does not exist or the url is still unfilled, get the THREDDS server
if not os.path.isfile(out_dir+'/THREDDS_Servers.txt') or (len(url)==0):
	# if not in file
	r = requests.get(data_request_url, params=params, auth=(API_USERNAME, API_TOKEN))
	data = r.json()
	
	if 'message' in data:
		if 'code' in data['message']:
			print('Uh oh! No data available for this time period. Please try again!\n')
			sys.exit()
		elif 'Authentication failed' in data['message']:
			print('Please check your login credentials for typos.')
			sys.exit()

	url = data['allURLs'][0]

	with open(out_dir+'/THREDDS_Servers.txt',"a+") as f:
		f.write(','.join([url,site,start_time,end_time, datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')])+'\n')
	print('\nTHREDDS Server URL:',url)

# Get the datasets
# We have to wait for the data to appear on the server, try every 15 seconds until it is there
# Timeout after 8 minutes 
print('\nWaiting for data...')
selected_datasets = ooi_mod.get_data(url)
tic = time.time()
while len(selected_datasets) == 0:
    time.sleep(15)
    print('Waiting...')
    selected_datasets = ooi_mod.get_data(url)
    toc = time.time() - tic
    if int(my_choice) < 4 and toc > 480:
    	print('Something is wrong... Exiting now.')
    	sys.exit()
    
# We should now be able to get all of the data into a structure using netCDF4
if len(selected_datasets) == 1:
	ds = nc.Dataset(selected_datasets[0])
else:
	ds = nc.MFDataset(selected_datasets)

print('Data is loaded!')

# Manipulating data
#---------------------------------------------------------------------------------------------------

# # relevant fields from netcdf file
# flds = ['time','pressure','practical_salinity','temp','density']
# units = []
# for jj in range (0,len(flds)):
#     units.append(ds[flds[jj]].units)

# # fix the time stamp:
# t_ooi = ds[flds[0]][:] # pull out the time from the netcdf
# if '1900' in units[0]: # there are two options for the reference year for the OOI time: 1900,1970
#     t0=datetime.toordinal(date(1900,1,1))
# elif '1970' in units[0]:
#     t0=datetime.toordinal(date(1970,1,1))

# # use this function to convert to a python datetime
# tt =[]
# for jj in range(0,len(t_ooi)):
#     tt.append(ooi_mod.ooi_to_datetime(t_ooi[jj],t0))


# # put the data into a pandas data frame for convenient storage
# df = pd.DataFrame(data=tt,columns=[flds[0]])
# for jj in range (1,len(flds)):
#      df.insert(jj,flds[jj],ds[flds[jj]][:])

# # set the time (first col) as index:
# df.set_index('time',inplace=True)

# # replace fill values with nans:
# df[df==-9999999.0]=np.nan

# # get a name for the output pickle file:
# fname = selected_datasets[0]
# fname = fname.split('.') # makes a list out of the path name
# save_name = out_dir + fname[0] + '.p'
# # save the dataframe as a pickle file
# df.to_pickle(save_name)
# # save the metadata as a pickle file:
# pickle.dump(units, open('meta_'+save_name, 'wb')) # 'wb' is for write binary
