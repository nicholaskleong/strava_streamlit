import streamlit as st
import os

from strava import *
import strava_auth
st. set_page_config(layout="wide")
if 'access_token' not in st.session_state:
    strava_auth.login_header()
    strava_auth.authenticate()

access_token = st.session_state['access_token']
activities = init_data(access_token)
act_list = st.multiselect('Activities',activities.sport_type.unique(), default = ['Run','TrailRun'])
filtered_activities = filter_activities(activities,act_list)

st.subheader('Yearly Distance')
st.plotly_chart(make_yearly_distance_plot(filtered_activities))