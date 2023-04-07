import streamlit as st
from datetime import datetime
import os

from strava import *

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
# if True:
    st.header("Strava data explorer")
    access_token = get_access_token(os.environ["client_id"],os.environ["client_secret"],os.environ["refresh_token"])
    activities = get_activities(access_token)
    activities = clean_activities(activities)
    runs = make_runs(activities)

    st.dataframe(runs)
    st.subheader('Weekly Distance')
    start_date = st.date_input('Start Date',value = datetime(2023,1,1))
    weekly = runs.loc[start_date:]['distance_km'].resample('W').sum()
    st.line_chart(weekly,y='distance_km')

    idx = st.selectbox('Select run to display detailed data',
                 options = runs)
    # idx = 8731733215

    run = Run(access_token,idx)
    st.plotly_chart(run.make_split_plot())