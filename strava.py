import os
import requests
import urllib3
import pandas as pd
from datetime import timedelta,datetime
import pytz
import streamlit as st
import plotly.express as px
import polyline

BASE_URL = 'https://www.strava.com/'
@st.cache_data
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

@st.cache_data
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
    cols = ['id','name','start_date','distance_km','moving_time','average_speed']
    runs = activities[activities.sport_type.isin(['Run','TrailRun'])][cols]
    # runs['min_km']=runs.apply(lambda row: timedelta(seconds = 1/row['average_speed']*1000),axis=1)
    runs['min_km'] = runs.average_speed.apply(calculate_km_interval)
    runs['label'] = runs.apply(lambda row: f"{row.id} - {row['name']} ({row.distance_km:0.1f}km)", axis=1)
    runs = runs.set_index('start_date')
    runs = runs.sort_index(ascending=False)
    return runs

def activites_per_week(runs,start_date=datetime(2023,1,1)):
    num_weeks = datetime.today().isocalendar()[1]
    num_activites = len(runs[start_date:])
    runs_per_week = num_activites/num_weeks
    return runs_per_week

def activites_last_week(runs):
    return len(runs[datetime.today()-timedelta(days=7):])
    
def distance_last_week(runs):
    temp = runs[datetime.today()-timedelta(days=7):]
    dist_last_week = temp['distance_km'].sum()
    return dist_last_week

week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def get_activity(access_token, idx):
    header = {'Authorization': 'Bearer ' + access_token}
    param = {}
    activity_url = f'{BASE_URL}/api/v3/activities/{idx}'
    activity = requests.get(activity_url, headers=header, params=param).json()
    return activity

class Run(object):
    def __init__(self,access_token,idx):
        self.idx = idx
        self.access_token = access_token

        self.data = self.get_data()
        self.splits = self.get_splits()
        
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
                     'average_speed':'Pace'})
        fig['layout']['yaxis']['autorange'] = "reversed"
        fig['layout']['xaxis']['showticklabels'] = False
        fig.update_traces(marker_color='green')
        return fig
    def make_map(self):
        mp = pd.DataFrame(polyline.decode(self.data['map']['polyline']))
        mp.columns = ['lat','long']
        fig = px.line_mapbox(mp,'lat','long',
                            mapbox_style = 'open-street-map',
                            zoom=13)
        return fig