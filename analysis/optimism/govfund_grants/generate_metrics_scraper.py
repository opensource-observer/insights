from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from openai import OpenAI
import requests
import time
import json
import re

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-infobars')

driver = webdriver.Chrome(options=chrome_options)

output_path = "grant_metrics.json"

GPT_API_KEY = ''
GPT_PROMPT = """
You are an assistant that extracts key information from grant application texts. Given the text of a grant application and its critical milestones, perform the following tasks:

1. Identify the project name.
2. Extract relevant metrics and their corresponding goals.
   - If a goal for a metric is provided, include it.
   - If a goal is not provided for a metric, set its goal to "N/A".

Structure the output as a JSON object in the following format:

{
    "project_name": "project_name",
    "metrics": {
        "metric1": "goal1",
        "metric2": "goal2",
        ...
    }
}

Ensure that the output is valid JSON without any additional text or explanations.

---

**Grant Application Text:**

<INSERT_GRANT_APPLICATION_TEXT_HERE>

**Critical Milestones:**

<INSERT_CRITICAL_MILESTONES_HERE>
"""


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


def extract_application_info(soup: BeautifulSoup) -> List[Dict[str, str]]:
    text = ""   

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

        text += "Question: " + curr_question + "Answer: " + curr_answer

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
    
    return text, critical_milestones


def extract_metrics(text, critical_milestones):
    client = OpenAI(api_key = GPT_API_KEY)

    prompt = GPT_PROMPT.replace("<INSERT_GRANT_APPLICATION_TEXT_HERE>", text)\
                       .replace("<INSERT_CRITICAL_MILESTONES_HERE>", json.dumps(critical_milestones))

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        response_format = {"type": "json_object"},
    )
    metrics_str = completion.choices[0].message.content
    metrics = json.loads(metrics_str)

    return metrics


def scrape_application(application_url):
    try: 
        driver.get(application_url)

        WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CLASS_NAME, "octo-propertyrow")))
        time.sleep(10)

        html = driver.page_source

        soup = BeautifulSoup(html, "html.parser")

        application_text, critical_milestones = extract_application_info(soup)
        metrics = extract_metrics(application_text, critical_milestones)
        
        print(f"Successfully processed: {application_url}")

        return metrics

    except Exception as e:
        print(f"Failed to scrape {application_url}: {e}")


def main(grant_path, comparator):

    with open(grant_path, 'r') as file:
            gov_grants = json.load(file)

    target_grants = filter_grants(gov_grants, comparator)
    final_metrics = []

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)

    for i, grant in enumerate(target_grants):
        if i > 0 and i % 10 == 0:
            driver.quit()
            driver = webdriver.Chrome(options=chrome_options)

        url = grant['proposal_link']
        if not is_url_valid(url):
            grant_name = grant['project_name'].replace(" ", '_').replace("/", '-').lower()
            print(f"Project {grant_name} - Invalid or inaccessible URL: {url}")
            continue

        metrics = scrape_application(url)
        final_metrics.append(metrics)

    driver.quit()
    
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(final_metrics, output_file, ensure_ascii=False, indent=4)


main('govgrants.json', growth_season_six)