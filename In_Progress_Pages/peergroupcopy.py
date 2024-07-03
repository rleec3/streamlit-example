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
ORG_URL = 'https://projects.propublica.org/nonprofits/api/v2/organizations/{}.json'
def fetch_nonprofit_data(state=None, city=None, zip_code=None, ntee=None, c_code=None, page=0):
    params = {'page': page}
    if state:
        params['state[id]'] = state
    if city:
        params['city'] = city
    if zip_code:
        params['zipcode'] = zip_code
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

def fetch_organization_by_ein(ein):
    response = requests.get(ORG_URL.format(ein))
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch organization data from ProPublica")
        return None
def parse_user_input(user_input):
    inputs = tokenizer(user_input, return_tensors="pt")
    outputs = model.generate(inputs.input_ids, max_length=50)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    filters = {}
    if "location" in user_input:
        filters['location'] = user_input.split("location")[1].strip()
    return filters

def get_coordinates(location):
    location = geolocator.geocode(location)
    if location:
        return (location.latitude, location.longitude)
    return None

def filter_and_rank_data(data, comparison_org, filters, proximity=None):
    df = pd.DataFrame(data['organizations'])
    
    if 'location' in filters and 'proximity' in filters:
        location_coords = get_coordinates(filters['location'])
        if location_coords:
            def within_proximity(row):
                row_coords = (row['latitude'], row['longitude'])
                return geodesic(location_coords, row_coords).miles <= filters['proximity']
            df = df[df.apply(within_proximity, axis=1)]
    
    if comparison_org:
        comparison_stats = {
            'assets': comparison_org.get('totassetsend', 0),
            'revenue': comparison_org.get('totrevenue', 0),
            'expenses': comparison_org.get('totfuncexpns', 0),
            'employees': comparison_org.get('employees', 0),
        }
        
        df['within_assets_range'] = df['totassetsend'].apply(lambda x: 0.5 * comparison_stats['assets'] <= x <= 2 * comparison_stats['assets'] if x is not None else False)
        df['within_revenue_range'] = df['totrevenue'].apply(lambda x: 0.5 * comparison_stats['revenue'] <= x <= 2 * comparison_stats['revenue'] if x is not None else False)
        df['within_expenses_range'] = df['totfuncexpns'].apply(lambda x: 0.5 * comparison_stats['expenses'] <= x <= 2 * comparison_stats['expenses'] if x is not None else False)
        df['within_employees_range'] = df['employees'].apply(lambda x: 0.5 * comparison_stats['employees'] <= x <= 2 * comparison_stats['employees'] if x is not None else False)
        df['same_state'] = df['state'] == comparison_org['state']
        
        df['matches'] = df[['within_assets_range', 'within_revenue_range', 'within_expenses_range', 'within_employees_range', 'same_state']].sum(axis=1)
        df = df.sort_values('matches', ascending=False)
    
    return df
st.title("Nonprofit Peer Group Finder")
st.sidebar.header("Filter Options")

include_proximity = st.sidebar.checkbox("Include Proximity")
if include_proximity:
    proximity_filter = st.sidebar.number_input("Proximity (miles)", min_value=0, step=1)

include_state = st.sidebar.checkbox("Include State")
if include_state:
    state_filter = st.sidebar.text_input("State (two-letter code, e.g., NY)")

include_city = st.sidebar.checkbox("Include City")
if include_city:
    city_filter = st.sidebar.text_input("City")

include_zip_code = st.sidebar.checkbox("Include Zip Code")
if include_zip_code:
    zip_code_filter = st.sidebar.text_input("Zip Code")

include_ntee = st.sidebar.checkbox("Include NTEE Category")
if include_ntee:
    ntee_filter = st.sidebar.selectbox("NTEE Category", [None, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

include_c_code = st.sidebar.checkbox("Include 501(c) Classification")
if include_c_code:
    c_code_filter = st.sidebar.selectbox("501(c) Classification", [None, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 28, 92])

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

comparison_toggle = st.sidebar.checkbox("Enable Comparison with Target Organization")
if comparison_toggle:
    comparison_ein = st.sidebar.text_input("Input Target Organization EIN")
if st.sidebar.button("Search"):
    comparison_org = None
    if comparison_toggle and comparison_ein:
        comparison_org_data = fetch_organization_by_ein(comparison_ein)
        if comparison_org_data:
            comparison_org = comparison_org_data['organization']

    data = fetch_nonprofit_data(
        state=state_filter if include_state else None, 
        city=city_filter if include_city else None, 
        zip_code=zip_code_filter if include_zip_code else None, 
        ntee=ntee_filter if include_ntee else None, 
        c_code=c_code_filter if include_c_code else None
    )
    
    if data and data['organizations']:
        # Display comparison organization information
        if comparison_org:
            st.write("### Target Organization Information")
            st.write(comparison_org)

        filters = parse_user_input("")
        if include_proximity:
            filters['proximity'] = proximity_filter

        df = filter_and_rank_data(data, comparison_org, filters, proximity_filter if include_proximity else None)
        
        st.write("### Similar Organizations")
        for index, row in df.iterrows():
            st.write(f"Name: {row['name']}, City: {row['city']}, State: {row['state']}, Assets: {row.get('totassetsend', 'N/A')}, Revenue: {row.get('totrevenue', 'N/A')}, Employees: {row.get('employees', 'N/A')}")
            if comparison_org:
                checks = {
                    'Assets': row.get('within_assets_range', False),
                    'Revenue': row.get('within_revenue_range', False),
                    'Expenses': row.get('within_expenses_range', False),
                    'Employees': row.get('within_employees_range', False),
                    'State': row.get('same_state', False)
                }
                for key, value in checks.items():
                    st.write(f"{key}: {'✅' if value else '❌'}")
