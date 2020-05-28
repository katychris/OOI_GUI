"""
Module of functions for the OOI DataGrabber.
HEG (5/25/2020)
"""

# imports
import os, sys, shutil
from datetime import timedelta, datetime
import requests
import re


def make_dir(dirname, clean=False):
    """
    Make a directory if it does not exist.
    Use clean=True to clobber the existing directory.
    """
    if clean == True:
        shutil.rmtree(dirname, ignore_errors=True)
        os.mkdir(dirname)
    else:
        try:
            os.mkdir(dirname)
        except OSError:
            pass # assume OSError was raised because directory already exists

# fix the OOI time stamp and convert to python
def ooi_to_datetime(datenum,t0):
    # inputs:
    #   datenum = an OOI time value
    #   t0= reference date (from the netcdf units)
    # OOI time is in seconds from either 1900 or 1970, depending on staiton
    # python ordinal time starts starts

    # day = integer of datenum (no decimal) - 366
    DD = t0 + datenum/[24*60*60]
    DD=datetime.fromordinal(int(DD))
    # calculate hour, min, sec from the fraction of a day in datenum:
    HH = datenum % 1 * 24
    MM = HH % 1 * 60
    SS = MM % 1 * 60
    FF = SS % 1 * 1000

    HH = timedelta(hours=int(HH))
    MM = timedelta(minutes=int(MM))
    SS = timedelta(seconds=int(SS))
    FF = timedelta(milliseconds=int(round(FF)))
    
    return DD + HH + MM + SS + FF


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