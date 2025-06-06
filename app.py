import streamlit as st
from datetime import datetime
import requests

'''
# TaxiFareModel front
'''

# Initialisation une seule fois
if "init_now" not in st.session_state:
    st.session_state.init_now = datetime.now()

# Date
st.markdown('### When ?')
date = st.date_input('When do you need a ride ?',st.session_state.init_now.date(), min_value=st.session_state.init_now.date())

# Time
time = st.time_input('What time is your ride ?', st.session_state.init_now.time())

# Pickup longitude
st.markdown('### Where ?')
pickup_longitude = st.number_input('Insert the longitude where you need to be pickup', format='%.6f', step=.000001)

# Pickup latitude
pickup_latitude = st.number_input('Insert the latitude where you need to be pickup', format='%.6f', step=.000001)

# Pickup longitude
dropoff_longitude = st.number_input('Insert the longitude where you need to be dropoff', format='%.6f', step=.000001)

# Pickup latitude
dropoff_latitude = st.number_input('Insert the latitude where you need to be dropoff', format='%.6f', step=.000001)

# Passenge Count
st.markdown('### How many ?')
passenger_count = st.number_input('How many will there be?', format='%d', min_value=1, value=1, step=1)

# API call

url = 'https://taxifare.lewagon.ai/predict'
params ={
    "pickup_datetime": datetime.combine(date, time),
    "pickup_longitude": pickup_longitude,
    "pickup_latitude": pickup_latitude,
    "dropoff_longitude": dropoff_longitude,
    "dropoff_latitude": dropoff_latitude,
    "passenger_count": passenger_count
}

if st.button('Estimate fare'):
    response = requests.get(url, params=params)
    if response.status_code == 200:
        result = response.json()
        st.write("Estimated fare :", f'${round(result['fare'], 2)}')
    else:
        st.error(f"Erreur {response.status_code}")
