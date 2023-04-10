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

#Metrics

col1, col2, col3,col4 = st.columns(4)
col1.plotly_chart(make_number(activites_per_week(runs),"Runs per Week",''),use_container_width=True)
col2.plotly_chart(make_number(distance_this_year(runs),"Distance this Year",'km'),use_container_width=True)
col3.plotly_chart(make_gauge(distance_this_month(runs),100,f"Distance {datetime.today().strftime('%B')}",'km'),use_container_width=True)
col4.plotly_chart(make_gauge(distance_last_week(runs),25,f"Distance last 7 Days",'km'),use_container_width=True)


#Heatmap
start_date,end_date = datetime.today()-timedelta(days=42),datetime.today()
dist,text,yticks = make_plot_data(runs,datetime.today().replace(tzinfo=tz)-timedelta(days=49),datetime.today().replace(tzinfo=tz))
fig,ax = make_heatmap(dist,text,yticks)
st.pyplot(fig)

#Weekly Distance
st.subheader('2023 Weekly Distance')
# start_date = st.date_input('Start Date',value = datetime(2023,1,1))
# weekly = runs.loc[start_date:]['distance_km'].resample('W').sum()
# st.line_chart(weekly,y='distance_km')
st.plotly_chart(make_weekly_distance_plot(runs.loc[datetime(2023,1,1,tzinfo=tz):]))

st.subheader('Recent Runs')
st.dataframe(recent_runs(runs), )