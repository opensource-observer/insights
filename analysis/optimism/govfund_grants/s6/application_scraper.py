from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from typing import Dict, Any
import requests
import time
import json
import re
import os


# Path to your ChromeDriver
template_path = "data/application_template.md"
output_path = "data/proposals"

# Set up Selenium WebDriver
driver = webdriver.Chrome()

# Define relevant OP Chains
op_chains = [
    "zora", "base", "mode", "pontem", "lisk", "metal", "mint", "xterio",
    "polynomial", "race", "worldchain", "shape", "campaign", "ozean", "soneium", "op",
    "fraxtal", "redstone", "cyber", "kroma", "ham", "swan", "boba", "lyra",
    "orderly", "bob", "donatuz", "celol2", "gameswift", "arenaz_nodgames", "thebinaryholdings", "automata",
    "funki", "ethernity", "metis", "hypr", "aevo", "loot chain", "rollux", "mantle",
    "pgn", "manta_pacific", "opbnb", "syndicate_frame", "ancient8", "goldchain", "karak", "blast",
    "stack", "rss3", "lambda", "optopia", "ethxy", "matchain", "zircuit", "debank",
    "superseed", "vienna", "curio", "giant_leap_gaming", "unidex_molten", "stealthchain", "foam space", "zentachain",
    "rise", "axonum", "form", "myshell", "allo", "fractal", "unite", "hemi",
    "nal", "clique", "unichain", "ink", "odyssey", "swell"
]


def growth_season_six(grant):
    return grant['round'] == 'Grants Season 6' and grant['meta']['Incentive Program Launched?'] == 'Growth'


def filter_grants(gov_grants, comparator):
    target_grants = []
    
    for grant in gov_grants:
        if comparator(grant):
            target_grants.append(grant)

    return target_grants


def is_url_valid(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def extract_application_info(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extracts application information from a BeautifulSoup object.

    This function scrapes data from a parsed HTML document and organizes it into a dictionary. 
    It captures details such as contact information, grant requests, milestones, and other sections.

    :param soup: BeautifulSoup object containing the parsed HTML of the page.
    :return: A dictionary containing the scraped application information.
    """
    out = {}    

    tag_group_1 = soup.find_all("div", class_="MuiInputBase-input MuiOutlinedInput-input Mui-disabled MuiInputBase-inputMultiline MuiInputBase-inputSizeSmall MuiBox-root css-9v42dl")
    out['email'] = tag_group_1[0].get_text(separator=" ", strip=True) if tag_group_1 else 'N/A'
    out['telegram'] = tag_group_1[1].get_text(separator=" ", strip=True) if tag_group_1 and len(tag_group_1) > 1 else 'N/A'
    out['x_handle'] = tag_group_1[2].get_text(separator=" ", strip=True) if tag_group_1 and len(tag_group_1) > 2 else 'N/A'
    out['discord'] = tag_group_1[3].get_text(separator=" ", strip=True) if tag_group_1 and len(tag_group_1) > 3 else 'N/A'
    out['demo'] = tag_group_1[4].get_text(separator=" ", strip=True) if tag_group_1 and len(tag_group_1) > 4 else 'N/A'
    out['other'] = tag_group_1[5].get_text(separator=" ", strip=True) if tag_group_1 and len(tag_group_1) > 5 else 'N/A'
    address = tag_group_1[6].get_text(separator=" ", strip=True) if tag_group_1 and len(tag_group_1) > 6 else 'N/A'
    out['spending_confirmation'] = tag_group_1[7].get_text(separator=" ", strip=True) if tag_group_1 and len(tag_group_1) > 7 else 'N/A'
    out['metric_objective'] = tag_group_1[8].get_text(separator=" ", strip=True) if tag_group_1 and len(tag_group_1) > 8 else 'N/A'
    out['grant_as_a_service_provider'] = tag_group_1[9].get_text(separator=" ", strip=True) if tag_group_1 and len(tag_group_1) > 9 else 'N/A'
    out['contributions_from_non_team_members'] = tag_group_1[10].get_text(separator=" ", strip=True) if tag_group_1 and len(tag_group_1) > 10 else 'N/A'

    tag_group_2 = soup.find_all("input", class_="MuiInputBase-input MuiOutlinedInput-input Mui-disabled MuiInputBase-inputSizeSmall css-8ks90l", attrs={"placeholder": "Enter a number"})
    out['op_request_locked'] = tag_group_2[0]['value'] if tag_group_2 else 'N/A'
    out['op_request_user_incentives'] = tag_group_2[1]['value'] if len(tag_group_2) > 1 else 'N/A'

    tag_group_3 = soup.find_all("input", class_="MuiInputBase-input MuiOutlinedInput-input Mui-disabled MuiInputBase-inputSizeSmall MuiInputBase-inputAdornedStart MuiInputBase-inputAdornedEnd MuiAutocomplete-input MuiAutocomplete-inputFocused css-1ra0c3x")
    network = tag_group_3[0]['value'] if tag_group_3 else 'N/A'
    
    out['l2_recipient_address'] = {network: address}

    tag_group_4 = soup.find_all("span", class_="MuiChip-label MuiChip-labelSmall css-b9zgoq")
    out['mission_request_metric'] = tag_group_4[0].get_text(separator=" ", strip=True) if tag_group_4 else 'N/A'
    out['compliance_1'] = tag_group_4[1].get_text(separator=" ", strip=True) if tag_group_4 and len(tag_group_4) > 1 else 'N/A'
    out['compliance_2'] = tag_group_4[2].get_text(separator=" ", strip=True) if tag_group_4 and len(tag_group_4) > 2 else 'N/A'
    out['compliance_3'] = tag_group_4[3].get_text(separator=" ", strip=True) if tag_group_4 and len(tag_group_4) > 3 else 'N/A'
    out['compliance_4'] = tag_group_4[4].get_text(separator=" ", strip=True) if tag_group_4 and len(tag_group_4) > 4 else 'N/A'

    tag_group_5 = soup.find_all("div", class_="ProseMirror bangle-editor")
    out['resubmission_explanation'] = tag_group_5[6].get_text(separator=" ", strip=True) if tag_group_5 and len(tag_group_5) > 6 else 'N/A'
    out['code_audit'] = tag_group_5[7].get_text(separator=" ", strip=True) if tag_group_5 and len(tag_group_5) > 7 else 'N/A'
    out['project_explanation'] = tag_group_5[9].get_text(separator=" ", strip=True) if tag_group_5 and len(tag_group_5) > 9 else 'N/A'
    out['market_analysis'] = tag_group_5[11].get_text(separator=" ", strip=True) if tag_group_5 and len(tag_group_5) > 11 else 'N/A'
    out['grant_impact'] = tag_group_5[13].get_text(separator=" ", strip=True) if tag_group_5 and len(tag_group_5) > 13 else 'N/A'
    out['labeled_contracts'] = tag_group_5[15].get_text(separator=" ", strip=True) if tag_group_5 and len(tag_group_5) > 15 else 'N/A'
    out['budget_and_plan'] = tag_group_5[19].get_text(separator=" ", strip=True) if tag_group_5 and len(tag_group_5) > 19 else 'N/A'
    out['optimism_relationship'] = tag_group_5[21].get_text(separator=" ", strip=True) if tag_group_5 and len(tag_group_5) > 21 else 'N/A'

    tag_group_6 = soup.find_all("textarea", class_="MuiInputBase-input MuiInputBase-inputMultiline Mui-readOnly Editable readonly octo-propertyvalue MuiInputBase-readOnly css-avbc5r")
    tag_group_7 = soup.find_all("input", class_="MuiInputBase-input Mui-readOnly Editable readonly octo-propertyvalue MuiInputBase-readOnly css-1i2cby2")
    tag_group_8 = soup.find_all("div", class_="octo-propertyvalue readonly MuiBox-root css-1t8wpoj")

    critical_milestones = []
    rows = soup.find_all("div", class_="TableRow")
    for i, row in enumerate(rows):
        curr_milestone = {}
        
        curr_milestone['milestone_type'] = tag_group_4[i+5].get_text(separator=" ", strip=True) if tag_group_4 and len(tag_group_4) > i+5 else 'N/A'
        curr_milestone['op_tokens_request'] = tag_group_4[i+6].get_text(separator=" ", strip=True) if tag_group_4 and len(tag_group_4) > i+6 else 'N/A'
        curr_milestone['cycle'] = tag_group_4[i+7].get_text(separator=" ", strip=True) if tag_group_4 and len(tag_group_4) > i+7 else 'N/A'
        curr_milestone['completed'] = tag_group_4[i+8].get_text(separator=" ", strip=True) if tag_group_4 and len(tag_group_4) > i+8 else 'N/A'
        curr_milestone['title'] = tag_group_6[0].get_text(separator=" ", strip=True) if tag_group_6 else 'N/A'
        curr_milestone['source_of_truth'] = tag_group_7[0]['value'] if tag_group_7 else 'N/A'
        curr_milestone['op_amount'] = tag_group_7[1]['value'] if tag_group_7 and len(tag_group_7) > 1 else 'N/A'
        curr_milestone['op_deployment_date'] = tag_group_8[0].get_text(separator=" ", strip=True) if tag_group_8 else 'N/A'
        curr_milestone['incentives_due_date'] = tag_group_8[1].get_text(separator=" ", strip=True) if tag_group_8 and len(tag_group_8) > 1 else 'N/A'
        
        critical_milestones.append(curr_milestone)

    out['critical_milestones'] = critical_milestones

    return out


def fill_template(template_path: str, output_path: str, data: Dict[str, Any], project_name: str, project_url: str) -> None:
    """
    Reads the template Markdown file, fills placeholders with data, and saves the completed file with improved formatting.

    :param template_path: Path to the Markdown template file with placeholders.
    :param output_path: Directory where the filled Markdown file will be saved.
    :param data: Dictionary containing the scraped data, including nested dictionaries if applicable.
    """
    # Read and process the template
    with open(template_path, "r", encoding="utf-8") as template_file:
        template_content = template_file.read()

    # Replace placeholders with properly formatted data
    for key, value in data.items():
        if isinstance(value, dict):  # Handle nested dictionaries
            # Format nested content with indents for readability
            nested_content = "\n".join(f"    - **{k}:** {v}" for k, v in value.items())
            formatted_value = f"\n{nested_content}" if nested_content else "N/A"
        elif isinstance(value, list):  # Handle lists
            formatted_value = "\n".join(f"    - {item}" for item in value) if value else "N/A"
        else:  # Handle simple strings
            formatted_value = str(value) if value else "N/A"

        # Replace the placeholder in the template
        template_content = template_content.replace(f"{{{key}}}", formatted_value)

    template_content = template_content.replace("{project_name}", project_name).replace("{project_url}", project_url)

    # Write the formatted content to the uniquely named output file
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(template_content)

    print(f"Filled template saved to '{output_path}'")


def scrape_application(application_url, output_path, project_name):
    try: 
        driver.get(application_url) # Open the page

        # Wait for the page to fully load a key element
        WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CLASS_NAME, "octo-propertyrow")))
        time.sleep(10)

        html = driver.page_source # Get the rendered HTML
        # driver.quit() # Close the browser

        # Parse the rendered HTML with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        extracted_data = extract_application_info(soup)
        fill_template(template_path, output_path, extracted_data, project_name, application_url)
        print(f"Successfully processed: {application_url}")

        return extracted_data

    except Exception as e:
        print(f"Failed to scrape {application_url}: {e}")


def extract_addresses_and_chains(text):
    # Regex to extract contract addresses and urls pointing to contracts
    contract_address_pattern = r"0x[a-fA-F0-9]{40}"
    contract_urls_pattern = r"https?://[^\s]+"

    # Regex for finding op chain names
    op_chain_pattern = r"\b(" + "|".join(re.escape(chain) for chain in op_chains) + r")\b"

    # Extracting contract addresses and urls
    contract_addresses = re.findall(contract_address_pattern, text)
    contract_urls = re.findall(contract_urls_pattern, text)

    # Extracting op chain names
    chains_mentioned = re.findall(op_chain_pattern, text, re.IGNORECASE)
    chains_mentioned = list(set(chains_mentioned))  # Remove duplicates

    return {
        "contract_addresses": contract_addresses,
        "contract_urls": contract_urls,
        "chains_mentioned": chains_mentioned
    }


def main(grant_path, output_path, comparator):

    with open(grant_path, 'r') as file:
            gov_grants = json.load(file)

    target_grants = filter_grants(gov_grants, comparator)
    final_grants = []

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_path = os.path.join(output_path, f"s6_growth_{timestamp}.md")
    os.makedirs(output_path)

    for grant in target_grants:
        project_name = grant['project_name']
        grant_name = project_name.replace(" ", '_').replace("/", '-').lower()
        url = grant['proposal_link']

        if not is_url_valid(url):
            print(f"Project {grant_name} - Invalid or inaccessible URL: {url}")
            continue

        grant_output_path = os.path.join(output_path, f"{grant_name}.md")

        extracted_data = scrape_application(url, grant_output_path, project_name)

        if extracted_data:
            grant['relevant_dates'] = {'op_deployment': list(set([e['op_deployment_date'] for e in extracted_data['critical_milestones']])) if 'critical_milestones' in extracted_data.keys() and extracted_data['critical_milestones'] else 'N/A', 
                                    'incentives_due': list(set([e['incentives_due_date'] for e in extracted_data['critical_milestones']])) if 'critical_milestones' in extracted_data.keys() and extracted_data['critical_milestones'] else 'N/A'}
            grant['relevant_metrics'] = {'mission_request_metric': extracted_data['mission_request_metric'] if 'mission_request_metric' in extracted_data.keys() and extracted_data['mission_request_metric'] else 'N/A', 
                                        'metric_objective': extracted_data['metric_objective'] if 'metric_objective' in extracted_data.keys() and extracted_data['metric_objective'] else 'N/A'}
            grant['l2_addresses'] = extracted_data['l2_recipient_address'] if 'l2_recipient_address' in extracted_data.keys() and extracted_data['l2_recipient_address'] else 'N/A'

            extracted_addresses_and_chains = extract_addresses_and_chains(extracted_data['labeled_contracts'])
            if extracted_addresses_and_chains:
                grant['contract_addresses'] = extracted_addresses_and_chains['contract_addresses'] if 'contract_addresses' in extracted_addresses_and_chains.keys() and extracted_addresses_and_chains['contract_addresses'] else 'N/A'
                grant['relevant_chains'] = extracted_addresses_and_chains['chains_mentioned'] if 'chains_mentioned' in extracted_addresses_and_chains.keys() and extracted_addresses_and_chains['chains_mentioned'] else 'N/A'
                grant['contract_urls'] = extracted_addresses_and_chains['contract_urls'] if 'contract_urls' in extracted_addresses_and_chains.keys() and extracted_addresses_and_chains['contract_urls'] else 'N/A'

        final_grants.append(grant)

    driver.quit()

    final_grants_path = os.path.join(output_path, f"updated_grants.json")
    with open(final_grants_path, "w", encoding="utf-8") as output_file:
        json.dump(final_grants, output_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main('data/govgrants.json', output_path, growth_season_six)