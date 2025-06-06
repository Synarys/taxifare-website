import streamlit as st
from streamlit_folium import st_folium
import folium
from datetime import datetime
import requests
from math import radians, cos, sin, asin, sqrt

st.set_page_config(layout="wide")

def geocode(address):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json"}
        headers = {"User-Agent": "streamlit-app"}
        r = requests.get(url, params=params, headers=headers)
        r.raise_for_status()
        data = r.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return [lat, lon]
    except:
        return None

def distance_between_coords(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def get_zoom_level(distance_km):
    if distance_km < 1:
        return 15
    elif distance_km < 5:
        return 13
    elif distance_km < 20:
        return 12
    elif distance_km < 50:
        return 11
    elif distance_km < 100:
        return 10
    elif distance_km < 200:
        return 8
    elif distance_km < 500:
        return 7
    elif distance_km < 1000:
        return 6
    elif distance_km < 5000:
        return 4
    elif distance_km < 8000:
        return 3
    else:
        return 2

def create_map(pickup, dropoff):
    distance = distance_between_coords(pickup, dropoff)
    zoom = get_zoom_level(distance)
    center = [(pickup[0] + dropoff[0]) / 2, (pickup[1] + dropoff[1]) / 2]

    m = folium.Map(location=center, zoom_start=zoom, doubleClickZoom=False)  # <-- ici
    folium.Marker(pickup, tooltip="Pickup", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(dropoff, tooltip="Dropoff", icon=folium.Icon(color="red")).add_to(m)
    folium.PolyLine([pickup, dropoff], color="blue", weight=3).add_to(m)
    return m

# Init session state
if "pickup_coords" not in st.session_state:
    st.session_state.pickup_coords = [40.75, -73.98]
if "dropoff_coords" not in st.session_state:
    st.session_state.dropoff_coords = [40.76, -73.97]
if "click_step" not in st.session_state:
    st.session_state.click_step = 0
if "fare" not in st.session_state:
    st.session_state.fare = None
if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = {}

if "current_time" not in st.session_state:
    st.session_state.current_time = datetime.now().time()
if "last_checked_date" not in st.session_state or st.session_state.last_checked_date != datetime.now().date():
    st.session_state.current_time = datetime.now().time()
    st.session_state.last_checked_date = datetime.now().date()

# Layout
col1, col2 = st.columns([1.2, 2.8], gap="large")

with col1:
    st.markdown("# 🚕 Taxi Fare Estimator")
    st.markdown("####")
    pickup_address = st.text_input("📍 Pickup address", "Empire State Building, NYC")
    dropoff_address = st.text_input("🏁 Dropoff address", "Times Square, NYC")

    if st.button("📌 Set the addresses"):
        pickup = geocode(pickup_address)
        dropoff = geocode(dropoff_address)
        if pickup and dropoff:
            st.session_state.pickup_coords = pickup
            st.session_state.dropoff_coords = dropoff
            st.session_state.click_step = 0
        else:
            st.warning("❌ Adresse introuvable.")
    st.markdown("####")
    date = st.date_input("📅 Date", value=datetime.now().date(), min_value=datetime.now().date())
    time = st.time_input("⏰ Time", value=st.session_state.current_time)
    passenger_count = st.number_input("👤 Passengers", min_value=1, max_value=4, value=1, step=1)

with col2:
    st.markdown("#### 🗺️ Double click on the map to set a point :")
    m = create_map(st.session_state.pickup_coords, st.session_state.dropoff_coords)
    map_data = st_folium(m, height=500, width="100%", key="map")

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        if st.session_state.click_step == 0:
            st.session_state.pickup_coords = [lat, lon]
            st.session_state.click_step = 1
        elif st.session_state.click_step == 1:
            st.session_state.dropoff_coords = [lat, lon]
            st.session_state.click_step = 0

    # Résultat affiché sous la carte dans une colonne plus petite
    if st.session_state.fare is not None:
        col_fare, col_map = st.columns([1, 4])  # rétrécit la zone d'affichage
        with col_fare:
            st.success(f"💰 Estimated fare: **${st.session_state.fare}**")

# Détection de changement des inputs
current_inputs = {
    "pickup": st.session_state.pickup_coords,
    "dropoff": st.session_state.dropoff_coords,
    "date": date,
    "time": time,
    "passenger": passenger_count
}

if current_inputs != st.session_state.last_inputs:
    dt = datetime.combine(date, time)
    params = {
            "pickup_datetime": dt.isoformat(),
            "pickup_longitude": st.session_state.pickup_coords[1],
            "pickup_latitude": st.session_state.pickup_coords[0],
            "dropoff_longitude": st.session_state.dropoff_coords[1],
            "dropoff_latitude": st.session_state.dropoff_coords[0],
            "passenger_count": passenger_count
        }

    try:
        response = requests.get("https://taxifare.lewagon.ai/predict", params=params, timeout=8)
        response.raise_for_status()
        st.session_state.fare = round(response.json()["fare"], 2)
    except:
        st.error("❌ Problème lors du calcul du tarif.")
        st.session_state.fare = None

    st.session_state.last_inputs = current_inputs
