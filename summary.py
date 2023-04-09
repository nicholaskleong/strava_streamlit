import streamlit as st
from datetime import datetime
import os

from strava import *
st. set_page_config(page_title='Summary',layout="wide")

st.header("Strava data explorer")
if 'access_token' not in st.session_state:
    init_data()
access_token = st.session_state['access_token']
runs = st.session_state['runs']

start_date,end_date = datetime.today()-timedelta(days=42),datetime.today()
dist,text,yticks = make_plot_data(runs,datetime.today()-timedelta(days=49),datetime.today())
fig,ax = make_heatmap(dist,text,yticks)
st.pyplot(fig)

st.subheader('2023 Weekly Distance')
# start_date = st.date_input('Start Date',value = datetime(2023,1,1))
# weekly = runs.loc[start_date:]['distance_km'].resample('W').sum()
# st.line_chart(weekly,y='distance_km')
st.plotly_chart(make_weekly_distance_plot(runs.loc[datetime(2023,1,1):]))