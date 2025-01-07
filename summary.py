import streamlit as st
from datetime import datetime
import os

from strava import *
import strava_auth
st. set_page_config(page_title='Summary',layout="wide")



st.header("Strava data explorer")
if 'access_token' not in st.session_state:
    strava_auth.login_header()
    strava_auth.authenticate()


access_token = st.session_state['access_token']
activities = init_data(access_token)
act_options = activities.sport_type.unique()
default_types = [activities.groupby('sport_type').distance.sum().sort_values().index[-1]]
default_types =['Run','Trail Run']
act_list = st.multiselect('Activities',act_options, default = default_types)
filtered_activities = filter_activities(activities,act_list)
st.session_state['filtered_activities'] = filtered_activities
#Metrics

col1, col2, col3,col4 = st.columns(4)
col1.plotly_chart(make_number(activites_per_week(filtered_activities),"Runs per Week",''),use_container_width=True)
col2.plotly_chart(make_number(distance_this_year(filtered_activities),"Distance this Year",'km'),use_container_width=True)
col3.plotly_chart(make_gauge(distance_this_month(filtered_activities),100,f"Distance {datetime.today().strftime('%B')}",'km'),use_container_width=True)
col4.plotly_chart(make_gauge(distance_last_week(filtered_activities),40,f"Distance last 7 Days",'km'),use_container_width=True)


#Heatmap
hm = Heatplot(filtered_activities,n_weeks=8)
fig,ax = hm.make_heatmap()
st.pyplot(fig,use_container_width=True)

#Weekly Distance
st.subheader('2023 Weekly Distance')
# start_date = st.date_input('Start Date',value = datetime(2023,1,1))
# weekly = runs.loc[start_date:]['distance_km'].resample('W').sum()
# st.line_chart(weekly,y='distance_km')
st.plotly_chart(make_weekly_distance_plot(filtered_activities.loc[datetime(2023,1,1,tzinfo=tz):]))

st.subheader('Recent Runs')
st.dataframe(recent_runs(filtered_activities), )
