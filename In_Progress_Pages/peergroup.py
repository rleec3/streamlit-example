import streamlit as st
import requests
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Initialize the Geopy geolocator
geolocator = Nominatim(user_agent="nonprofit_explorer")

BASE_URL = 'https://990-infrastructure.gtdata.org/irs-data/990basic120fields'

def fetch_nonprofit_data(ein):
    params = {'ein': ein}
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch data from the GTDC API: {response.status_code} - {response.text}")
        return None

def get_coordinates(location):
    location = geolocator.geocode(location)
    if location:
        return (location.latitude, location.longitude)
    return None

def filter_and_group_data(data, filters):
    df = pd.DataFrame(data)
    
    if 'location' in filters and 'miles' in filters:
        location_coords = get_coordinates(filters['location'])
        if location_coords:
            def within_miles(row):
                row_coords = (row['latitude'], row['longitude'])
                return geodesic(location_coords, row_coords).miles <= filters['miles']
            df = df[df.apply(within_miles, axis=1)]
    
    if 'min_assets' in filters:
        df = df[df['assets'] >= filters['min_assets']]
    if 'max_assets' in filters:
        df = df[df['assets'] <= filters['max_assets']]
    if 'min_revenue' in filters:
        df = df[df['revenue'] >= filters['min_revenue']]
    if 'max_revenue' in filters:
        df = df[df['revenue'] <= filters['max_revenue']]
    if 'min_employees' in filters:
        df = df[df['employees'] >= filters['min_employees']]
    if 'max_employees' in filters:
        df = df[df['employees'] <= filters['max_employees']]
    if 'min_expenses' in filters:
        df = df[df['expenses'] >= filters['min_expenses']]
    if 'max_expenses' in filters:
        df = df[df['expenses'] <= filters['max_expenses']]
    if 'state' in filters:
        df = df[df['FILERUSSTATE'] == filters['state']]
    if 'city' in filters:
        df = df[df['FILERUSCITY'].str.contains(filters['city'], case=False, na=False)]
    if 'zip' in filters:
        df = df[df['FILERUSZIP'].str.startswith(filters['zip'])]
    
    peer_groups = df.groupby(['FILERUSCITY', 'FILERUSSTATE']).apply(lambda x: x.to_dict(orient='records')).to_dict()
    
    return df, peer_groups

st.title("Nonprofit Peer Group Finder")
st.sidebar.header("Filter Options")

include_ein = st.sidebar.checkbox("Include EIN")
if include_ein:
    ein_filter = st.sidebar.text_input("Enter EIN")

include_state = st.sidebar.checkbox("Include State")
if include_state:
    state_filter = st.sidebar.text_input("State (two-letter code, e.g., NY)")

include_city = st.sidebar.checkbox("Include City")
if include_city:
    city_filter = st.sidebar.text_input("City")

include_zip = st.sidebar.checkbox("Include Zip Code")
if include_zip:
    zip_filter = st.sidebar.text_input("Zip Code")

include_miles = st.sidebar.checkbox("Include Miles from location")
if include_miles:
    miles_filter = st.sidebar.number_input("Miles from location", min_value=0, step=1)

include_employees = st.sidebar.checkbox("Include Employee Range")
if include_employees:
    min_employees = st.sidebar.number_input("Min Employees", min_value=0, step=1)
    max_employees = st.sidebar.number_input("Max Employees", min_value=0, step=1)

include_assets = st.sidebar.checkbox("Include Asset Range")
if include_assets:
    min_assets = st.sidebar.number_input("Min Assets", min_value=0, step=1000)
    max_assets = st.sidebar.number_input("Max Assets", min_value=0, step=1000)

include_expenses = st.sidebar.checkbox("Include Expense Range")
if include_expenses:
    min_expenses = st.sidebar.number_input("Min Expenses", min_value=0, step=1000)
    max_expenses = st.sidebar.number_input("Max Expenses", min_value=0, step=1000)

include_revenue = st.sidebar.checkbox("Include Revenue Range")
if include_revenue:
    min_revenue = st.sidebar.number_input("Min Revenue", min_value=0, step=1000)
    max_revenue = st.sidebar.number_input("Max Revenue", min_value=0, step=1000)

if st.sidebar.button("Search"):
    filters = {}
    
    if include_miles:
        filters['miles'] = miles_filter
    if include_employees:
        filters['min_employees'] = min_employees
        filters['max_employees'] = max_employees
    if include_assets:
        filters['min_assets'] = min_assets
        filters['max_assets'] = max_assets
    if include_expenses:
        filters['min_expenses'] = min_expenses
        filters['max_expenses'] = max_expenses
    if include_revenue:
        filters['min_revenue'] = min_revenue
        filters['max_revenue'] = max_revenue

    if include_state:
        filters['state'] = state_filter
    if include_city:
        filters['city'] = city_filter
    if include_zip:
        filters['zip'] = zip_filter

    ein = ein_filter if include_ein else None

    if ein:
        data = fetch_nonprofit_data(ein=ein)
    
        if data:
            df, peer_groups = filter_and_group_data(data, filters)
            
            st.write("Filtered Nonprofit Data:")
            st.write(df)
            
            st.write("Peer Groups:")
            for key, group in peer_groups.items():
                st.write(f"Location: {key}")
                st.write(group)
        else:
            st.error("No data found")
    else:
        st.error("Please provide an EIN to search.")
