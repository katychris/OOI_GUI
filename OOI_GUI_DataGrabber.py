import requests
import os,sys
import time
import matplotlib.pyplot as plt
import netCDF4 as nc
from datetime import datetime, timedelta, date
import warnings
import numpy as np
import pandas as pd
import ooi_mod # module with useful function

# Please insert your API Username and Token here
API_USERNAME = ''
API_TOKEN = ''

# Create an error if there is no username or token
class LoginError(Exception):
    pass
if len(API_USERNAME)==0 or len(API_TOKEN)==0:
    raise LoginError('Please input your API Username and Token')

# Create an error if the time selected by the user is not useable
class TimeError(Exception):
	pass

# Instrument Information
# This is all of the info for the CTDs at our stations
# I have hard coded it here, but I am looking for a way to grab this from the web instead?
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


# get the current working directory then only keep name up 2 levels
# this will be used as the root for /ooi_output:
dir_path = os.getcwd()
a = dir_path.split('/') # makes a list out of the path name
del a[-2:]# remove last two directories
dir_path = '/'.join(a)

# make an output directory for the data
out_dir = dir_path + '/ooi_output'
ooi_mod.make_dir(out_dir)


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
#---------------------------------------------------------------------------------------------------

# Print out the numbered stations
print('\n\033[1m' + 'Station Selection' + '\033[0m')
st_sel = st_df.index
for ii in range(len(st_sel)):
	print(str(ii+1) + ': ' + ' '.join([elem for elem in st_sel[ii].split('_')]))

# Have the user select one of the stations
my_choice = input('\n Input Station Number (return=1): ')
if len(my_choice)==0:
    my_choice = 1
Station = st_sel[int(my_choice)-1]
print('\n'+ ' '.join([elem for elem in Station.split('_')]))

# Get all of the info for that station
site = st_df.loc[Station]['Site']
node = st_df.loc[Station]['Node']
instrument = st_df.loc[Station]['Instrument']
method = st_df.loc[Station]['Method']
stream = st_df.loc[Station]['Stream']

# Have the min and max times that the user can select
station_start_time = datetime.strptime(st_df.loc[Station]['Start_Date'][0:19],'%Y-%m-%dT%H:%M:%S')
station_end_time = datetime.strptime(st_df.loc[Station]['End_Date'][0:19],'%Y-%m-%dT%H:%M:%S')

# Give the users a few time plotting options
print('\n\033[1m' + 'Time Selection' + '\033[0m')
opts = ['Last 90 Days','Last 1 Year','First 1 Year','Entire Time Series','Custom Date Range']
for ii in range(len(opts)):
	print(str(ii+1)+ ': ' + opts[ii])

# Have the user select one of the options
my_choice = input('\n Input Time Option (return=1): ')
if len(my_choice)==0:
    my_choice = 1

if int(my_choice) == 1: # Last 90 days
	start_time = station_end_time - timedelta(days=90)
	end_time = station_end_time

elif int(my_choice) == 2: # Last year
	start_time = station_end_time - timedelta(days=365)
	end_time = station_end_time

elif int(my_choice) == 3: # First year
	start_time = station_start_time
	end_time = station_start_time + timedelta(days=365)

elif int(my_choice) == 4: # Entire Time Series
	warnings.warn('\n\nWarning:Using the entire time series can be slow! (Particularly for shallow stations)')
	checky = input('Are you sure you want to continue y(enter)/n?')
	if checky.lower().startswith('y') or len(checky)==0:
		start_time = station_start_time
		end_time = station_end_time
	else:
		exit()

elif int(my_choice) == 5: # Custom Range
	print('Possible Time Range: ',station_start_time,' to ',station_end_time,'\n')
	st_time = input('Start Time (YYYY-mm-dd HH:MM:SS):')
	ed_time = input('End Time (YYYY-mm-dd HH:MM:SS):')

	start_time = datetime.strptime(st_time,'%Y-%m-%d %H:%M:%S')
	end_time = datetime.strptime(ed_time,'%Y-%m-%d %H:%M:%S')

	if ((start_time-station_start_time).days < 0) or ((end_time-station_end_time).days>0):
		raise TimeError('Please select a time within the given range.')

else:
	raise TimeError('Not a valid option. Please choose between 1-5.')

print('\nTime Range: ',start_time,' to ',end_time,'\n')

start_time = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
end_time = end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
params = {
  'beginDT':start_time,
  'endDT':end_time,
  'format':'application/netcdf',
  'include_provenance':'true',
  'include_annotations':'true'
}

# Create the request URL
api_base_url = 'https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv'
data_request_url ='/'.join((api_base_url,site,node,instrument,method,stream))

# Get the THREDDS server link 
# Need to make this so that it looks at a file of previously made links with date range
# Then, only have it run if this data has not been requested before
# This keeps a user from making duplicate servers and helps OOI
r = requests.get(data_request_url, params=params, auth=(API_USERNAME, API_TOKEN))
data = r.json()

if '404' in data:
	print('No data available for this time period. Please try again!\n')
	sys.exit()

url = data['allURLs'][0]
print('THREDDS Server URL:',url)
=======
from datetime import datetime,timedelta
import warnings
import sys

# # Please insert your API Username and Token here
# API_USERNAME = ''
# API_TOKEN = ''
API_USERNAME = 'OOIAPI-YMXPV7NOB6V80B'
API_TOKEN = 'C5UE5NIZ8UK'

# Create a function to get the data files stored on THREDDS server
def get_data(url):
  '''Function to grab all data from specified directory'''
  tds_url = 'https://opendap.oceanobservatories.org/thredds/dodsC'
  datasets = requests.get(url).text
  urls = re.findall(r'href=[\'"]?([^\'" >]+)', datasets)
  x = re.findall(r'(ooi/.*?.nc)', datasets)
  for i in x:
    if i.endswith('.nc') == False:
      x.remove(i)
  for i in x:
    try:
      float(i[-4])
    except:
      x.remove(i)
  datasets = [os.path.join(tds_url, i) for i in x]
  # Remove extraneous data files if necessary
  # This makes sure that the stream and the file match
  catalog_rms = url.split('/')[-2][20:]
  selected_datasets = []
  for d in datasets:
    if catalog_rms == d.split('/')[-1].split('_20')[0][15:]:
      selected_datasets.append(d + '#fillmismatch') # Add #fillmismatch to deal with a bug
  selected_datasets = sorted(selected_datasets)
  return selected_datasets 

# Create an error if there is no username or token
class LoginError(Exception):
    pass
if len(API_USERNAME)==0 or len(API_TOKEN)==0:
    raise LoginError('Please input your API Username and Token')

# Create an error if the time selected by the user is not useable
class TimeError(Exception):
	pass

# Instrument Information
# This is all of the info for the CTDs at our stations
# I have hard coded it here, but I am looking for a way to grab this from the web instead?
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
#---------------------------------------------------------------------------------------------------

# Print out the numbered stations
print('\n\033[1m' + 'Station Selection' + '\033[0m')
st_sel = st_df.index
for ii in range(len(st_sel)):
	print(str(ii+1) + ': ' + ' '.join([elem for elem in st_sel[ii].split('_')]))

# Have the user select one of the stations
my_choice = input('\n Input Station Number (return=1): ')
if len(my_choice)==0:
    my_choice = 1
Station = st_sel[int(my_choice)-1]
print('\n'+ ' '.join([elem for elem in Station.split('_')]))

# Get all of the info for that station
site = st_df.loc[Station]['Site']
node = st_df.loc[Station]['Node']
instrument = st_df.loc[Station]['Instrument']
method = st_df.loc[Station]['Method']
stream = st_df.loc[Station]['Stream']

# Have the min and max times that the user can select
station_start_time = datetime.strptime(st_df.loc[Station]['Start_Date'][0:19],'%Y-%m-%dT%H:%M:%S')
station_end_time = datetime.strptime(st_df.loc[Station]['End_Date'][0:19],'%Y-%m-%dT%H:%M:%S')

# Give the users a few time plotting options
print('\n\033[1m' + 'Time Selection' + '\033[0m')
opts = ['Last 90 Days','Last 1 Year','First 1 Year','Entire Time Series','Custom Date Range']
for ii in range(len(opts)):
	print(str(ii+1)+ ': ' + opts[ii])

# Have the user select one of the options
my_choice = input('\n Input Time Option (return=1): ')
if len(my_choice)==0:
    my_choice = 1

if int(my_choice) == 1: # Last 90 days
	start_time = station_end_time - timedelta(days=90)
	end_time = station_end_time

elif int(my_choice) == 2: # Last year
	start_time = station_end_time - timedelta(days=365)
	end_time = station_end_time

elif int(my_choice) == 3: # First year
	start_time = station_start_time
	end_time = station_start_time + timedelta(days=365)

elif int(my_choice) == 4: # Entire Time Series
	warnings.warn('\n\nWarning:Using the entire time series can be slow! (Particularly for shallow stations)')
	checky = input('Are you sure you want to continue y(enter)/n?')
	if checky.lower().startswith('y') or len(checky)==0:
		start_time = station_start_time
		end_time = station_end_time
	else:
		sys.exit()

elif int(my_choice) == 5: # Custom Range
	print('Possible Time Range: ',station_start_time,' to ',station_end_time,'\n')
	st_time = input('Start Time (YYYY-mm-dd HH:MM:SS):')
	ed_time = input('End Time (YYYY-mm-dd HH:MM:SS):')

	start_time = datetime.strptime(st_time,'%Y-%m-%d %H:%M:%S')
	end_time = datetime.strptime(ed_time,'%Y-%m-%d %H:%M:%S')

	if ((start_time-station_start_time).days < 0) or ((end_time-station_end_time).days>0):
		raise TimeError('Please select a time within the given range.')

else:
	raise TimeError('Not a valid option. Please choose between 1-5.')

print('\nTime Range: ',start_time,' to ',end_time,'\n')

start_time = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
end_time = end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
params = {
  'beginDT':start_time,
  'endDT':end_time,
  'format':'application/netcdf',
  'include_provenance':'true',
  'include_annotations':'true'
}

# Create the request URL
api_base_url = 'https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv'
data_request_url ='/'.join((api_base_url,site,node,instrument,method,stream))

# Get the THREDDS server link 
# Need to make this so that it looks at a file of previously made links with date range
# Then, only have it run if this data has not been requested before
# This keeps a user from making duplicate servers and helps OOI
r = requests.get(data_request_url, params=params, auth=(API_USERNAME, API_TOKEN))
data = r.json()

if '404' in data:
	print('No data available for this time period. Please try again!\n')
	sys.exit()
elif 'Authentication failed' in data:
  print('Please check your login credentials for typos.')
  sys.exit()

url = data['allURLs'][0]
print('THREDDS Server URL:',url)

# Get the datasets
# We have to wait for the data to appear on the server, try every 10 seconds until it is there
# Timeout after 3 minutes (if I've done my job right, this should never happen)
print('Waiting for data...')
selected_datasets = ooi_mod.get_data(url)
tic = time.time()
while len(selected_datasets) == 0:
    time.sleep(10)
    print('Waiting...')
    selected_datasets = ooi_mod.get_data(url)
    toc = time.time() - tic
    if toc > 300:
=======
# Timeout after 8 minutes  (if I've done my job right, this should never happen)
print('Waiting for data...')
selected_datasets = get_data(url)
tic = time.time()
while len(selected_datasets) == 0:
    time.sleep(15)
    print('Waiting...')
    selected_datasets = get_data(url)
    toc = time.time() - tic
    if int(my_choice) < 4 and toc > 480:
    	print('Something is wrong... Exiting now.')
    	break
    
# We should now be able to get all of the data into a structure using netCDF4
if len(selected_datasets) == 1:
	ds = nc.Dataset(selected_datasets[0])
else:
	ds = nc.MFDataset(selected_datasets)

# This section of code:
# 1. Loads the downloaded netcdf data
# 2. Converts the OOI time into Python time
# 3. Creates a pandas dataframe with time, pressure, temperature, salinity, and density
# 4. Saves the dataframe as a pickle file in the output folder

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
fname = Station + '_' + station_start_time + '_' + station_end_time #user inputs
save_name = out_dir + fname + '.p'
# save the dataframe as a pickle file
df.to_pickle(save_name)

# # save the metadata as a pickle file:
# pickle.dump(units, open('meta_'+save_name, 'wb')) # 'wb' is for write binary
=======
print('Data is loaded!')