#This code was created with the help of ChatGPT
import csv
import time
import os
import streamlit as st
import pydeck as pdk
import pandas as pd
from opencage.geocoder import OpenCageGeocode

st.set_page_config(
    page_title="Flood Report System",
    page_icon="🌊",  # Optional: You can specify an icon here
    layout="wide",  # Optional: 'centered' or 'wide'
    initial_sidebar_state="expanded",  # Optional: 'collapsed', 'expanded'
)

with st.spinner('Processing your report...'):
    # Simulate some delay (like API call or image upload)
    time.sleep(2)
st.success('Your flood report has been successfully added!')


# Set up OpenCage Geocoder API
key = 'API Key Here'  # Replace with your OpenCage API key
geocoder = OpenCageGeocode(key)

# Function to read existing flood data from CSV
def read_flood_data():
    try:
        with open("flood_data.csv", mode="r") as file:
            reader = csv.DictReader(file)
            return [row for row in reader]
    except FileNotFoundError:
        return []  # Return an empty list if the file doesn't exist

# Function to save updated flood data to CSV
def save_flood_data(data):
    with open("flood_data.csv", mode="w", newline='') as file:
        fieldnames = ["lat", "lon", "address", "type", "severity", "image_path"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()  # Write header row
        writer.writerows(data)  # Write the rows of data

# Function to save the uploaded image to the 'flood_images/' directory
def save_image(image, image_name):
    # Ensure the 'flood_images' directory exists
    if not os.path.exists('flood_images'):
        os.makedirs('flood_images')
    
    # Define the path where the image will be saved
    image_path = os.path.join('flood_images', image_name)
    
    # Save the image to the defined path
    with open(image_path, "wb") as img_file:
        img_file.write(image.getbuffer())
    
    return image_path

# Geocode address to get latitude and longitude
def geocode_address(address):
    result = geocoder.geocode(address)
    if result:
        lat = result[0]['geometry']['lat']
        lon = result[0]['geometry']['lng']
        return lat, lon
    return None, None

# Sidebar form for reporting a flood
st.sidebar.header("Report a Flood")
with st.sidebar.form("flood_form"):
    street_address = st.text_input("Street Address")
    flood_type = st.selectbox("Cause of Flood", ["Storm Drain Blockage", "Well/Reservoir Overflow", "Pipe Burst", "Debris", "Other"])
    
    # Conditional text input for custom flood type
    if flood_type == "Other":
        custom_flood_type = st.text_input("Please specify the cause of flooding")
    else:
        custom_flood_type = flood_type  # Use selected flood type if it's not "Other"
    
    severity = st.slider("Flood Severity (1 = Minor, 5 = Severe)", min_value=1, max_value=5)
    
    # Image uploader
    flood_image = st.file_uploader("Upload an image of the flood", type=["jpg", "png", "jpeg"])
    
    submitted = st.form_submit_button("Submit Report")

# If a user submits a new report, save it to the CSV file
if submitted and street_address:
    # Geocode the address to get latitude and longitude
    lat, lon = geocode_address(street_address)
    
    if lat and lon:
        # If an image is uploaded, save it to the flood_images folder
        if flood_image:
            image_name = f"{street_address.replace(' ', '_')}_{flood_type}.jpg"  # Name the image based on address and flood type
            image_path = save_image(flood_image, image_name)  # Save the image and get the file path
        else:
            image_path = None  # No image uploaded
        
        # Create a new report with latitude, longitude, and other details
        new_report = {
            "lat": lat,
            "lon": lon,
            "address": street_address,
            "type": custom_flood_type,
            "severity": severity,
            "image_path": image_path  # Store the path to the image
        }
        
        # Append the new report to the existing data
        flood_data = read_flood_data()  # Get current data from the CSV
        flood_data.append(new_report)  # Add the new report
        
        # Save the updated data to the CSV file
        save_flood_data(flood_data)
        
        # Display a success message
        st.success(f"Flood report added for {street_address}. See it on the map below.")
        
        # Display the image if it was uploaded
        if flood_image:
            st.image(flood_image, caption="Uploaded Flood Image", use_container_width=True)
    else:
        st.error("Could not geocode the address. Please try again.")

# Load and display all flood data (including images) from the CSV
flood_data = read_flood_data()

# If there is any flood data, show the map
if flood_data:
    # Create DataFrame for pydeck map rendering
    df = pd.DataFrame(flood_data)
    
    # Convert the 'lat' and 'lon' columns to numeric types
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # Set fixed zoom level and initial view for the map (for consistency)
    initial_lat = df['lat'].mean() if len(df) > 0 else 37.7749  # Default latitude (San Francisco)
    initial_lon = df['lon'].mean() if len(df) > 0 else -122.4194  # Default longitude (San Francisco)
    
    # Set a wider zoom level for a more "wide" map (e.g., zoom=8)
    view = pdk.ViewState(latitude=initial_lat, longitude=initial_lon, zoom=10)  # Wider zoom level
    
    # Define a layer for the flood reports
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["lon", "lat"],
        get_radius=100,  # Adjust the radius for visibility
        get_fill_color=[255, 0, 0],  # Red color for flood markers
        pickable=True,  # Allows interaction with the markers
        radius_min_pixels=5
    )
    
    # Mapbox style for street map
    map_style = "mapbox://styles/mapbox/streets-v11"  # Street map style from Mapbox

    # Create the pydeck deck with the specified map style
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        map_style=map_style  # Set the street map style
    )
    
    # Render the map in Streamlit
    st.pydeck_chart(deck)

# Display the flood reports in a user-friendly format
if flood_data:
    st.header("Flood Reports")
    
    # Create a table to display the reports
    for report in flood_data:
        with st.expander(f"Details for {report['address']}"):  # Make each report expandable
            st.subheader(f"Address: {report['address']}")
            st.write(f"Flood Type: {report['type']}")
            st.write(f"Severity: {report['severity']}/5")
            
            # Display image if available
            if report["image_path"]:
                st.image(report["image_path"], caption="Flood Image", use_container_width=True)
            
            st.write("----")

else:
    st.info("No flood reports available.")
