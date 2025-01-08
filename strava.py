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
    activites_url = f'{BASE_URL}/api/v3/athlete/activities'
    df_list = []
    for page in range(1,20):
        my_dataset = requests.get(activites_url, headers=header, params={'per_page': 200, 'page': page}).json()
        print(f'Retrieved {len(my_dataset)} activities on page {page}')
        if not len(my_dataset):
            print('escaping because no more activites')
            break
        activities = pd.json_normalize(my_dataset)
        df_list.append(activities)
    activities = pd.concat(df_list)
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
def filter_activities(activities,act_list):
    cols = ['id','name','start_date','distance_km','moving_time','elapsed_time','average_speed','sport_type']
    runs = activities[activities.sport_type.isin(act_list)][cols]
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
    return activities

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

def make_weekly_distance_plot(runs):
    # df = runs.distance_km.resample('W').sum()
    # fig = px.line(df,y='distance_km',text='distance_km')
    # fig.update_traces(texttemplate="%{y:0.0f}")
    # fig.update_traces(textposition='top center')
    # fig.update_traces(hovertemplate='%{x}<br>%{y:0.1f}km')
    df = runs
    df['week_start'] =( df.index - pd.to_timedelta(df.index.dayofweek, unit='days')).date
    df['run'] = df.groupby(pd.Grouper(freq='W')).cumcount() + 1

    weekly_totals = df.groupby('week_start')['distance_km'].sum()

    # Create a stacked bar chart
    fig = px.bar(df, x='week_start', y='distance_km', color='run',hover_name='name',
                title='Total Distance by Week',
                labels={'week': 'Week', 'distance_km': 'Total Distance (km)', 'label': 'Run'},
                color_continuous_scale='Viridis',
                barmode='stack',  # Use 'group' mode for stacked bars
                )

    for week, total in weekly_totals.items():
        fig.add_annotation(
            x=week, 
            y=total, 
            text=f'{total:.0f}', 
            showarrow=False, 
    #         arrowhead=1, 
            yshift=10  # Adjust yshift for annotation placement
        )
    fig.update_layout(
        coloraxis_colorbar=dict(
            tickvals=list(range(min(df['run']), max(df['run']) + 1)), 
            ticktext=list(map(str, range(min(df['run']), max(df['run']) + 1)))
        )
    )
    return fig
def make_yearly_distance_plot(runs):
    df = runs.distance_km.resample('Y').sum()
    fig = px.line(df,y='distance_km',text='distance_km')
    fig.update_traces(texttemplate="%{y:0.0f}")
    fig.update_traces(textposition='top center')
    fig.update_traces(hovertemplate='%{x:%Y}<br>%{y:0.1f}km')
    return fig

def recent_runs(runs):
    n = 10
    display_df = runs.iloc[-n:]
    display_df = display_df.reset_index(drop=False)
    col_map = {'start_date':'Date','name':'Name','distance_km':'Distance','min_km':'Pace','elapsed_time':'Time'}
    display_df = display_df[[col for col in col_map.keys()]]
    display_df = display_df.rename(col_map,axis=1)
    display_df['Date'] = display_df.Date.dt.strftime('%d-%m-%Y')
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
    
class Heatplot(object):
    def __init__(self,df,n_weeks,end_date = datetime.today()):
        tz = pytz.timezone('Australia/Sydney')
        self.n_weeks=min(n_weeks,(datetime.today()-datetime(datetime.today().year,1,1)).days//7 +1)
        
        if end_date:
            self.end_date =end_date.replace(tzinfo=tz)
        else:
            self.end_date = datetime.today().replace(tzinfo=tz)
        self.start_date = self._get_start_date()
        self.df = df = df.loc[self.start_date:self.end_date].copy()
        self.augment_df()        
        self.dist = self.make_array('distance_km')
        self.time = self.make_array('time',' hrs')
        self.pace = self.make_array('min_km',' min/km')
        self.yticks = self.make_yticks()
        self.text = self.make_text()
        
    
    def _get_start_date(self):
        start_date = (self.end_date-timedelta(7*(self.n_weeks-1))).replace(tzinfo=tz)
        start_date = start_date - timedelta(start_date.weekday() if start_date.weekday()!=0 else 7)
        return start_date
    
    def augment_df(self):
        self.df['min_km'] = self.df.average_speed.apply(calculate_km_interval)
        self.df['time'] = self.df.moving_time.apply(lambda x: ':'.join(str(timedelta(seconds=x)).split(':')[-3:-1]))
        self.df['y'] = self.df.index.isocalendar().week
        self.df['x']= self.df.index.isocalendar().day
    
    def make_array(self,data_col,suffix=False):
        last_row = self.end_date.isocalendar().week if self.end_date.weekday()!=0 else self.end_date.isocalendar().week-1
        size = (last_row,7)
        if suffix:
            arr = np.full(size,'',dtype=object)
        else:
            arr = np.zeros(size)
        for i,row in self.df.iterrows():
            arr[(row.y-1,row.x-1)] = row[data_col]
            if suffix:
                arr[(row.y-1,row.x-1)] += suffix
        arr = arr[-self.n_weeks:]
        return arr
    def make_yticks(self):
        yticks = list(pd.date_range(self.start_date,periods=self.n_weeks,freq='W-Mon').strftime('%d-%b-%Y'))
        return yticks
    def join_str_arrays(self,arr1,arr2,arr1_suffix=''):
        if arr1.dtype =='float64':
            arr = arr1.round(2).astype(str).copy()
        else:
            arr = arr1.astype(str).copy()
        for idx, val in np.ndenumerate(arr):
            arr[idx]=str(arr[idx])+arr1_suffix+f'\n{arr2[idx]}'
        return arr
    def make_text(self):
        text = self.join_str_arrays(self.dist,self.time,' km')
        text = self.join_str_arrays(text,self.pace)
        return text
    def make_heatmap(self):
        sz = 18
        ar = 0.6
        fig, ax = plt.subplots(1,1,figsize=(10,self.n_weeks*0.65))
        im = ax.imshow(self.dist, cmap='BuGn',aspect=.6)

        # Add values to each cell
        for i in range(self.text.shape[0]):
            for j in range(self.text.shape[1]):
                texta = ax.text(j, i, self.text[i, j],
                        ha="center", va="center", color="black",fontdict={'size' : 7})

        # Add a label to the colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("Distance(km)", rotation=-90, va="bottom")
        # Show the plot
        plt.xticks(list(range(7)),week)
        ax.xaxis.tick_top()
        plt.yticks(list(range(len(self.yticks))),self.yticks)
        return fig,ax