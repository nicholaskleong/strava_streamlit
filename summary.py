import streamlit as st
from datetime import datetime
import os

from strava import *
st. set_page_config(page_title='Summary',layout="wide")

st.header("Strava data explorer")
access_token = get_access_token(os.environ["client_id"],os.environ["client_secret"],os.environ["refresh_token"])
activities = get_activities(access_token)
activities = clean_activities(activities)
runs = make_runs(activities)
# write to state
st.session_state['runs'] = runs

st.dataframe(runs)
st.subheader('Weekly Distance')
# start_date = st.date_input('Start Date',value = datetime(2023,1,1))
weekly = runs['distance_km'].resample('W').sum()
st.line_chart(weekly,y='distance_km')

run_select= st.selectbox('Select run to display detailed data',
            options = runs.label,
            format_func = lambda x: x.split(' - ')[1])
print(run_select)
idx = run_select.split(' - ')[0]
col1,col2 = st.columns(2)
run = Run(access_token,idx)
col1.subheader('Kilometre Pace')
col1.plotly_chart(run.make_split_plot())
col2.subheader('Map')
col2.plotly_chart(run.make_map())