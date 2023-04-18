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
act_list = st.multiselect('Activities',activities.sport_type.unique(), default = activities.sport_type.unique()[:3])
filtered_activities = filter_activities(activities,act_list)
st.session_state['filtered_activities'] = filtered_activities
#Metrics

col1, col2, col3,col4 = st.columns(4)
col1.plotly_chart(make_number(activites_per_week(filtered_activities),"Runs per Week",''),use_container_width=True)
col2.plotly_chart(make_number(distance_this_year(filtered_activities),"Distance this Year",'km'),use_container_width=True)
col3.plotly_chart(make_gauge(distance_this_month(filtered_activities),100,f"Distance {datetime.today().strftime('%B')}",'km'),use_container_width=True)
col4.plotly_chart(make_gauge(distance_last_week(filtered_activities),25,f"Distance last 7 Days",'km'),use_container_width=True)


#Heatmap
start_date,end_date = datetime.today()-timedelta(days=42),datetime.today()
dist,text,yticks = make_plot_data(filtered_activities,datetime.today().replace(tzinfo=tz)-timedelta(days=49),datetime.today().replace(tzinfo=tz))
fig,ax = make_heatmap(dist,text,yticks)
st.pyplot(fig)

#Weekly Distance
st.subheader('2023 Weekly Distance')
# start_date = st.date_input('Start Date',value = datetime(2023,1,1))
# weekly = runs.loc[start_date:]['distance_km'].resample('W').sum()
# st.line_chart(weekly,y='distance_km')
st.plotly_chart(make_weekly_distance_plot(filtered_activities.loc[datetime(2023,1,1,tzinfo=tz):]))

st.subheader('Recent Runs')
st.dataframe(recent_runs(filtered_activities), )
