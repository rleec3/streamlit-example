import os
import streamlit as st
import requests
import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json

# Load model and tokenizer
model_name = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Function to get response from the local model
def get_response(prompt):
    inputs = tokenizer.encode(prompt, return_tensors="pt")
    outputs = model.generate(inputs, max_length=150, num_return_sequences=1, pad_token_id=tokenizer.eos_token_id)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.strip()

# Improved function to parse parameters from the local model response
def extract_parameters(response):
    try:
        response_json = json.loads(response)
        state = response_json.get("state", "NC")
        sort = response_json.get("sort", "-recent_annual_revenue")
        revenue_buckets = response_json.get("revenue_buckets", [5000000, 15000000])
        ntee_code = response_json.get("ntee_code", "B")
        operates_school = response_json.get("operates_school", False)
        show_only_active = response_json.get("show_only_active", True)
        limit = response_json.get("limit", 5)
        return state, sort, revenue_buckets, ntee_code, operates_school, show_only_active, limit
    except json.JSONDecodeError:
        st.error("Failed to decode parameters from response.")
        return "NC", "-recent_annual_revenue", [5000000, 15000000], "B", False, True, 5

# Function to search ProPublica
def search_propublica(state, sort, revenue_buckets, ntee_code, operates_school, show_only_active, limit):
    propublica_url = f"https://projects.propublica.org/nonprofits/search?sort={sort}&state%5B%5D={state}&recent_annual_revenue%5B%5D={'&recent_annual_revenue%5B%5D='.join(map(str, revenue_buckets))}&ntee_code%5B%5D={ntee_code}&operates_school={'1' if operates_school else '0'}&show_only_active={'1' if show_only_active else '0'}&q=&submit=Apply"
    response = requests.get(propublica_url)
    response.raise_for_status()
    return response.json()

# Function to fetch data from IRS 990 Data API
def fetch_irs_data(ein):
    irs_url = f"https://990-infrastructure.gtdata.org/irs-data/990basic120fields?ein={ein}"
    response = requests.get(irs_url)
    response.raise_for_status()
    return response.json()

# Extracting specific fields from IRS 990 Data API response
def parse_irs_data(data):
    results = data.get('body', {}).get('results', [])
    if results:
        result = results[0]
        return {
            "Organization Name": result.get('FILERNAME1', ''),
            "EIN": result.get('FILEREIN', ''),
            "Revenue": result.get('TOTREVCURYEA', ''),
            "Expenses": result.get('TOTEXPCURYEA', ''),
            "Assets": result.get('TOTASSETSEND', ''),
            "Tax Year": result.get('TAXYEAR', ''),
            "Title": result.get('TITLE', ''),  # Assuming TITLE field
            "Employee Name": result.get('EMPLOYEE_NAME', ''),  # Assuming EMPLOYEE_NAME field
            "Base Compensation": result.get('BASE_COMPENSATION', ''),  # Assuming BASE_COMPENSATION field
            "Bonus & Incentive Compensation": result.get('BONUS_INCENTIVE_COMPENSATION', ''),  # Assuming BONUS_INCENTIVE_COMPENSATION field
            "Other Reportable Compensation": result.get('OTHER_REPORTABLE_COMPENSATION', ''),  # Assuming OTHER_REPORTABLE_COMPENSATION field
            "Retirement and Deferred Compensation": result.get('RETIREMENT_DEFERRED_COMPENSATION', ''),  # Assuming RETIREMENT_DEFERRED_COMPENSATION field
            "Nontaxable Benefits": result.get('NONTAXABLE_BENEFITS', ''),  # Assuming NONTAXABLE_BENEFITS field
            "Total Reportable Compensation": result.get('TOTAL_REPORTABLE_COMPENSATION', ''),  # Assuming TOTAL_REPORTABLE_COMPENSATION field
            "Health Benefits": result.get('HEALTH_BENEFITS', ''),  # Assuming HEALTH_BENEFITS field
            "Contributions to Employee Benefit Plans": result.get('CONTRIBUTIONS_EMPLOYEE_BENEFIT_PLANS', ''),  # Assuming CONTRIBUTIONS_EMPLOYEE_BENEFIT_PLANS field
            "Estimated Other Compensation": result.get('ESTIMATED_OTHER_COMPENSATION', ''),  # Assuming ESTIMATED_OTHER_COMPENSATION field
            "Total Compensation": result.get('TOTAL_COMPENSATION', ''),  # Assuming TOTAL_COMPENSATION field
            "Citation": f"https://projects.propublica.org/nonprofits/organizations/{result.get('FILEREIN', '')}"
        }
    return {}

# Streamlit App
st.title("Nonprofit Data Chatbot")

# Initialize session state for messages
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# User input
user_input = st.text_input("You: ", key="user_input")
if user_input:
    st.session_state['messages'].append(f"You: {user_input}")
    gpt_prompt = f"User asked: {user_input}\nPlease provide the necessary parameters for searching nonprofits, including state, sort order, revenue buckets, NTEE code, operates school, show only active, and limit."
    gpt_response = get_response(gpt_prompt)
    st.session_state['messages'].append(f"Bot: {gpt_response}")

    # Extract parameters from the local model response
    state, sort, revenue_buckets, ntee_code, operates_school, show_only_active, limit = extract_parameters(gpt_response)

    # Search ProPublica
    try:
        propublica_data = search_propublica(state, sort, revenue_buckets, ntee_code, operates_school, show_only_active, limit)
        eins = [org['ein'] for org in propublica_data['organizations'][:limit]]
    except Exception as e:
        st.error(f"Error searching ProPublica: {e}")
        st.stop()

    # Fetch IRS data for each EIN
    irs_data_list = []
    for ein in eins:
        try:
            irs_data = fetch_irs_data(ein)
            parsed_data = parse_irs_data(irs_data)
            irs_data_list.append(parsed_data)
        except Exception as e:
            st.error(f"Error fetching IRS data for EIN {ein}: {e}")

    # Display the data in a table
    if irs_data_list:
        df = pd.DataFrame(irs_data_list)
        st.write(df)

# Display chat messages
for message in st.session_state['messages']:
    st.write(message)
