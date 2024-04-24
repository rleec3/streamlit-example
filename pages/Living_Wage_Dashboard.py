import altair as alt
import streamlit as st
import openpyxl
import pandas as pd
import streamlit_shadcn_ui as ui

# Assuming 'path_to_file.xlsx' is the correct path to your Excel file
file_path = 'fbc_data_2024_V1.2.xlsx'

st.set_page_config(page_title='Living Wage Dashboard', page_icon='C3_Only_Ball.png')
# Function to load data
@st.cache_data
def load_data(sheet_name):
    # Using the `header` parameter to specify which row contains column names
    # `engine='openpyxl'` is specified since the default engine might not handle '.xlsm' correctly
    data = pd.read_excel(file_path, sheet_name=sheet_name, header=0, engine='openpyxl')  
    data = data.dropna(axis='columns', how='all')  # Drop columns with all NaN values
    return data

# Load the County and Metro datasets
county_data = load_data('County_Annual')  # Update with the correct sheet name for County data
metro_data = load_data('Metro_Annual')  # Update with the correct sheet name for Metro data

# Streamlit application layout
banner_path = 'Horizontal_Banner_NoSC.png'
st.image(banner_path, width=400)
st.title("Living Wage Dashboard") 
ui.badges(badge_list=[ ("Under Construction", "destructive")], class_name="flex gap-2", key="main_badges1")

# Filter selection sidebar
with st.sidebar:
    data_type = st.radio("Select Data Type", ("County", "Metro"))
    selected_state = st.selectbox("Select State", county_data['State abv.'].unique())
    provider_filter = st.multiselect("Select Providers", [1, 2])
    dependents_filter = st.multiselect("Select Dependents", [0, 1, 2, 3, 4])

    # Dynamic selection for monetary columns to include in total
    monetary_columns = ['Housing', 'Food', 'Transportation', 'Healthcare', 'Other Necessities ', 'Childcare', 'Taxes']
    selected_monetary_columns = st.multiselect('Select monetary columns to include in Total:', monetary_columns)

# Based on data type, load the appropriate area data
if data_type == "County":
    areas = county_data[county_data['State abv.'] == selected_state]['County'].unique()
else:
    areas = metro_data[metro_data['State abv.'] == selected_state]['Areaname'].unique()

sorted_areas = sorted(areas)
selected_area = st.selectbox(f"Select {data_type} Area", sorted_areas)

#selected_area = st.selectbox(f"Select {data_type} Area", areas)

# Filter the data based on selections
if data_type == "County":
    filtered_data = county_data[
        (county_data['State abv.'] == selected_state) & 
        (county_data['County'] == selected_area) &
        (county_data['Provider'].isin(provider_filter)) &
        (county_data['Dependent'].isin(dependents_filter))  # Make sure 'Dependents' matches your data column
    ]
else:
    filtered_data = metro_data[
        (metro_data['State abv.'] == selected_state) & 
        (metro_data['Areaname'] == selected_area) &
        (metro_data['Provider'].isin(provider_filter)) &
        (metro_data['Dependent'].isin(dependents_filter))  # Make sure 'Dependents' matches your data column
    ]

# Calculate the total for selected monetary columns
if selected_monetary_columns:
    filtered_data['Total'] = filtered_data[selected_monetary_columns].astype(float).sum(axis=1)

# Exclude certain columns from the final output
columns_to_exclude = ['case_id', 'top100', 'num_counties_in_st', 'st_cost_rank', 'st_med_aff_rank', 'st_income_rank', 'top100_cost_rank', 'top100_med_faminc_rank', 'top100_med_aff_rank', 'county_fips']
columns_to_include = [col for col in filtered_data.columns if col not in columns_to_exclude]
final_output = filtered_data[columns_to_include]

final_output['Adult, Child Configuration'] = final_output['Provider'].astype(str) + ',' + final_output['Dependent'].astype(str)

# Display the final output in the Streamlit app
st.header("Living Wage") 
st.dataframe(final_output)


# Apply a 20% Healthcare credit and recalculate the total
if 'Healthcare' in final_output.columns:
    healthcare_credit_df = final_output.copy()
    healthcare_credit_df['Healthcare'] *= 0.20  # Apply the 20% credit

    # Check if 'Total' needs to be recalculated
    if 'Total' in healthcare_credit_df.columns and 'Healthcare' in selected_monetary_columns:
        healthcare_credit_df['Total'] = healthcare_credit_df[selected_monetary_columns].astype(float).sum(axis=1)

    # Display the new Living Wage table with Healthcare credit
    st.header("Living Wage w/ Healthcare Credit") 
    st.dataframe(healthcare_credit_df)

if 'Other Necessities ' in healthcare_credit_df.columns:
    thriving_wage_df = healthcare_credit_df.copy()
    thriving_wage_df['Other Necessities '] *= 2  # Double the values in 'Other Necessities'

    # Check if 'Total' needs to be recalculated
    if 'Total' in thriving_wage_df.columns and 'Other Necessities ' in selected_monetary_columns:
        # Only include the selected monetary columns for the new total
        thriving_wage_df['Total'] = thriving_wage_df[selected_monetary_columns].astype(float).sum(axis=1)

    # Display the new Thriving Wage table
    st.header("Thriving Wage") 
    st.dataframe(thriving_wage_df)


# comparison chart


filtered_data['Adult, Child Configuration'] = filtered_data['Provider'].astype(str) + ',' + filtered_data['Dependent'].astype(str)
# Create the 'Living Wage' and 'Thriving Wage' comparison DataFrame
comparison_df = pd.DataFrame({
    'Adult, Child Configuration': filtered_data['Adult, Child Configuration'],
    'Living Wage': healthcare_credit_df['Total'] / 1000,  # Divide by 1000 to match the desired unit
    'Thriving Wage': thriving_wage_df['Total'] / 1000  # Divide by 1000 to match the desired unit
})

# Display the comparison table
st.header(f"Household Living Wage for {selected_area}, {selected_state}")
st.table(comparison_df.style.format({'Living Wage': '${:,.0f}', 'Thriving Wage': '${:,.0f}'}))

# Create the bar chart comparison
long_df = comparison_df.melt('Adult, Child Configuration', var_name='Wage Type', value_name='Wage')

# Define color scheme
colors = ['#2078a1', '#144961']  # Light teal and dark teal colors

# Create the grouped bar chart
grouped_bar_chart = alt.Chart(long_df).mark_bar().encode(
    x=alt.X('Wage Type:N', axis=alt.Axis(title='')),
    y=alt.Y('Wage:Q', axis=alt.Axis(title='Wage (1,000s)', format=',.0f'), scale=alt.Scale(zero=True)),
    color=alt.Color('Wage Type:N', scale=alt.Scale(domain=['Living Wage', 'Thriving Wage'], range=colors)),
    tooltip=[alt.Tooltip('Wage Type:N', title='Wage Type'), alt.Tooltip('Wage:Q', title='Wage', format=',.0f')],
    order=alt.Order(
        # Sort to ensure that the bars are ordered correctly within each group
        'Wage Type:N',
        sort='ascending'
    )
).properties(
    width=alt.Step(30)  # Controls the width of the bars
).facet(
    column=alt.Column('Adult, Child Configuration:N', header=alt.Header(title=None))
)

# Display the chart
st.header(f"Household Living Wage for {selected_area}, {selected_state}")
st.altair_chart(grouped_bar_chart, use_container_width=True)