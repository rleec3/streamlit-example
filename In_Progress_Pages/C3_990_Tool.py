
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from lxml import etree
import openpyxl
from io import BytesIO
# Function to fetch years and corresponding URLs for the given EIN
st.set_page_config(page_title='Nonprofit Search Tool', page_icon='C3_Only_Ball.png', layout='wide')
def fetch_years(ein):
    base_url = "https://projects.propublica.org"
    url = f"{base_url}/nonprofits/organizations/{ein}"
    response = requests.get(url)
    years = {}
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        sections = soup.find_all("section", class_="single-filing-period")
        for section in sections:
            year = section['id'].replace("filing", "")
            links = section.find_all("a", class_="btn")
            xml_link = None
            for link in links:
                # Check if 'XML' is in the text, ignoring case
                if 'xml' in link.text.lower():
                    xml_link = link['href']
                    break
            if xml_link:
                years[year] = base_url + xml_link  # Concatenate base_url with the href attribute
                object_id = xml_link.split('object_id=')[-1]
                detailed_url = f"{base_url}/nonprofits/download-xml?object_id={object_id}"
                years[year] = (xml_link, detailed_url)
            else:
                years[year] = "XML link not found"  # Handle cases where no XML link is found
    return years
#helper function to extract text 
def get_text(soup, selector):
    element = soup.select_one(selector)
    return element.text.strip() if element else "Not Available"
# Function to fetch detailed data from a URL associated with a selected year
# Define namespaces for XML parsing
ns = {'efile': 'http://www.irs.gov/efile'}
# Fetch and parse organization and individual data
def fetch_data(ein, detailed_url):
    #url = full_url
    response = requests.get(detailed_url)
    if response.status_code == 200:
        tree = etree.fromstring(response.content)
        
        organization_data = {
            'EIN': ein,
            'Business Name': tree.xpath('//efile:Return/efile:ReturnHeader/efile:Filer/efile:BusinessName/efile:BusinessNameLine1Txt/text()', namespaces=ns)[0],
            'City': tree.xpath('//efile:Return/efile:ReturnHeader/efile:Filer/efile:USAddress/efile:CityNm/text()', namespaces=ns)[0] if tree.xpath('//efile:Return/efile:ReturnHeader/efile:Filer/efile:USAddress/efile:CityNm/text()', namespaces=ns) else "Not Available",
            'State': tree.xpath('//efile:Return/efile:ReturnHeader/efile:Filer/efile:USAddress/efile:StateAbbreviationCd/text()', namespaces=ns)[0],
            'Fiscal Year End': tree.xpath('//efile:Return/efile:ReturnHeader/efile:TaxPeriodEndDt/text()', namespaces=ns)[0],
            'Total Assets EOY': tree.xpath('//efile:Return/efile:ReturnData/efile:IRS990/efile:TotalAssetsEOYAmt/text()', namespaces=ns)[0],
            'Total Expenses': tree.xpath('//efile:Return/efile:ReturnData/efile:IRS990/efile:CYTotalExpensesAmt/text()', namespaces=ns)[0],
            'Total Revenue': tree.xpath('//efile:Return/efile:ReturnData/efile:IRS990/efile:CYTotalRevenueAmt/text()', namespaces=ns)[0],
            'Employee Count': tree.xpath('//efile:Return/efile:ReturnData/efile:IRS990/efile:TotalEmployeeCnt/text()', namespaces=ns)[0],
            # Add additional organization fields as necessary
        }
        fiscal_year_end_text = organization_data["Fiscal Year End"]
        if "-" in fiscal_year_end_text:
                fiscal_year_parts = fiscal_year_end_text.split("-")
                if len(fiscal_year_parts) == 3:
                    fiscal_year_month = int(fiscal_year_parts[1])
                    fiscal_year_year = int(fiscal_year_parts[0])
                    if fiscal_year_month == 12:
                        w_year_end = fiscal_year_end_text
                    else:
                        w_year_end = f"{fiscal_year_year - 1}-12-31"
                    organization_data["WYearEnd"] = w_year_end
        #helper function
        def get_text(section, xpaths, namespaces):
            # Accept xpaths as a list to handle multiple possible tags
            for xpath in xpaths:
                result = section.xpath(xpath, namespaces=namespaces)
                if result:
                    return result[0]  # Return the first result found
            return "Not Available"
        # Parse individuals' data
        individuals_data = []
        part_j_sections = tree.xpath('//efile:Return/efile:ReturnData/efile:IRS990ScheduleJ/efile:RltdOrgOfficerTrstKeyEmplGrp', namespaces=ns)
        for section in part_j_sections:
            name = get_text(section, ['.//efile:PersonNm/text()', './/efile:BusinessNameLine1Txt/text()'], ns)
            title = section.xpath('.//efile:TitleTxt/text()', namespaces=ns)[0] if section.xpath('.//efile:TitleTxt/text()', namespaces=ns) else "Not Available"
            compensation_data = {
                'Base Compensation': section.xpath('.//efile:BaseCompensationFilingOrgAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:BaseCompensationFilingOrgAmt/text()', namespaces=ns) else "Not Available",
                'Bonus': section.xpath('.//efile:BonusFilingOrganizationAmount/text()', namespaces=ns)[0] if section.xpath('.//efile:BonusFilingOrganizationAmount/text()', namespaces=ns) else "Not Available",
                'Other Compensation': section.xpath('.//efile:OtherCompensationFilingOrgAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:OtherCompensationFilingOrgAmt/text()', namespaces=ns) else "Not Available",
                'Deferred Compensation': section.xpath('.//efile:DeferredCompensationFlngOrgAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:DeferredCompensationFlngOrgAmt/text()', namespaces=ns) else "Not Available",
                'Nontaxable Benefits': section.xpath('.//efile:NontaxableBenefitsFilingOrgAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:NontaxableBenefitsFilingOrgAmt/text()', namespaces=ns) else "Not Available",
                'Total Compensation': section.xpath('.//efile:TotalCompensationFilingOrgAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:TotalCompensationFilingOrgAmt/text()', namespaces=ns) else "Not Available",
                'Reportable Compensation (Part VII)': section.xpath('.//efile:ReportableCompFromOrgAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:ReportableCompFromOrgAmt/text()', namespaces=ns) else "Not Available",
                'Reportable Compensation From Rltd Org (Part VII)': section.xpath('.//efile:ReportableCompFromRltdOrgAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:ReportableCompFromRltdOrgAmt/text()', namespaces=ns) else "Not Available",
                'Other Compensation (Part VII)': section.xpath('.//efile:OtherCompensationAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:OtherCompensationAmt/text()', namespaces=ns) else "Not Available",
                'Avg Hr Per Week (Part VII)': section.xpath('.//efile:AverageHoursPerWeekRt/text()', namespaces=ns)[0] if section.xpath('.//efile:AverageHoursPerWeekRt/text()', namespaces=ns) else "Not Available",
            }
            individual_data = {'Name': name, 'Title': title}
            individual_data.update(compensation_data)
            individuals_data.append(individual_data)
        
        #schedule A
        individuals_data2 = []
        part_vii_sections = tree.xpath('//efile:Return/efile:ReturnData/efile:IRS990/efile:Form990PartVIISectionAGrp', namespaces=ns)
        for section in part_vii_sections:
            name = get_text(section, ['.//efile:PersonNm/text()', './/efile:BusinessNameLine1Txt/text()'], ns)
            title = section.xpath('.//efile:TitleTxt/text()', namespaces=ns)[0] if section.xpath('.//efile:TitleTxt/text()', namespaces=ns) else "Not Available"
            compensation_data2 = {
                'Reportable Compensation (Part VII)': section.xpath('.//efile:ReportableCompFromOrgAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:ReportableCompFromOrgAmt/text()', namespaces=ns) else "Not Available",
                'Reportable Compensation From Rltd Org (Part VII)': section.xpath('.//efile:ReportableCompFromRltdOrgAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:ReportableCompFromRltdOrgAmt/text()', namespaces=ns) else "Not Available",
                'Other Compensation (Part VII)': section.xpath('.//efile:OtherCompensationAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:OtherCompensationAmt/text()', namespaces=ns) else "Not Available",
                'Avg Hr Per Week (Part VII)': section.xpath('.//efile:AverageHoursPerWeekRt/text()', namespaces=ns)[0] if section.xpath('.//efile:AverageHoursPerWeekRt/text()', namespaces=ns) else "Not Available",
            }
            individual_data2 = {'Name': name, 'Title': title}
            individual_data2.update(compensation_data2)
            individuals_data2.append(individual_data2)
        #return {'organization_data': organization_data, 'individuals_data': individuals_data, 'individuals_data2': individual_data2}
    #else:
        #return {'organization_data': {}, 'individuals_data': [], 'individuals_data2': []}
        for individual in individuals_data:
            corresponding_entry = next((entry for entry in individuals_data2 if entry['Name'] == individual['Name']), None)
            if corresponding_entry:
                individual.update(corresponding_entry)
        return {'organization_data': organization_data, 'individuals_data': individuals_data}
    else:
        return {'organization_data': {}, 'individuals_data': []}
# Streamlit UI components

def edit_excel_template(data, template_path):
    workbook = openpyxl.load_workbook(template_path)
    sheet = workbook["Template"]  # Assumes that the sheet name is "Template"
    row = 9
    for entry in data:
        sheet[f"D{row}"] = entry["Organization_Name"]
        sheet[f"E{row}"] = entry["EIN"]
        sheet[f"F{row}"] = f"{entry['City']}, {entry['State']}"
        sheet[f"K{row}"] = entry["Employee_Name"]
        sheet[f"L{row}"] = entry["Title_Of_Position"]
        sheet[f"M{row}"] = entry["Base Compensation"]
        sheet[f"Q{row}"] = entry["Deferred Compensation"]
        sheet[f"P{row}"] = entry["Other Compensation"]
        sheet[f"G{row}"] = entry["W2E"]
        sheet[f"H{row}"] = entry["Fiscal_Year_End"]
        sheet[f"J{row}"] = entry["Total Assets"]
        sheet[f"R{row}"] = entry["Nontaxable Benefits"]
        sheet[f"S{row}"] = entry["Total Compensation"]
        sheet[f"N{row}"] = entry["Bonus"]
        
        row += 1
    edited_file = BytesIO()
    workbook.save(edited_file)
    edited_file.seek(0)  # Move the cursor to the start of the stream
    return edited_file

# Streamlit UI components
banner_path = 'Horizontal_Banner_NoSC.png'
st.image(banner_path, width=400)
st.header("C3 990 Tool")
num_orgs = st.number_input("How many organizations do you want to fetch?", min_value=1, max_value=30, value=1, key="num_orgs")
# Initialize or reset session state variables as needed
if 'organizations_data' not in st.session_state:
    st.session_state['organizations_data'] = []
if 'all_individuals_data' not in st.session_state:
    st.session_state['all_individuals_data'] = []
if 'selected_incumbents' not in st.session_state:
    st.session_state['selected_incumbents'] = {}
if 'year_data' not in st.session_state:
    st.session_state['year_data'] = {}
if 'selected_years' not in st.session_state:
    st.session_state['selected_years'] = {}
# Initialize year_data for each organization
for i in range(num_orgs):
    if str(i) not in st.session_state['year_data']:
        st.session_state['year_data'][str(i)] = {}
# Generate EIN input fields and year dropdowns dynamically
for i in range(num_orgs):
    with st.container():
        col1, col2 = st.columns(2)
        ein = col1.text_input(f"Enter EIN {i+1}", key=f"ein_{i}")
        
        if ein.strip() and not st.session_state['year_data'][str(i)]:
            st.session_state['year_data'][str(i)] = fetch_years(ein)
        
        if st.session_state['year_data'][str(i)]:
            years = list(st.session_state['year_data'][str(i)].keys())
            if years:
                selected_year = col2.selectbox("Select a year", years, key=f"year_{i}")
                st.session_state['selected_years'][str(i)] = selected_year
# Single button to fetch data for all selected EINs and years
if st.button("Fetch Data for All Selected", key='fetch_data_button'):
    st.session_state['organizations_data'] = []
    st.session_state['all_individuals_data'] = []
    for i in range(num_orgs):
        ein = st.session_state[f"ein_{i}"]
        year = st.session_state['selected_years'][str(i)]
        if ein.strip() and year:
            detailed_url = st.session_state['year_data'][str(i)][year][1]
            fetched_data = fetch_data(ein, detailed_url)
            st.session_state['organizations_data'].append(fetched_data['organization_data'])
            st.session_state['all_individuals_data'].append(fetched_data['individuals_data'])
            # Display organization data and individuals data if available
            #st.write(f"Organization data for {ein} in the year {year}:")
            organization_data = fetched_data['organization_data']
            st.subheader(organization_data.get('Business Name', 'Unknown'))
            st.write(f"Organization data in the year {year}:")
            st.json(fetched_data['organization_data'])
            
            if fetched_data['individuals_data']:
                st.write(f"Individuals data in the year {year}:")
                df_individuals = pd.DataFrame(fetched_data['individuals_data'])
                st.dataframe(df_individuals)
# Check if the data is fetched to display the dropdowns for selecting incumbents
if st.session_state.get('organizations_data') and st.session_state.get('all_individuals_data'):
    for i, individuals_data in enumerate(st.session_state['all_individuals_data']):
        if individuals_data:
            employee_options = ['None'] + [f"{person['Name']} ({person['Title']})" for person in individuals_data]
            key = f"employee_{i}"
            st.session_state.selected_incumbents[key] = st.selectbox(
                f"Select an employee for organization {i+1}", options=employee_options, index=0, key=f"employee_{i}"
            )
# Button to generate the final output chart after confirmation of selections
if st.button("Generate Final Output Chart", key='generate_chart_button'):
    final_chart_data = []
    if 'final_chart_data' not in st.session_state:
        st.session_state['final_chart_data'] = []
    
    # To avoid duplicates, create a set of unique identifiers for each row based on EIN and name
    existing_data_identifiers = {(row['EIN'], row['Employee_Name']) for row in st.session_state['final_chart_data']}
    
    for i, organization_data in enumerate(st.session_state['organizations_data']):
        incumbent_key = f"employee_{i}"
        if st.session_state.selected_incumbents.get(incumbent_key) and st.session_state.selected_incumbents[incumbent_key] != 'None':
            name_title = st.session_state.selected_incumbents[incumbent_key].split(' (')
            name = name_title[0]
            title = name_title[1].rstrip(')')
            selected_person_data = next(
                (person for person in st.session_state['all_individuals_data'][i]
                if f"{person['Name']} ({person['Title']})" == st.session_state.selected_incumbents[incumbent_key]), None
            )
            if selected_person_data and (organization_data.get('EIN'), name) not in existing_data_identifiers:
                chart_row = {
                    "Organization_Name": organization_data.get('Business Name', 'Unknown'),
                    "EIN": organization_data.get('EIN', 'Not Available'),
                    "Fiscal_Year_End": organization_data.get('Fiscal Year End', 'Not Available'),
                    "W2E": organization_data.get('WYearEnd', 'Not Available'),
                    "City": organization_data.get('City', 'Not Available'),
                    "State": organization_data.get('State', 'Not Available'),
                    "Employee_Name": name,
                    "Title_Of_Position": title,
                    "Total Assets": organization_data.get('Total Assets EOY', 'Not Available'),
                    "Total Expenses": organization_data.get('Total Expenses', 'Not Available'),
                    "Total Revenue": organization_data.get('Total Revenue', 'Not Available'),
                    "Employee Count": organization_data.get('Employee Count', 'Not Available'),
                    "Base Compensation": selected_person_data.get('Base Compensation', 'Not Available'),
                    "Bonus": selected_person_data.get('Bonus', 'Not Available'),
                    "Other Compensation": selected_person_data.get('Other Compensation', 'Not Available'),
                    "Deferred Compensation": selected_person_data.get('Deferred Compensation', 'Not Available'),
                    "Nontaxable Benefits": selected_person_data.get('Nontaxable Benefits', 'Not Available'),
                    "Total Compensation": selected_person_data.get('Total Compensation', 'Not Available'),
                    # ... include additional fields as necessary ...
                }
                # Append the row to the final chart data in session state
                final_chart_data.append(chart_row)
                st.session_state['final_chart_data'].append(chart_row)
    
    # Convert the final chart data to a DataFrame and display it
    final_df = pd.DataFrame(st.session_state['final_chart_data'])
    st.write(final_df)
    #st.dataframe(final_df)

    if final_chart_data:
        edited_file = edit_excel_template(final_chart_data, '990TEMPLATE.xlsx')
        st.download_button(label="Download Updated 990 Template", data=edited_file, file_name="990_template.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
# Reset functionality
if st.button("Reset", key='reset_button'):
    st.session_state.clear()
    st.experimental_rerun()
