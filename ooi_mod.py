"""
Module of functions for the OOI DataGrabber.
HEG (5/25/2020)
"""

# imports
import os, sys, shutil
from datetime import timedelta, datetime

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