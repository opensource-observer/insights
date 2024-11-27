from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import requests
import time
import json
import re
import os

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-infobars')

driver = webdriver.Chrome(options=chrome_options)

output_path = "data/proposals"

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


def extract_target_info(grant, extracted_list, critical_milestones) -> Dict[str, str]:
    questions = [element['q'].lower().replace(":", "") for element in extracted_list]
    
    grant['l2_addresses'] = extracted_list[questions.index("l2 recipient address")]['a'] if "l2 recipient address" in questions else "N/A"

    metric_questions = [question for question in questions if ("metric" in question or "objective" in question) or (question == "impact analysis")]
    metrics = {}
    for metric_question in metric_questions:
        metrics[metric_question] = extracted_list[questions.index(metric_question)]['a']
    grant['relevant_metrics'] = metrics

    date_headers = [header for header in critical_milestones['headers'] if "date" in header.lower()]
    dates = {}
    for date_header in date_headers:
        date_index = critical_milestones['headers'].index(date_header)
        dates[date_header] = []
        for row in critical_milestones['rows']:
            dates[date_header].append(row[date_index])

        dates[date_header] = list(set(dates[date_header]))
    grant['relevant_dates'] = dates

    #op_deployment_date_index, incentives_due_date_index = critical_milestones['headers'].index('op_deployment_date'), critical_milestones['headers'].index('incentives_due_date')
    #relevant_dates = {'op_deployment_date': [], 'incentives_due_date': []}
    #for row in critical_milestones['rows']:
    #    relevant_dates['op_deployment_date'].append(row[op_deployment_date_index])
    #    relevant_dates['incentives_due_date'].append(row[incentives_due_date_index])

    #relevant_dates['op_deployment_date'] = list(set(relevant_dates['op_deployment_date']))
    #relevant_dates['incentives_due_date'] = list(set(relevant_dates['incentives_due_date']))
    #grant['relevant_dates'] = relevant_dates

    if "full list of the project’s labeled contracts" in questions:
        extracted_addresses_and_chains = extract_addresses_and_chains(extracted_list[questions.index("full list of the project’s labeled contracts")]['a'])
        if extracted_addresses_and_chains:
            grant['contract_addresses'] = extracted_addresses_and_chains['contract_addresses'] if 'contract_addresses' in extracted_addresses_and_chains.keys() and extracted_addresses_and_chains['contract_addresses'] else 'N/A'
            grant['relevant_chains'] = extracted_addresses_and_chains['chains_mentioned'] if 'chains_mentioned' in extracted_addresses_and_chains.keys() and extracted_addresses_and_chains['chains_mentioned'] else 'N/A'
            grant['contract_urls'] = extracted_addresses_and_chains['contract_urls'] if 'contract_urls' in extracted_addresses_and_chains.keys() and extracted_addresses_and_chains['contract_urls'] else 'N/A'

    return grant


def extract_application_info(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Extracts application information from a BeautifulSoup object.

    This function scrapes data from a parsed HTML document and organizes it into a dictionary. 
    It captures details such as contact information, grant requests, milestones, and other sections.

    :param soup: BeautifulSoup object containing the parsed HTML of the page.
    :return: A dictionary containing the scraped application information.
    """
    out = []   

    question_selectors = [
        {'tag': 'p', 'class_': 'MuiTypography-root MuiTypography-body1 css-3vrlul', 'out': 'text'}
    ]

    answer_selectors = [
        {'tag': 'div', 'class_': 'MuiInputBase-root MuiOutlinedInput-root MuiInputBase-colorPrimary Mui-disabled MuiInputBase-fullWidth MuiInputBase-sizeSmall css-19odyoo', 'out': 'text'},
        {'tag': 'div', 'class_': 'MuiStack-root css-17or55h', 'out': 'text'},
        {'tag': 'input', 'class_': 'MuiInputBase-input MuiOutlinedInput-input Mui-disabled MuiInputBase-inputSizeSmall css-8ks90l', 'out': 'value'},
        {'tag': 'div', 'class_': 'css-1m71jyw', 'out': 'text'},
        {'tag': 'span', 'class_': 'MuiChip-label MuiChip-labelSmall css-b9zgoq', 'out': 'text'}
    ]

    content = soup.find_all("div", class_='MuiStack-root proposal-form-field-answer css-lpl635')

    for i, c in enumerate(content):
        curr_question, curr_answer = "N/A", "N/A"

        for selector in question_selectors:
            element = c.find(selector['tag'], class_=selector['class_'])
            if element:
                if selector['out'] == 'text':
                    curr_question = element.get_text(separator=" ", strip=True)
                    curr_question = re.sub(r'[\u200b\u00a0]', '', curr_question)
                break

        for selector in answer_selectors:
            element = c.find(selector['tag'], class_=selector['class_'])
            if element:
                try:
                    curr_answer = element.get_text(separator=" ", strip=True) if selector['out'] == 'text' else element['value']
                    curr_answer = re.sub(r'[\u200b\u00a0]', '', curr_answer)
                except (AttributeError, KeyError):
                    curr_answer = "N/A"
                break

        if curr_question == "N/A":
            continue

        if curr_question.endswith(" *"):
            curr_question = curr_question[:-2]

        out.append({'q': curr_question, 'a': curr_answer})

    out = out[:-1]

    critical_milestones = {}

    table = soup.find("div", class_="Table")

    headers = table.find_all("div", class_='octo-table-cell header-cell disable-drag-selection')
    headers = [header.get_text(separator=" ", strip=True) for header in headers]
    headers = [re.sub(r'[\u200b\u00a0]', '', header) for header in headers]
    critical_milestones['headers'] = headers[:-1]

    rows = table.find_all("div", class_="TableRow")
    row_contents = []
    for i, row in enumerate(rows):
        cells = row.find_all("div", class_="octo-table-cell")
        cell_contents = []
        for cell in cells:
            try:
                c = cell.find("input", class_="MuiInputBase-input Mui-readOnly Editable readonly octo-propertyvalue MuiInputBase-readOnly css-1i2cby2")['value']
                c = re.sub(r'[\u200b\u00a0]', '', c)
            except (AttributeError, TypeError, KeyError):
                c = cell.get_text(separator=" ", strip=True) if cell else "N/A"
                c = re.sub(r'[\u200b\u00a0]', '', c)
            cell_contents.append(c)

        row_contents.append(cell_contents[:-1])
    critical_milestones['rows'] = row_contents
    
    return out, critical_milestones


def fill_template(output_path: str, extracted_data: List[Dict[str, str]], critical_milestones: Dict[str, List[str]], project_name: str, project_url: str) -> None:
    """
    Creates a Markdown file with project details, extracted questions and answers, and critical milestones.

    :param output_path: Path to save the generated Markdown file.
    :param extracted_data: List of dictionaries where 'q' represents the question and 'a' represents the answer.
    :param critical_milestones: Dictionary containing 'headers' (list of column headers) and 'rows' (list of milestone rows).
    :param project_name: Name of the project.
    :param project_url: URL of the project.
    """
    # Start building the Markdown content
    markdown_content = f"# {project_name}\n\n"
    markdown_content += f"**Project URL:** [Link]({project_url})\n\n"
    
    # Add questions and answers
    for item in extracted_data:
        question = item.get('q', 'N/A')
        answer = item.get('a', 'N/A')
        markdown_content += f"**{question}**\n\n{answer}\n\n"
    
    # Add critical milestones
    if critical_milestones:
        markdown_content += "## Critical Milestones\n\n"
        headers = critical_milestones.get('headers', [])
        rows = critical_milestones.get('rows', [])
        
        if headers and rows:
            for row in rows:
                milestone_details = [f"**{header}:** {row[i]}" for i, header in enumerate(headers)]
                markdown_content += "- " + "; ".join(milestone_details) + "\n"
        else:
            markdown_content += "No critical milestones available.\n"
    
    # Write the content to the output file
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(markdown_content)

    print(f"Markdown file saved to '{output_path}'")


def scrape_application(grant, application_url, output_path, project_name):
    try: 
        driver.get(application_url) # Open the page

        # Wait for the page to fully load a key element
        WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CLASS_NAME, "octo-propertyrow")))
        time.sleep(10)

        html = driver.page_source # Get the rendered HTML
        # driver.quit() # Close the browser

        # Parse the rendered HTML with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        extracted_data, critical_milestones = extract_application_info(soup)
        fill_template(output_path, extracted_data, critical_milestones, project_name, application_url)
        extracted_table_info = extract_target_info(grant, extracted_data, critical_milestones)
        
        print(f"Successfully processed: {application_url}")

        return extracted_table_info

    except Exception as e:
        print(f"Failed to scrape {application_url}: {e}")


def main(grant_path, output_path, comparator):

    with open(grant_path, 'r') as file:
            gov_grants = json.load(file)

    target_grants = filter_grants(gov_grants, comparator)
    final_grants = []

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_path = os.path.join(output_path, f"s6_growth_{timestamp}.md")
    os.makedirs(output_path)

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)

    for i, grant in enumerate(target_grants):
        if i > 0 and i % 10 == 0:
            driver.quit()
            driver = webdriver.Chrome(options=chrome_options)

        project_name = grant['project_name']
        grant_name = project_name.replace(" ", '_').replace("/", '-').lower()
        url = grant['proposal_link']

        if not is_url_valid(url):
            print(f"Project {grant_name} - Invalid or inaccessible URL: {url}")
            continue

        grant_output_path = os.path.join(output_path, f"{grant_name}.md")

        extracted_table_info = scrape_application(grant, url, grant_output_path, project_name)

        final_grants.append(extracted_table_info)

    driver.quit()

    final_grants_path = os.path.join(output_path, f"updated_grants.json")
    with open(final_grants_path, "w", encoding="utf-8") as output_file:
        json.dump(final_grants, output_file, ensure_ascii=False, indent=4)

#scrape_application(g, 'https://app.charmverse.io/op-grants/derive-formerly-lyra-chain-intent-3b-9106030612947877', 'temp.md', 'temp')

main('govgrants.json', output_path, growth_season_six)