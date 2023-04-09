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

st.dataframe(runs)
st.subheader('Weekly Distance')
# start_date = st.date_input('Start Date',value = datetime(2023,1,1))
weekly = runs['distance_km'].resample('W').sum()
st.line_chart(weekly,y='distance_km')