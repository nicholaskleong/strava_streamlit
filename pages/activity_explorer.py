import streamlit as st
import os
from datetime import datetime
import pandas as pd  # Import pandas for date handling

from strava import *
import strava_auth

st.set_page_config(layout="wide")

if 'access_token' not in st.session_state:
    strava_auth.login_header()
    strava_auth.authenticate()

access_token = st.session_state['access_token']
activities = init_data(access_token)


# Filters
col1, col2, col3 = st.columns(3)


with col1:
    act_options = activities.sport_type.unique()
    default_types = ['Run', 'TrailRun']
    act_list = st.multiselect('Activities', act_options, default=default_types)
    # Apply Filters
    filtered_activities = filter_activities(activities, act_list)

with col2:
    min_distance = st.number_input("Min Distance (km)", min_value=0.0, value=0.0)
    max_distance = st.number_input("Max Distance (km)", min_value=0.0, value=filtered_activities['distance_km'].max())  # Dynamic max

with col3:
    min_date = st.date_input("Start Date", value=filtered_activities.index.min())  # Dynamic min
    max_date = st.date_input("End Date", value=datetime.now().date())  # Dynamic max



filtered_activities = filtered_activities[
    (filtered_activities['distance_km'] >= min_distance) &
    (filtered_activities['distance_km'] <= max_distance) &
    (filtered_activities.index.date >= min_date) &  # Access index directly
    (filtered_activities.index.date <= max_date)
]
filtered_activities = filtered_activities.reset_index()
display_df = filtered_activities
col_map = {'start_date':'Date','name':'Name','distance_km':'Distance','min_km':'Pace','elapsed_time':'Time'}
display_df = display_df[[col for col in col_map.keys()]]
display_df = display_df.rename(col_map,axis=1)
display_df = display_df.sort_values('Date',ascending=False)
display_df['Date'] = display_df.Date.dt.strftime('%d-%b-%Y')
display_df['Time'] = display_df.Time.apply(format_seconds)


st.text(f"Number of filtered activities: {len(filtered_activities)}") #More informative text
st.subheader('Fiiltered Activities')

if not filtered_activities.empty: #Check if the df is empty
    st.dataframe(display_df,hide_index=True )

else:
    st.write("No activities match the selected filters.") # Inform the User