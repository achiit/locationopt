
import streamlit as st
import os
import googlemaps
from geopy.geocoders import GoogleV3
import folium
from streamlit_folium import folium_static
from itertools import permutations
import streamlit.components.v1 as components
from dotenv import load_dotenv


load_dotenv()


API_KEY = st.write("API_KEY", st.secrets["GOOGLE_MAPS_API_KEY"])
gmaps = googlemaps.Client(key=API_KEY)
geolocator = GoogleV3(api_key=API_KEY)

def get_location_suggestions(query):
    if not query:
        return []
    results = gmaps.places_autocomplete(query, types='address')
    return [result['description'] for result in results]

def calculate_total_distance(route):
    total_distance = 0
    for i in range(len(route) - 1):
        result = gmaps.directions(route[i], route[i+1], mode="driving")
        if result:
            total_distance += result[0]['legs'][0]['distance']['value']
    return total_distance

def optimize_route(locations):
    if len(locations) <= 2:
        return locations

    possible_routes = list(permutations(locations[1:-1]))
    
    best_route = None
    min_distance = float('inf')

    for route in possible_routes:
        current_route = [locations[0]] + list(route) + [locations[-1]]
        distance = calculate_total_distance(current_route)
        if distance < min_distance:
            min_distance = distance
            best_route = current_route

    return best_route

def create_map(locations):
    coordinates = [geolocator.geocode(loc).point[:2] for loc in locations]
    m = folium.Map(location=coordinates[0], zoom_start=10)
    
    for i, coord in enumerate(coordinates):
        folium.Marker(
            coord,
            popup=locations[i],
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    folium.PolyLine(
        coordinates,
        weight=2,
        color='blue',
        opacity=0.8
    ).add_to(m)
    
    return m

def create_google_maps_link(locations):
    base_url = "https://www.google.com/maps/dir/?api=1"
    origin = f"&origin={locations[0].replace(' ', '+')}"
    destination = f"&destination={locations[-1].replace(' ', '+')}"
    waypoints = f"&waypoints={'+to:'.join([loc.replace(' ', '+') for loc in locations[1:-1]])}"
    return base_url + origin + destination + waypoints

st.title("Employee Drop Location Optimizer")

# Get device location
st.write("Fetching your current location...")
components.html(
    """
    <script>
    navigator.geolocation.getCurrentPosition(
        (position) => {
            document.getElementById('lat').textContent = position.coords.latitude;
            document.getElementById('lon').textContent = position.coords.longitude;
        },
        (error) => {
            document.getElementById('lat').textContent = 'Error';
            document.getElementById('lon').textContent = 'Error';
        }
    );
    </script>
    <p>Latitude: <span id="lat"></span></p>
    <p>Longitude: <span id="lon"></span></p>
    """,
    height=100,
)

# Current location input with real-time search
current_location = st.text_input("Current Location (or use device location)")
if current_location:
    suggestions = get_location_suggestions(current_location)
    if suggestions:
        current_location = st.selectbox("Select current location", suggestions, key="current_loc")

# Employee inputs with real-time search
employee_data = []
for i in range(5):
    st.subheader(f"Employee {i+1}")
    name = st.text_input(f"Employee {i+1} Name", key=f"name_{i}")
    location = st.text_input(f"Employee {i+1} Drop Location", key=f"location_{i}")
    if location:
        suggestions = get_location_suggestions(location)
        if suggestions:
            location = st.selectbox(f"Select location for Employee {i+1}", suggestions, key=f"select_{i}")
    employee_data.append((name, location))

if st.button("Optimize Route"):
    locations = [current_location] + [data[1] for data in employee_data if data[1]]
    if len(locations) < 2:
        st.error("Please enter at least one employee location in addition to the current location.")
    else:
        optimized_route = optimize_route(locations)
        
        st.subheader("Optimized Route:")
        for i, loc in enumerate(optimized_route):
            st.write(f"{i+1}. {loc}")
        
        st.subheader("Route Map:")
        map = create_map(optimized_route)
        folium_static(map)
        
        google_maps_link = create_google_maps_link(optimized_route)
        st.markdown(f"[Open in Google Maps]({google_maps_link})")