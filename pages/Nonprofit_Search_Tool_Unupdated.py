
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from lxml import etree

# Function to fetch years and corresponding URLs for the given EIN
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
        
        # Parse individuals' data
        individuals_data = []
        part_j_sections = tree.xpath('//efile:Return/efile:ReturnData/efile:IRS990ScheduleJ/efile:RltdOrgOfficerTrstKeyEmplGrp', namespaces=ns)
        for section in part_j_sections:
            name = section.xpath('.//efile:PersonNm/text()', namespaces=ns)[0] if section.xpath('.//efile:PersonNm/text()', namespaces=ns) else "Not Available"
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
            name = section.xpath('.//efile:PersonNm/text()', namespaces=ns)[0] if section.xpath('.//efile:PersonNm/text()', namespaces=ns) else "Not Available"
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
import streamlit as st
# Streamlit UI components
st.title("Nonprofit Organization Data Fetcher")
num_orgs = st.number_input("How many organizations do you want to fetch?", min_value=1, max_value=10, value=1, key="num_orgs")
# Initialize or manage year data and selected years
if 'year_data' not in st.session_state or 'selected_years' not in st.session_state or 'prev_num_orgs' not in st.session_state or st.session_state['prev_num_orgs'] != num_orgs:
    st.session_state['year_data'] = {str(i): {} for i in range(num_orgs)}
    st.session_state['selected_years'] = {str(i): "" for i in range(num_orgs)}
    st.session_state['prev_num_orgs'] = num_orgs
# Generate EIN input fields and year dropdowns dynamically
for i in range(num_orgs):
    with st.container():
        col1, col2 = st.columns(2)
        ein = col1.text_input(f"Enter EIN {i+1}", key=f"ein_{i}")
        
        # Load available years when an EIN is entered and update dynamically
        if ein.strip() and not st.session_state['year_data'][str(i)]:
            st.session_state['year_data'][str(i)] = fetch_years(ein)
        
        # Show available years dropdown next to the EIN input if years are loaded
        if st.session_state['year_data'][str(i)]:
            years = list(st.session_state['year_data'][str(i)].keys())
            st.session_state['selected_years'][str(i)] = col2.selectbox("Select a year", years, key=f"year_{i}")
# Single button to fetch data for all selected EINs and years
if st.button("Fetch Data for All Selected"):
    for i in range(num_orgs):
        ein = st.session_state[f"ein_{i}"]
        year = st.session_state['selected_years'][str(i)]
        if ein.strip() and year:
            detailed_url = st.session_state['year_data'][str(i)][year][1]
            fetched_data = fetch_data(ein, detailed_url)
            organization_data = fetched_data['organization_data']
            individuals_data = fetched_data['individuals_data']
            # Display organization data
            st.write(f"Organization data for {ein} in the year {year}:")
            st.json(organization_data)
            # Create and display a dataframe for individuals_data
            if individuals_data:
                st.write(f"Individuals data for {ein} in the year {year}:")
                df_individuals = pd.DataFrame(individuals_data)
                st.dataframe(df_individuals)
            else:
                st.write("No individuals data found for this organization.")
    
# Reset functionality
if st.button("Reset"):
    st.session_state['year_data'] = {str(i): {} for i in range(num_orgs)}
    st.session_state['selected_years'] = {str(i): "" for i in range(num_orgs)}
    st.experimental_rerun()



