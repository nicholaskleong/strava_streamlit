import streamlit as st
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
    st.dataframe(activities)
    print(runs)
    st.dataframe(runs[['distance_km','moving_time','average_speed','min_km']])
    st.write('Text asdf')