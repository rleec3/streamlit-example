
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from lxml import etree
import openpyxl
from io import BytesIO
from datetime import datetime



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
#def get_text(soup, selector):
    #element = soup.select_one(selector)
    #return element.text.strip() if element else "Not Available"
# Function to fetch detailed data from a URL associated with a selected year
# Define namespaces for XML parsing
ns = {'efile': 'http://www.irs.gov/efile'}
def get_text(element, xpaths, namespaces):
    """
    Attempt to fetch data from a list of XPaths.
    Returns the text from the first successful XPath query or "Not Available" if none match.
    """
    for xpath in xpaths:
        result = element.xpath(xpath, namespaces=namespaces)
        if result:
            return result[0]  # Return the first result found
    return "Not Available"
# Fetch and parse organization and individual data
def fetch_data(ein, detailed_url):
    #url = full_url
    
    response = requests.get(detailed_url)
    if response.status_code == 200:
        tree = etree.fromstring(response.content)
        
        organization_data = {
            'EIN': ein,
            'Business Name': get_text(tree, ['//efile:Return/efile:ReturnHeader/efile:Filer/efile:BusinessName/efile:BusinessNameLine1Txt/text()'], ns),
            'City': get_text(tree, ['//efile:Return/efile:ReturnHeader/efile:Filer/efile:USAddress/efile:CityNm/text()'], ns),
            'State': get_text(tree, ['//efile:Return/efile:ReturnHeader/efile:Filer/efile:USAddress/efile:StateAbbreviationCd/text()'], ns),
            'Fiscal Year End': get_text(tree, ['//efile:Return/efile:ReturnHeader/efile:TaxPeriodEndDt/text()'], ns),
            'Total Assets EOY': get_text(tree, ['//efile:Return/efile:ReturnData/efile:IRS990/efile:TotalAssetsEOYAmt/text()', './/efile:FMVAssetsEOYAmt/text()'], ns),
            'Total Expenses': get_text(tree, ['//efile:Return/efile:ReturnData/efile:IRS990/efile:CYTotalExpensesAmt/text()', './/efile:TotalExpensesRevAndExpnssAmt/text()'], ns),
            'Total Revenue': get_text(tree, ['//efile:Return/efile:ReturnData/efile:IRS990/efile:CYTotalRevenueAmt/text()', './/efile:TotalRevAndExpnssAmt/text()'], ns), 
            'Employee Count': get_text(tree, ['//efile:Return/efile:ReturnData/efile:IRS990/efile:TotalEmployeeCnt/text()'], ns)
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
        #def get_text(section, xpaths, namespaces):
            # Accept xpaths as a list to handle multiple possible tags
            #for xpath in xpaths:
                #result = section.xpath(xpath, namespaces=namespaces)
                #if result:
                    #return result[0]  # Return the first result found
            #return "Not Available"
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
                'Avg Hr Per Week (Part VII) Test': section.xpath('.//efile:AverageHoursPerWeekRt/text()', namespaces=ns)[0] if section.xpath('.//efile:AverageHoursPerWeekRt/text()', namespaces=ns) else "Not Available",
            }
            individual_data = {'Name': name, 'Title': title}
            individual_data.update(compensation_data)
            individuals_data.append(individual_data)
        
        #schedule A
        individuals_data2 = []
        part_vii_sections = tree.xpath('//efile:Return/efile:ReturnData/efile:IRS990/efile:Form990PartVIISectionAGrp', namespaces=ns)
        for section in part_vii_sections:
            name = get_text(section, ['.//efile:PersonNm/text()', './/efile:BusinessNameLine1Txt/text()'], ns)
            title = get_text(section, ['.//efile:TitleTxt/text()', './/efile:TitleTxt/text()'], ns)
            compensation_data2 = {
                'Reportable Compensation (Part VII)': section.xpath('.//efile:ReportableCompFromOrgAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:ReportableCompFromOrgAmt/text()', namespaces=ns) else "Not Available",
                'Reportable Compensation From Rltd Org (Part VII)': section.xpath('.//efile:ReportableCompFromRltdOrgAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:ReportableCompFromRltdOrgAmt/text()', namespaces=ns) else "Not Available",
                'Other Compensation (Part VII)': section.xpath('.//efile:OtherCompensationAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:OtherCompensationAmt/text()', namespaces=ns) else "Not Available",
                'Avg Hr Per Week (Part VII)': section.xpath('.//efile:AverageHoursPerWeekRt/text()', namespaces=ns)[0] if section.xpath('.//efile:AverageHoursPerWeekRt/text()', namespaces=ns) else "Not Available",
            }
            individual_data2 = {'Name': name, 'Title': title}
            individual_data2.update(compensation_data2)
            individuals_data2.append(individual_data2)
            
        #990PF
        individuals_data3 = []
        part_pf_sections = tree.xpath('//efile:Return/efile:ReturnData/efile:IRS990PF/efile:OfficerDirTrstKeyEmplInfoGrp/efile:OfficerDirTrstKeyEmplGrp', namespaces=ns)
        for section in part_pf_sections:
            name = get_text(section, ['.//efile:PersonNm/text()', './/efile:BusinessNameLine1Txt/text()'], ns)
            title = get_text(section, ['.//efile:TitleTxt/text()'], ns)
            compensation_data3 = {
                'Reportable Compensation (PF)': section.xpath('.//efile:CompensationAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:CompensationAmt/text()', namespaces=ns) else "Not Available",
                'Employee Benefit Amount (PF)': section.xpath('.//efile:EmployeeBenefitProgramAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:EmployeeBenefitProgramAmt/text()', namespaces=ns) else "Not Available",
                'Other Compensation (PF)': section.xpath('.//efile:ExpenseAccountOtherAllwncAmt/text()', namespaces=ns)[0] if section.xpath('.//efile:ExpenseAccountOtherAllwncAmt/text()', namespaces=ns) else "Not Available",
                'Avg Hr Per Week (PF)': section.xpath('.//efile:AverageHrsPerWkDevotedToPosRt/text()', namespaces=ns)[0] if section.xpath('.//efile:AverageHrsPerWkDevotedToPosRt/text()', namespaces=ns) else "Not Available",
            }
            individual_data3 = {'Name': name, 'Title': title}
            individual_data3.update(compensation_data3)
            individuals_data3.append(individual_data3)
        #return {'organization_data': organization_data, 'individuals_data': individuals_data, 'individuals_data2': individual_data2}
    #else:
        #return {'organization_data': {}, 'individuals_data': [], 'individuals_data2': []}
        # Combine all individual data
        combined_individuals_data = individuals_data + individuals_data2 + individuals_data3
        unique_individuals = {individual['Name']: individual for individual in combined_individuals_data}.values()

        # Update individual records with merged data
        final_individuals_data = []
        for individual in unique_individuals:
            merged_data = {}
            for dataset in [individuals_data, individuals_data2, individuals_data3]:
                for data in dataset:
                    if data['Name'] == individual['Name']:
                        merged_data.update(data)
            final_individuals_data.append(merged_data)

        return {'organization_data': organization_data, 'individuals_data': final_individuals_data}
    




# Streamlit UI components

def edit_excel_template(data, template_path):
    def to_number(value):
        try:
            return float(value)
        except ValueError:
            return value
    def to_proper_case(text):
        return text.title()
    def format_date(date_str):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%m/%d/%Y")
        except ValueError:
            return date_str
    workbook = openpyxl.load_workbook(template_path)
    sheet = workbook["Form 990 - Position Title"]  # Assumes that the sheet name is "Template"
    sheet2 = workbook["PEER GROUP"]
    #sheet3 = workbook["Form 990F - Position Title"]
    sheet4 = workbook["Form 990PF - Position Title"]
    row = 6
    for entry in data:
        sheet2[f"B{row}"] = to_proper_case(entry["Organization_Name"])
        sheet2[f"C{row}"] = to_number(entry["EIN"])
        sheet2[f"F{row}"] = to_proper_case(entry["City"]) 
        sheet2[f"G{row}"] = entry["State"]
        sheet2[f"E{row}"] = format_date(entry["W2E"])
        sheet2[f"D{row}"] = format_date(entry["Fiscal_Year_End"])
        sheet2[f"H{row}"] = to_number(entry["Total Assets"])
        sheet2[f"I{row}"] = to_number(entry["Total Expenses"])
        sheet2[f"J{row}"] = to_number(entry["Total Revenue"])
        sheet2[f"N{row}"] = to_number(entry["Employee Count"])

        sheet[f"H{row}"] = to_proper_case(entry["Employee_Name"])
        sheet[f"I{row}"] = to_proper_case(entry["Title_Of_Position"])
        sheet[f"P{row}"] = to_number(entry["Base Compensation"])
        sheet[f"T{row}"] = to_number(entry["Deferred Compensation"])
        sheet[f"S{row}"] = to_number(entry["Other Compensation"])
        sheet[f"U{row}"] = to_number(entry["Nontaxable Benefits"])
        #sheet[f"S{row}"] = to_number(entry["Total Compensation"])
        sheet[f"Q{row}"] = to_number(entry["Bonus"])

        #sheet4[f"B{row}"] = to_proper_case(entry["Organization_Name"])
        #sheet4[f"C{row}"] = to_number(entry["EIN"])
        #sheet4[f"F{row}"] = to_proper_case(entry["City"]) 
        #sheet4[f"G{row}"] = entry["State"]
        #sheet4[f"E{row}"] = format_date(entry["W2E"])
        #sheet4[f"D{row}"] = format_date(entry["Fiscal_Year_End"])
        #sheet4[f"J{row}"] = to_number(entry["Total Assets"])
        #sheet4[f"K{row}"] = to_number(entry["Total Expenses"])
        #sheet4[f"J{row}"] = to_number(entry["Total Revenue"])
        #sheet4[f"L{row}"] = to_number(entry["Employee Count"])
        sheet4[f"H{row}"] = to_proper_case(entry["Employee_Name"])
        sheet4[f"I{row}"] = to_proper_case(entry["Title_Of_Position"])
        sheet4[f"O{row}"] = to_number(entry["Reportable Comp PF"])
        sheet4[f"P{row}"] = to_number(entry["Benefits Comp PF"])
        sheet4[f"Q{row}"] = to_number(entry["Expenses and Other Comp PF"])
        
        row += 1
    edited_file = BytesIO()
    workbook.save(edited_file)
    edited_file.seek(0)  # Move the cursor to the start of the stream
    return edited_file

# Streamlit UI components


# Streamlit UI components
# Streamlit UI components
banner_path = 'Horizontal_Banner_NoSC.png'
st.image(banner_path, width=400)
st.header("C3 990 Tool Edit/Upload")
# Mito spreadsheet for EIN input
uploaded_file = st.file_uploader("Upload EIN Excel file", type=["xlsx"])
if uploaded_file:
   excel_data = pd.read_excel(uploaded_file, sheet_name='Sheet1')
   eins = excel_data['EIN'].dropna().astype(str).tolist()
   if eins:
       num_orgs = len(eins)
       st.write(f"Found {num_orgs} EINs in the uploaded file.")
       # Allow user to select years to fetch
       selected_years_option = st.selectbox("Select the year range to fetch data for", ["Most Recent Year", "Most Recent Two Years", "Past Three Years"])
       # Initialize session state variables
       st.session_state['organizations_data'] = []
       st.session_state['all_individuals_data'] = []
       st.session_state['year_data'] = {}
       st.session_state['selected_years'] = {}
       # Initialize year_data for each EIN
       for i in range(num_orgs):
           st.session_state['year_data'][str(i)] = fetch_years(eins[i])
       # Button to confirm year selection and generate the final chart
       if st.button("Generate Final Output Chart"):
           # Fetch data for each EIN with progress indicator
           st.session_state['organizations_data'] = []
           st.session_state['all_individuals_data'] = []
           progress_text = st.empty()
           progress_bar = st.progress(0)
           for i, ein in enumerate(eins):
               try:
                   if ein.strip() and st.session_state['year_data'][str(i)]:
                       years = list(st.session_state['year_data'][str(i)].keys())
                       if selected_years_option == "Most Recent Year":
                           selected_years = [max(years)]
                       elif selected_years_option == "Most Recent Two Years":
                           selected_years = sorted(years, reverse=True)[:2]
                       else:
                           selected_years = sorted(years, reverse=True)[:3]
                       for year in selected_years:
                           st.session_state['selected_years'][str(i)] = year
                           detailed_url = st.session_state['year_data'][str(i)][year][1]
                           fetched_data = fetch_data(ein, detailed_url)
                           st.session_state['organizations_data'].append(fetched_data['organization_data'])
                           st.session_state['all_individuals_data'].append(fetched_data['individuals_data'])
               except Exception as e:
                   st.write(f"Error fetching data for EIN {ein}: {e}")
                   st.session_state['organizations_data'].append({"EIN": ein, "Business Name": "Not Found"})
                   st.session_state['all_individuals_data'].append([])
               # Update progress indicator
               progress = (i + 1) / num_orgs
               progress_bar.progress(progress)
               progress_text.text(f"{i + 1}/{num_orgs} EINs Parsed")
           # Generate final output chart
           final_chart_data = []
           st.session_state['final_chart_data'] = []
           existing_data_identifiers = {(row['EIN'], row['Employee_Name']) for row in st.session_state['final_chart_data']}
           for i, organization_data in enumerate(st.session_state['organizations_data']):
               individuals_data = st.session_state['all_individuals_data'][i]
               # Calculate Total Compensation (PF) for each individual and sort
               for individual_data in individuals_data:
                   try:
                       individual_data['Total Compensation (PF)'] = (
                           float(individual_data.get('Reportable Compensation (PF)', 0)) +
                           float(individual_data.get('Employee Benefit Amount (PF)', 0)) +
                           float(individual_data.get('Other Compensation (PF)', 0))
                       )
                   except Exception as e:
                       individual_data['Total Compensation (PF)'] = 0
                       st.write(f"Error calculating Total Compensation (PF) for {individual_data.get('Name')}: {e}")
                   # Ensure Total Compensation is numeric
                   try:
                       individual_data['Total Compensation'] = float(individual_data.get('Total Compensation', 0))
                   except Exception as e:
                       individual_data['Total Compensation'] = 0
                       st.write(f"Error calculating Total Compensation for {individual_data.get('Name')}: {e}")
               top_individuals = sorted(individuals_data, key=lambda x: x['Total Compensation (PF)'] + x['Total Compensation'], reverse=True)[:5]
               for individual_data in top_individuals:
                   name = individual_data['Name']
                   title = individual_data['Title']
                   if (organization_data.get('EIN'), name) not in existing_data_identifiers:
                       chart_row = {
                           "Organization_Name": organization_data.get('Business Name', 'Unknown'),
                           "EIN": organization_data.get('EIN', 'Not Available'),
                           "W2E": organization_data.get('WYearEnd', 'Not Available'),
                           "Fiscal_Year_End": organization_data.get('Fiscal Year End', 'Not Available'),
                           "City": organization_data.get('City', 'Not Available'),
                           "State": organization_data.get('State', 'Not Available'),
                           "Employee_Name": name,
                           "Title_Of_Position": title,
                           "Total Assets": organization_data.get('Total Assets EOY', 'Not Available'),
                           "Total Expenses": organization_data.get('Total Expenses', 'Not Available'),
                           "Total Revenue": organization_data.get('Total Revenue', 'Not Available'),
                           "Employee Count": organization_data.get('Employee Count', 'Not Available'),
                           "Base Compensation": individual_data.get('Base Compensation', 'Not Available'),
                           "Bonus": individual_data.get('Bonus', 'Not Available'),
                           "Other Compensation": individual_data.get('Other Compensation','Not Available'),
                           "Deferred Compensation": individual_data.get('Deferred Compensation', 'Not Available'),
                           "Nontaxable Benefits": individual_data.get('Nontaxable Benefits', 'Not Available'),
                           "Total Compensation": individual_data.get('Total Compensation', 'Not Available'),
                           "Reportable Comp PF": individual_data.get('Reportable Compensation (PF)', 'Not Available'),
                           "Benefits Comp PF": individual_data.get('Employee Benefit Amount (PF)', 'Not Available'),
                           "Expenses and Other Comp PF": individual_data.get('Other Compensation (PF)', 'Not Available'),
                           "Total Compensation (PF)": individual_data['Total Compensation (PF)']
                       }
                       final_chart_data.append(chart_row)
                       st.session_state['final_chart_data'].append(chart_row)
           final_df = pd.DataFrame(st.session_state['final_chart_data'])
           st.write(final_df)
           if final_chart_data:
               edited_file = edit_excel_template(final_chart_data, '990TemplateNewLg.xlsm')
               st.download_button(label="Download Updated 990 Template", data=edited_file, file_name="990_template.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
# Reset functionality
if st.button("Reset", key='reset_button'):
   st.session_state.clear()
   st.rerun()