import streamlit as st
import os

from strava import *
import strava_auth
st. set_page_config(layout="wide")
if 'access_token' not in st.session_state:
    strava_auth.login_header()
    strava_auth.authenticate()
access_token = st.session_state['access_token']
# init_data(access_token)
filtered_activities = st.session_state['filtered_activities']


run_select= st.selectbox('Select run to display detailed data',
            options = filtered_activities.label.iloc[::-1],
            format_func = lambda x: x.split(' - ')[1])
print(run_select)
idx = run_select.split(' - ')[0]
col1,col2 = st.columns([1.3,2])
run = Run(access_token,idx)

col1.subheader('Kilometre Pace')
col1.plotly_chart(run.make_split_plot())
col2.subheader('Map')
col2.plotly_chart(run.make_map())

st.plotly_chart(run.make_analysis_plot())