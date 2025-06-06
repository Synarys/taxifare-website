import streamlit as st
import pandas as pd
from datetime import datetime
import requests


'# 🚕 TaxiFareModel'


# Initialisation une seule fois
if "init_now" not in st.session_state:
    st.session_state.init_now = datetime.now()

'### ⏰ When ?'
# Date
date = st.date_input('When do you need a ride ?',st.session_state.init_now.date(), min_value=st.session_state.init_now.date())

# Time
time = st.time_input('What time is your ride ?', st.session_state.init_now.time())

'### 📍 Where ?'
col1, col2 = st.columns(2)

# Pickup longitude
with col1:
    pickup_longitude = st.number_input('Insert the pickup longitude (-74.02 to -73.92) :', format='%.5f', min_value=-74.02, max_value=-73.92, step=.001)

# Pickup latitude
with col2:
    pickup_latitude = st.number_input('Insert the pickup latitude (40.70 to 40.88) :', format='%.5f', min_value=40.70, max_value=40.88,step=.001)

# Pickup longitude
with col1:
    dropoff_longitude = st.number_input('Insert the dropoff longitude (-74.02 to -73.92) :', format='%.5f', min_value=-74.02, max_value=-73.92, step=.001)

# Pickup latitude
with col2:
    dropoff_latitude = st.number_input('Insert the dropoff latitude (40.70 to 40.88) :', format='%.5f', min_value=40.70, max_value=40.88,step=.001)

'### 🧍 How many ?'
# Passenge Count
passenger_count = st.number_input('How many will there be?', format='%d', min_value=1, max_value=4, value=1, step=1)

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

'### 🗺️ Your travel :'
map_data = pd.DataFrame({'lat': [pickup_latitude, dropoff_latitude], 'lon': [pickup_longitude, dropoff_longitude]})
st.map(map_data)
