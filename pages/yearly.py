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
act_options = activities.sport_type.unique()
# default_type = activities.groupby('sport_type').distance.sum().sort_values().index[-1]
default_types =['Run','TrailRun']
act_list = st.multiselect('Activities',act_options, default = default_types)
filtered_activities = filter_activities(activities,act_list)
st.text(len(filtered_activities))
st.subheader('Yearly Distance')
st.plotly_chart(make_yearly_distance_plot(filtered_activities))