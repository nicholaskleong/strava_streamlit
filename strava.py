import os
import requests
import urllib3
import pandas as pd
import numpy as np
from datetime import timedelta,datetime
import pytz
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import polyline

import matplotlib.pyplot as plt

BASE_URL = 'https://www.strava.com/'
tz = pytz.timezone('Australia/Sydney')
def get_access_token(client_id,client_secret,refresh_token) ->str:
    '''Use refresh token to get new access token'''
    auth_url = f'{BASE_URL}oauth/token'
    

    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': "refresh_token",
        'f': 'json'
    }
    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()['access_token']
    return access_token

def get_activities(access_token):
    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    activites_url = f'{BASE_URL}/api/v3/athlete/activities'
    my_dataset = requests.get(activites_url, headers=header, params=param).json()
    activities = pd.json_normalize(my_dataset)
    return activities

def clean_activities(activities):
    activities['start_date']=pd.to_datetime(activities.start_date_local)
    activities['distance_km'] = activities.distance/1000
    activities = activities.sort_values('start_date')
    return activities
def calculate_km_interval(speed_ms):
    km_s = 1000/speed_ms
    minutes, seconds = divmod(km_s, 60)
    out = f'{minutes:.0f}:{seconds:02.0f}'
    return out
def make_runs(activities):
    cols = ['id','name','start_date','distance_km','moving_time','elapsed_time','average_speed']
    runs = activities[activities.sport_type.isin(['Run','TrailRun'])][cols]
    # runs['min_km']=runs.apply(lambda row: timedelta(seconds = 1/row['average_speed']*1000),axis=1)
    runs['min_km'] = runs.average_speed.apply(calculate_km_interval)
    runs['label'] = runs.apply(lambda row: f"{row.id} - {row['name']} ({row.distance_km:0.1f}km)", axis=1)
    runs = runs.set_index('start_date')
    runs = runs.sort_index()
    return runs

@st.cache_data(ttl=1200)
def init_data(access_token):
    # access_token = get_access_token(os.environ["client_id"],os.environ["client_secret"],os.environ["refresh_token"])
    activities = get_activities(access_token)
    activities = clean_activities(activities)
    runs = make_runs(activities)
    st.session_state['access_token'] = access_token
    st.session_state['runs'] = runs

def activites_per_week(runs,start_date=datetime(datetime.today().replace(tzinfo=tz).year,1,1,tzinfo=tz)):
    num_weeks = datetime.today().isocalendar()[1]
    num_activites = len(runs[start_date:])
    runs_per_week = num_activites/num_weeks
    return runs_per_week

def activites_last_week(runs):
    return len(runs[datetime.today()-timedelta(days=7):])
    
def distance_last_week(runs):
    temp = runs[datetime.today().replace(tzinfo=tz)-timedelta(days=7):]
    dist_last_week = temp['distance_km'].sum()
    return dist_last_week

def distance_this_year(runs):
    temp = runs[datetime(datetime.today().replace(tzinfo=tz).year,1,1,tzinfo=tz):]
    dist_this_year = temp['distance_km'].sum()
    return dist_this_year
def distance_this_month(runs):
    temp = runs.loc[datetime.today().strftime('%B-%Y')]
    dist_this_month = temp['distance_km'].sum()
    return dist_this_month


week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def get_activity(access_token, idx):
    header = {'Authorization': 'Bearer ' + access_token}
    param = {}
    activity_url = f'{BASE_URL}/api/v3/activities/{idx}'
    activity = requests.get(activity_url, headers=header, params=param).json()
    return activity

def make_array(df,data_col,start_date,end_date):
    size = (max(df['y']),max(df['x']))
    arr = np.zeros(size)
    for i,row in df.iterrows():
        arr[(row.y-1,row.x-1)] = row[data_col]
    arr = arr[start_date.isocalendar().week-1:end_date.isocalendar().week]
    return arr
def make_str_array(df,data_col,start_date,end_date,suffix=''):
    size = (max(df['y']),max(df['x']))
    arr = np.full(size,'',dtype=object)
    for i,row in df.iterrows():
        arr[(row.y-1,row.x-1)] = row[data_col] + suffix
    arr = arr[start_date.isocalendar().week-1:end_date.isocalendar().week]
    return arr

def join_str_arrays(arr1,arr2,arr1_suffix=''):
    if arr1.dtype =='float64':
        arr = arr1.round(2).astype(str).copy()
    else:
        arr = arr1.astype(str).copy()
    for idx, val in np.ndenumerate(arr):
        arr[idx]=str(arr[idx])+arr1_suffix+f'\n{arr2[idx]}'
    return arr

def make_plot_data(runs,start_date,end_date):
    runs['min_km'] = runs.average_speed.apply(calculate_km_interval)

    runs['time'] = runs.moving_time.apply(lambda x: ':'.join(str(timedelta(seconds=x)).split(':')[-3:-1]))
    df = runs.loc[start_date:end_date].copy()
    df['y'] = df.index.isocalendar().week
    df['x']= df.index.isocalendar().day

    dist =make_array(df,'distance_km',start_date,end_date)
    time =make_str_array(df,'time',start_date,end_date, ' hrs')
    pace = make_str_array(df,'min_km',start_date,end_date, ' min/km')
    
    text = join_str_arrays(dist,time,' km')
    text = join_str_arrays(text,pace)
    yticks = list(pd.date_range(start_date,end_date-timedelta(1),freq='W-Mon').strftime('%d-%b-%Y'))
    return dist[1:,:],text[1:,:],yticks

def make_heatmap(dist,text,yticks):
    sz = 18
    ar = 0.6
    fig, ax = plt.subplots(1,1,figsize=(14,5))
    im = ax.imshow(dist, cmap='BuGn',aspect=.6)

    # Add values to each cell
    for i in range(text.shape[0]):
        for j in range(text.shape[1]):
            texta = ax.text(j, i, text[i, j],
                           ha="center", va="center", color="black")

    # Add a label to the colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Distance(km)", rotation=-90, va="bottom")
    # Show the plot
    plt.xticks(list(range(7)),week)
    ax.xaxis.tick_top()
    plt.yticks(list(range(len(yticks))),yticks)
    return fig,ax

def make_weekly_distance_plot(runs):
    df = runs.distance_km.resample('W').sum()
    fig = px.line(df,y='distance_km')
    return fig

def recent_runs(runs):
    n = 10
    display_df = runs.iloc[-n:]
    display_df = display_df.reset_index(drop=False)
    col_map = {'start_date':'Date','name':'Name','distance_km':'Distance','min_km':'Pace','elapsed_time':'Time'}
    display_df = display_df[[col for col in col_map.keys()]]
    display_df = display_df.rename(col_map,axis=1)
    display_df['Date'] = display_df.Date.dt.strftime('%d-%b-%Y')
    display_df['Time'] = display_df.Time.apply(format_seconds)
    return display_df

def format_seconds(seconds):
    h,rem = divmod(seconds,3600)
    m,s = divmod(rem,60)
    time_str = ''
    if h !=0:
        time_str+= f'{h}h '
    time_str+= f'{m}m {s}s'
    return time_str

def make_gauge(value,target,title,suffix):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title},
        number = {"suffix": suffix},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {'axis': {'range': [None, target]}},
    ))
    fig.update_layout(
        height=270,
        width=270,
        font = {'color': "Black"}
    )
    return fig
def make_number(value,title,suffix):
    fig = go.Figure(go.Indicator(
        mode = "number",
        value = value,
        title = {'text': title},
        number = {"suffix": suffix},
        domain = {'x': [0, 1], 'y': [0, 1]},
    ))
    fig.update_layout(
        height=300,
        width=300,
        font = {'color': "Black"}
    )
    return fig

class Run(object):
    def __init__(self,access_token,idx):
        self.idx = idx
        self.access_token = access_token
        self.fields = ['time','altitude','latlng','velocity_smooth']
        self.data = self.get_data()
        self.splits = self.get_splits()
        self.stream_df = self.get_stream_data()
    
    def __repr__(self):
        return f"{self.data['name']} - {self.data['distance']/1000:0.1f}km"
    def get_data(self):
        act = get_activity(self.access_token,self.idx)
        return act
    def get_splits(self):
        splits = pd.json_normalize(self.data['splits_metric'])
        splits['km_interval'] = splits.apply(lambda row: calculate_km_interval(row.average_speed),axis=1)
        return splits
    def make_split_plot(self):
        fig = px.bar(self.splits,'average_speed',
             text = 'km_interval',
            labels = {'index':'Kilometre',
                     'average_speed':'Pace'},
            width=400,
            height=400)
        fig['layout']['yaxis']['autorange'] = "reversed"
        fig['layout']['xaxis']['showticklabels'] = False
        fig.update_traces(marker_color='green')
        return fig
    def make_map(self):
        mp = pd.DataFrame(polyline.decode(self.data['map']['polyline']))
        mp.columns = ['lat','long']
        fig = px.line_mapbox(mp,'lat','long',
                            mapbox_style = 'open-street-map',
                            zoom=13,
                            width=600,
                            height=800)
        return fig
    
    def _get_streams(self,field):
        header = {'Authorization': 'Bearer ' + self.access_token}
        param = {'keys':[field], 'key_by_type':True}
        activity_stream_url = f'{BASE_URL}/api/v3/activities/{self.idx}/streams'
        activity_stream = requests.get(activity_stream_url, headers=header, params=param).json()
        return activity_stream

    def get_stream_data(self):
        dat =[]
        for field in self.fields:
            streams = self._get_streams(field)
            srs = pd.Series(data = streams[field]['data'],index = streams['distance']['data'])
            srs.name = field
            dat.append(srs)
        df = pd.concat(dat,axis=1)
        return df
    def make_analysis_plot(self):
        n=10
        stream_df = self.stream_df        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_scatter(x=stream_df.index,
                        y=stream_df['altitude'],
                        name = 'altitude',
                        mode='lines',
                        secondary_y=False,
                        marker_color='#EE964B'
                    )
        fig.add_scatter(x=stream_df.index,
                        y=stream_df['velocity_smooth'].rolling(n).median(),
                        name = 'speed',
                        mode='lines',
                        secondary_y=True,
                        marker_color = '#0D3B66'
                    )
        fig.update_layout(
            height = 600,
            width = 1200
        )
        return fig