import pandas as pd

# Instrument Information
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

st_df.to_pickle('./Station_Info.pkl')

