"""
Module of functions for the OOI DataGrabber.
HEG (5/25/2020)
"""

# imports
import os, sys, shutil, re
import requests


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


def get_data(url):
    '''Function to grab all data from specified THREDDS server'''
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
            selected_datasets.append(d + '#fillmismatch') #fillmismatch to deal with a bug
    selected_datasets = sorted(selected_datasets)
    return selected_datasets


def list_picker(title,data_list,default_val=1):
    '''Formatting for user input on an item in a list, returns the index of the desired item'''

    print('\n\033[1m' + title + '\033[0m')
    for ii in range(len(data_list)):
        print(str(ii+1) + ': ' + data_list[ii])

    my_choice = input('\n Input Selection Number (return='+str(default_val)+'): ')
    if len(my_choice) == 0:
        my_choice = str(default_val)
    print()
    print('\33[42m'+ data_list[int(my_choice)-1]+'\33[0m')

    return my_choice

