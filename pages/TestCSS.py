import streamlit as st

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">', unsafe_allow_html=True)    

def icon(icon_name):
    st.markdown(f'<i class="material-icons">{icon_name}</i>', unsafe_allow_html=True)

local_css("CSS/streamlit.css")
remote_css('https://fonts.googleapis.com/icon?family=Material+Icons')

icon("search")
selected = st.text_input("", "Search...")
button_clicked = st.button("OK")


#######################


import altair as alt
import streamlit as st
import openpyxl
import pandas as pd
import streamlit_shadcn_ui as ui
from io import BytesIO

# Assuming 'path_to_file.xlsx' is the correct path to your Excel file
file_path = 'fbc_data_2024_V1.2.xlsx'


st.header("Living Wage Dashboard") 
st.caption('Source: Economic Policy Institute Family Budget Calculator, January 2024. Data are in 2023 dollars.')

col1, col2 = st.columns([2, 2])  # Here, col1 is three times wider than col2

# Place a caption in each column
with col1:
    st.caption('⚪ : Data not utilized in client deliverables')

with col2:
    st.caption('🟢 : Data utilized in client deliverables')
#ui.badges(badge_list=[ ("Under Construction", "destructive")], class_name="flex gap-2", key="main_badges1")

# Filter selection sidebar
with st.sidebar:
    data_type = st.radio("Select Data Type", ("County", "Metro"))
    selected_state = st.selectbox("Select State", county_data['State abv.'].unique())
    

    

# Based on data type, load the appropriate area data
if data_type == "County":
    areas = county_data[county_data['State abv.'] == selected_state]['County'].unique()
else:
    areas = metro_data[metro_data['State abv.'] == selected_state]['Areaname'].unique()

sorted_areas = sorted(areas)
selected_area = st.selectbox(f"Select {data_type} Area", sorted_areas)