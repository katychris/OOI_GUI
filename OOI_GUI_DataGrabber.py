import requests
import os
import re
import time
import matplotlib.pyplot as plt
import netCDF4 as nc

# Please insert your API Username and Token here
API_USERNAME = ''
API_TOKEN = ''

# Raise an error if there is no username or toaken
class LoginError(Exception):
    pass

if len(API_USERNAME)==0 or len(API_TOKEN)==0:
    raise LoginError('Please input your API Username and Token')

# Instrument Information - Still need to make this able to take user inputs
# We want the user to be able to select their station
site = 'RS01SBPS'
node = 'SF01A'
instrument = '2A-CTDPFA102'
method = 'streamed'
stream = 'ctdpf_sbe43_sample'

# Set up selection parameters - Still need to make this able to take user inputs
# Ideally we can give the user the max/min dates for their selected station
start_time = '2015-04-01T00:00:00.000Z'
end_time = '2015-05-01T00:00:00.000Z'
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
url = data['allURLs'][0]

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

# Get the datasets
# We have to wait for the data to appear on the server, try every 10 seconds until it is there
print('Waiting for data...')
selected_datasets = get_data(url)
while len(selected_datasets) == 0:
    time.sleep(10)
    print('waiting...')
    selected_datasets = get_data(url)
    

# We should now be able to get all of the data into a structure using netCDF4
ds = nc.MFDataset(selected_datasets)
