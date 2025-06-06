import streamlit as st
from streamlit_folium import st_folium
import folium
from datetime import datetime
import requests
from math import radians, cos, sin, asin, sqrt
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")

# Geocoding direct
def geocode(address):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json"}
        headers = {
            "User-Agent": "TaxiFareApp/1.0 (contact@votresite.com)"
        }
        r = requests.get(url, params=params, headers=headers)
        r.raise_for_status()
        data = r.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return [lat, lon]
    except:
        return None

# Geocoding inverse
def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json"}
        headers = {
            "User-Agent": "TaxiFareApp/1.0 (contact@votresite.com)"
        }
        r = requests.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json().get("display_name", "")
    except:
        return ""

# Distance haversine
def distance_between_coords(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

# Zoom adaptatif
def get_zoom_level(distance_km):
    if distance_km < 1: return 15
    elif distance_km < 5: return 13
    elif distance_km < 20: return 12
    elif distance_km < 50: return 11
    elif distance_km < 100: return 10
    elif distance_km < 200: return 8
    elif distance_km < 500: return 7
    elif distance_km < 1000: return 6
    elif distance_km < 5000: return 4
    elif distance_km < 8000: return 3
    else: return 2

# Carte avec points
def create_map(pickup, dropoff):
    distance = distance_between_coords(pickup, dropoff)
    zoom = get_zoom_level(distance)
    center = [(pickup[0] + dropoff[0]) / 2, (pickup[1] + dropoff[1]) / 2]
    m = folium.Map(location=center, zoom_start=zoom, doubleClickZoom=False)
    folium.Marker(pickup, tooltip="Pickup", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(dropoff, tooltip="Dropoff", icon=folium.Icon(color="red")).add_to(m)
    folium.PolyLine([pickup, dropoff], color="blue", weight=3).add_to(m)
    return m

# Session init
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
if "pickup_address" not in st.session_state:
    st.session_state.pickup_address = "Empire State Building, NYC"
if "dropoff_address" not in st.session_state:
    st.session_state.dropoff_address = "Times Square, NYC"
if "user_time" not in st.session_state:
    st.session_state.user_time = datetime.now().time()

# Rafraîchissement auto
st_autorefresh(interval=1000, key="refresh")

# UI
col1, col2 = st.columns([1.2, 2.8], gap="large")

with col1:
    st.markdown("# 🚕 Taxi Fare Estimator")
    st.markdown("####")

    new_pickup_address = st.text_input("📍 Pickup address", st.session_state.pickup_address)
    if new_pickup_address != st.session_state.pickup_address:
        coords = geocode(new_pickup_address)
        if coords:
            st.session_state.pickup_coords = coords
        st.session_state.pickup_address = new_pickup_address

    new_dropoff_address = st.text_input("🏁 Dropoff address", st.session_state.dropoff_address)
    if new_dropoff_address != st.session_state.dropoff_address:
        coords = geocode(new_dropoff_address)
        if coords:
            st.session_state.dropoff_coords = coords
        st.session_state.dropoff_address = new_dropoff_address

    date = st.date_input("📅 Date", value=datetime.now().date(), min_value=datetime.now().date())
    time = st.time_input("⏰ Time", value=st.session_state.user_time)
    st.session_state.user_time = time

    passenger_count = st.number_input("👤 Passengers", min_value=1, max_value=4, value=1, step=1)

    if st.session_state.fare is not None:
        col_fare, col_map = st.columns([1, 1.3])
        with col_fare:
            st.success(f"Estimated fare: **${st.session_state.fare}**")

with col2:
    st.markdown("#### 🗺️ Double click on the map to set a point :")
    m = create_map(st.session_state.pickup_coords, st.session_state.dropoff_coords)
    map_data = st_folium(m, height=540, width="100%", key="map")

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        if st.session_state.click_step == 0:
            st.session_state.pickup_coords = [lat, lon]
            st.session_state.pickup_address = reverse_geocode(lat, lon)
            st.session_state.click_step = 1
        elif st.session_state.click_step == 1:
            st.session_state.dropoff_coords = [lat, lon]
            st.session_state.dropoff_address = reverse_geocode(lat, lon)
            st.session_state.click_step = 0

# Requête API si changement
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
        r = requests.get("https://taxifare.lewagon.ai/predict", params=params, timeout=8)
        r.raise_for_status()
        st.session_state.fare = round(r.json()["fare"], 2)
    except:
        st.error("❌ Problème lors du calcul du tarif.")
        st.session_state.fare = None
    st.session_state.last_inputs = current_inputs
