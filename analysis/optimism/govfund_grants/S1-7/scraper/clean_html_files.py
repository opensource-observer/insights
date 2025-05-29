from bs4 import BeautifulSoup
import os
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/cleaner.log'),
        logging.StreamHandler()
    ]
)

OUTPUT_DIR = "scraped_data"

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

def process_html_file(filepath):
    """Process a single HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Clean the HTML
        clean_soup = clean_html(soup)
        
        # Save the cleaned HTML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(clean_soup))
        
        return True
    except Exception as e:
        logging.error(f"Error processing {filepath}: {str(e)}")
        return False

def main():
    if not os.path.exists(OUTPUT_DIR):
        logging.error(f"Directory {OUTPUT_DIR} does not exist!")
        return

    # Get list of HTML files
    html_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.html')]
    total_files = len(html_files)
    
    if total_files == 0:
        logging.info("No HTML files found to process!")
        return

    logging.info(f"Found {total_files} HTML files to process")
    
    # Process files with progress bar
    successful = 0
    with tqdm(total=total_files, desc="Cleaning HTML files") as pbar:
        for filename in html_files:
            filepath = os.path.join(OUTPUT_DIR, filename)
            if process_html_file(filepath):
                successful += 1
            pbar.update(1)
    
    logging.info(f"Successfully cleaned {successful} out of {total_files} files")

if __name__ == "__main__":
    main() 