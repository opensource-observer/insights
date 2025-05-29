from bs4 import BeautifulSoup
import json
import time
import threading
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from tqdm import tqdm
import concurrent.futures
import tempfile
import shutil
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/scraper.log'),
        logging.StreamHandler()
    ]
)

URLS_PATH = "data/urls.json"
OUTPUT_DIR = "scraped_data"
WAIT_TIME = 10

def load_urls(path=URLS_PATH, batch_size=10):
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            all_urls = data.get('urls', [])
            scraped_urls = set(data.get('scraped', {}).keys())
            
            # Filter out already scraped URLs
            unscraped_urls = [url for url in all_urls if url not in scraped_urls]
            
            # Return only the first batch_size URLs
            return unscraped_urls[:batch_size]
    except FileNotFoundError:
        logging.warning(f"URLs file not found at {path}, using default URLs")
        return [
            "https://gov.optimism.io/t/gf-phase-0-proposal-uniswap/2133/5",
            "https://gov.optimism.io/t/gf-phase-0-proposal-1inch-network/655",
            "https://gov.optimism.io/t/gf-phase-0-proposal-celer-network/1749",
        ]

def get_total_unscraped():
    try:
        with open(URLS_PATH, 'r') as f:
            data = json.load(f)
            all_urls = data.get('urls', [])
            scraped_urls = set(data.get('scraped', {}).keys())
            return len([url for url in all_urls if url not in scraped_urls])
    except FileNotFoundError:
        return 0

def update_scraped_record(url, filename):
    """Update the scraped record in urls.json"""
    try:
        # Read the current data
        with open(URLS_PATH, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"urls": [], "scraped": {}}
    except json.JSONDecodeError:
        # If the file is corrupted, create a new one
        data = {"urls": [], "scraped": {}}
    
    if "scraped" not in data:
        data["scraped"] = {}
    
    # Update the data
    data["scraped"][url] = filename
    
    # Write to a temporary file first
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
    try:
        json.dump(data, temp_file, indent=4)
        temp_file.close()
        # Move the temporary file to the actual file
        shutil.move(temp_file.name, URLS_PATH)
        logging.info(f"Updated scraped record for {url}")
    except Exception as e:
        logging.error(f"Error updating scraped record: {str(e)}")
        # Clean up the temporary file if something went wrong
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise

def clean_html(soup):
    """Extract text content and hyperlinks from HTML"""
    # Remove script and style elements
    for script in soup(["script", "style", "meta", "link"]):
        script.decompose()
    
    # Create a new soup with just the content we want
    clean_soup = BeautifulSoup('<div class="content"></div>', 'html.parser')
    content_div = clean_soup.find('div', class_='content')
    
    # Process each element
    for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'li']):
        if element.name == 'a':
            # Keep links with their text
            new_element = clean_soup.new_tag('a', href=element.get('href', ''))
            new_element.string = element.get_text(strip=True)
            content_div.append(new_element)
            content_div.append(clean_soup.new_string('\n'))
        else:
            # Keep text content
            text = element.get_text(strip=True)
            if text:
                new_element = clean_soup.new_tag(element.name)
                new_element.string = text
                content_div.append(new_element)
                content_div.append(clean_soup.new_string('\n'))
    
    return clean_soup

def save_data(url, soup):
    """Save the scraped data to a file"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Extract proposal name based on URL type
    if "charmverse.io" in url:
        if "id=" in url:
            # Handle ID-based URLs
            # Example: https://app.charmverse.io/op-grants/proposals?id=628c674f-26c4-4bd0-b667-be7d666b3886
            proposal_id = url.split('id=')[-1]
            filename = f"charmverse-proposal-{proposal_id}.html"
        elif "page-" in url:
            # Handle page URLs
            # Example: https://app.charmverse.io/op-grants/page-15839212306939565
            page_id = url.split('page-')[-1]
            filename = f"charmverse-page-{page_id}.html"
        else:
            # Handle slug-based URLs
            # Example: https://app.charmverse.io/op-grants/fluid-dex-on-base-12731267690074222
            proposal_slug = url.split('/')[-1]
            filename = f"charmverse-proposal-{proposal_slug}.html"
    elif "gov.optimism.io" in url:
        # For Optimism governance forum URLs
        # Example: https://gov.optimism.io/t/gf-phase-0-proposal-uniswap/2133/5
        proposal_name = url.split('/t/')[-1].split('/')[0]
        filename = f"{proposal_name}.html"
    else:
        # For external URLs
        # Example: http://li.fi/
        domain = url.split('://')[-1].split('/')[0]
        filename = f"external-{domain}.html"
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Clean the HTML before saving
    clean_soup = clean_html(soup)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(clean_soup))
    logging.info(f"Saved cleaned data to {filepath}")
    
    # Update the scraped record
    update_scraped_record(url, filename)

def scrape_website(url):
    """Scrape a single website and save the results"""
    logging.info(f"Starting scrape for {url}")
    try:
        options = Options()
        options.headless = True
        logging.info("Initializing Chrome driver...")
        driver = webdriver.Chrome(options=options)
        logging.info(f"Navigating to {url}")
        driver.get(url)
        logging.info(f"Waiting {WAIT_TIME} seconds for page load...")
        time.sleep(WAIT_TIME)
        logging.info("Parsing page content...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        logging.info("Closing Chrome driver...")
        driver.quit()
        
        save_data(url, soup)
        logging.info(f"Successfully scraped {url}")
        return True
    except WebDriverException as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error scraping {url}: {str(e)}")
        return False

def main():
    start_time = time.time()
    total_unscraped = get_total_unscraped()
    
    if total_unscraped == 0:
        logging.info("No URLs left to scrape!")
        return

    logging.info(f"Starting batch scraping process. Total URLs to scrape: {total_unscraped}")
    
    # Create progress bar for overall progress
    with tqdm(total=total_unscraped, desc="Overall Progress") as pbar:
        batch_num = 1
        total_scraped = 0

        while True:
            urls = load_urls(batch_size=10)
            if not urls:
                break

            # Create progress bar for current batch
            with tqdm(total=len(urls), desc=f"Batch {batch_num}", leave=False) as batch_pbar:
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    # Submit all URLs to the thread pool
                    future_to_url = {executor.submit(scrape_website, url): url for url in urls}
                    
                    # Process completed futures
                    for future in concurrent.futures.as_completed(future_to_url):
                        url = future_to_url[future]
                        try:
                            success = future.result()
                            if success:
                                total_scraped += 1
                                pbar.update(1)
                            batch_pbar.update(1)
                        except Exception as e:
                            logging.error(f"Error processing {url}: {str(e)}")
                            batch_pbar.update(1)

            batch_num += 1

    end_time = time.time()
    logging.info(f"All batches completed in {end_time - start_time:.2f} seconds")
    logging.info(f"Total URLs scraped: {total_scraped}")

if __name__ == "__main__":
    main()