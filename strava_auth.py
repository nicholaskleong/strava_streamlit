import base64
import os
import httpx
import streamlit as st

APP_URL = st.secrets['app_url']
STRAVA_CLIENT_ID = st.secrets['strava']['client_id']
STRAVA_CLIENT_SECRET = st.secrets['strava']['client_secret']
STRAVA_AUTHORIZATION_URL = "https://www.strava.com/oauth/authorize"
STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"
DEFAULT_ACTIVITY_LABEL = "NO_ACTIVITY_SELECTED"
STRAVA_ORANGE = "#fc4c02"

@st.cache_data(show_spinner=False)
def load_image_as_base64(image_path):
    with open(image_path, "rb") as f:
        contents = f.read()
    return base64.b64encode(contents).decode("utf-8")

def authorization_url():
    request = httpx.Request(
        method="GET",
        url=STRAVA_AUTHORIZATION_URL,
        params={
            "client_id": STRAVA_CLIENT_ID,
            "redirect_uri": APP_URL,
            "response_type": "code",
            "approval_prompt": "auto",
            "scope": "activity:read_all"
        }
    )

    return request.url

def login_header(header=None):
    strava_authorization_url = authorization_url()

    if header is None:
        base = st
    else:
        col1, _, _, button = header
        base = button

    base64_image = load_image_as_base64("./static/connect_strava.png")
    base.markdown(
        (
            f"<a href=\"{strava_authorization_url}\" target=\"_self\">"
            f"  <img alt=\"strava login\"  src=\"data:image/png;base64,{base64_image}\" width=\"10%\">"
            f"</a>"
        ),
        unsafe_allow_html=True,
    )
@st.cache_data(show_spinner=False)
def exchange_authorization_code(authorization_code):
    response = httpx.post(
        url="https://www.strava.com/oauth/token",
        json={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "code": authorization_code,
            "grant_type": "authorization_code",
        }
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        # st.error("Something went wrong while authenticating with Strava. Please reload and try again")
        st.experimental_set_query_params()
        st.stop()
        return

    strava_auth = response.json()

    return strava_auth

def authenticate():
    query_params = st.experimental_get_query_params()
    authorization_code = query_params.get("code", [None])[0]

    if authorization_code is None:
        authorization_code = query_params.get("session", [None])[0]

    if authorization_code is None:
        st.stop()
        return
    else:
        # logout_header(header=header)
        strava_auth = exchange_authorization_code(authorization_code)
        # logged_in_title(strava_auth, header)
        st.experimental_set_query_params(session=authorization_code)

        st.session_state['access_token'] = strava_auth['access_token']