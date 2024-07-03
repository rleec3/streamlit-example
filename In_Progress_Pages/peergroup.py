import streamlit as st
import requests
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Initialize the Hugging Face model
model_name = "google/flan-t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Initialize the Geopy geolocator
geolocator = Nominatim(user_agent="nonprofit_explorer")

BASE_URL = 'https://projects.propublica.org/nonprofits/api/v2/search.json'

def fetch_nonprofit_data(query=None, state=None, ntee=None, c_code=None, page=0):
    params = {'page': page}
    if query:
        params['q'] = query
    if state:
        params['state[id]'] = state
    if ntee:
        params['ntee[id]'] = ntee
    if c_code:
        params['c_code[id]'] = c_code
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch data from ProPublica")
        return None

def parse_user_input(user_input):
    inputs = tokenizer(user_input, return_tensors="pt")
    outputs = model.generate(inputs.input_ids, max_length=50)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Basic parsing logic (you can expand this)
    filters = {}
    if "location" in user_input:
        filters['location'] = user_input.split("location")[1].strip()
    if "asset size" in user_input:
        size_range = [int(s) for s in user_input.split() if s.isdigit()]
        if len(size_range) == 2:
            filters['min_assets'], filters['max_assets'] = size_range
    if "revenue" in user_input:
        revenue_range = [int(s) for s in user_input.split() if s.isdigit()]
        if len(revenue_range) == 2:
            filters['min_revenue'], filters['max_revenue'] = revenue_range
    if "employees" in user_input:
        employee_range = [int(s) for s in user_input.split() if s.isdigit()]
        if len(employee_range) == 2:
            filters['min_employees'], filters['max_employees'] = employee_range
    if "expenses" in user_input:
        expense_range = [int(s) for s in user_input.split() if s.isdigit()]
        if len(expense_range) == 2:
            filters['min_expenses'], filters['max_expenses'] = expense_range
    if "miles" in user_input:
        miles = [int(s) for s in user_input.split() if s.isdigit()]
        if miles:
            filters['miles'] = miles[0]
    
    return filters


def get_coordinates(location):
    location = geolocator.geocode(location)
    if location:
        return (location.latitude, location.longitude)
    return None

def filter_and_group_data(data, filters):
    df = pd.DataFrame(data['organizations'])
    
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
    
    peer_groups = df.groupby(['city', 'state']).apply(lambda x: x.to_dict(orient='records')).to_dict()
    
    return df, peer_groups

def get_coordinates(location):
    location = geolocator.geocode(location)
    if location:
        return (location.latitude, location.longitude)
    return None

def filter_and_group_data(data, filters):
    df = pd.DataFrame(data['organizations'])
    
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
    
    peer_groups = df.groupby(['city', 'state']).apply(lambda x: x.to_dict(orient='records')).to_dict()
    
    return df, peer_groups


st.title("Nonprofit Peer Group Finder")
st.sidebar.header("Filter Options")

include_query = st.sidebar.checkbox("Include Search Query")
if include_query:
    user_query = st.sidebar.text_input("Enter your search query")

include_state = st.sidebar.checkbox("Include State")
if include_state:
    state_filter = st.sidebar.text_input("State (two-letter code, e.g., NY)")

include_ntee = st.sidebar.checkbox("Include NTEE Category")
if include_ntee:
    ntee_filter = st.sidebar.selectbox("NTEE Category", [None, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

include_c_code = st.sidebar.checkbox("Include 501(c) Classification")
if include_c_code:
    c_code_filter = st.sidebar.selectbox("501(c) Classification", [None, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 28, 92])

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
    if include_query and user_query:
        filters = parse_user_input(user_query)
        
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

    state = state_filter if include_state else None
    ntee = ntee_filter if include_ntee else None
    c_code = c_code_filter if include_c_code else None

    data = fetch_nonprofit_data(query=user_query if include_query else None, state=state, ntee=ntee, c_code=c_code)
    
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
