import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Optional
import google.generativeai as genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

def load_oso_projects() -> List[Dict]:
    """Load OSO projects from JSON file."""
    with open('data/oso_projects.json', 'r') as f:
        return json.load(f)

def match_project(project_name: str, html_content: str, oso_projects: List[Dict]) -> str:
    """Use Gemini to match a project with OSO projects."""
    
    valid_slugs = [project['oso_slug'] for project in oso_projects] + ['unknown']

    # Prepare context for Gemini
    context = f"""
    SYSTEM:
    You are an expert matcher.  Given a project application, a list of valid OSO slugs,
    and details about OSO projects (description, urls), select exactly one slug or "unknown."
    Do NOT hallucinate or invent slugs.  Output only a single JSON object with the key "oso_slug."
    Do NOT include any markdown formatting or code blocks in your response.

    USER:
    Project to match:
    Name: {project_name}

    Full project application content (HTML):
    {html_content}

    Valid OSO slugs:
    {json.dumps(valid_slugs)}

    Details OSO projects:
    {json.dumps(oso_projects, indent=2)}

    Return exactly one JSON object:
    {{"oso_slug": "<one_of_valid_slugs_or_unknown>"}}
    """
    
    try:
        response = model.generate_content(context)
        response_text = response.text.strip()
        
        # Remove any markdown code block formatting
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        # Parse the JSON response
        result = json.loads(response_text)
        return result['oso_slug']
    except Exception as e:
        print(f"Error matching project {project_name}: {e}")
        return "unknown"

def process_projects(batch_size: int = 10):
    """Process projects in batches and save results regularly."""
    # Load OSO projects
    oso_projects = load_oso_projects()
    
    # Load project HTML mapping
    projects = []
    with open('data/project_html.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['project_name'] and row['html']:  # Skip empty rows
                projects.append(row)
    
    # Create or load results file
    results_file = 'data/project_matches.csv'
    existing_matches = {}
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle both old and new column names
                project_name = row.get('project_name') or row.get('Project Name')
                if project_name:
                    existing_matches[project_name] = row['oso_slug']
    
    # Process projects in batches
    for i in range(0, len(projects), batch_size):
        batch = projects[i:i + batch_size]
        
        for project in batch:
            if project['project_name'] in existing_matches:
                continue
                
            print(f"Processing {project['project_name']}...")
            
            # Read HTML file
            html_path = Path('scraped_data') / project['html']
            if not html_path.exists():
                print(f"Warning: HTML file not found for {project['project_name']}")
                continue
                
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            oso_slug = match_project(project['project_name'], html_content, oso_projects)
            
            # Save result
            existing_matches[project['project_name']] = oso_slug
            
            # Save to CSV after each project
            with open(results_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['project_name', 'html', 'oso_slug'])
                writer.writeheader()
                for proj_name, slug in existing_matches.items():
                    # Find the corresponding HTML file
                    html_file = next((p['html'] for p in projects if p['project_name'] == proj_name), '')
                    writer.writerow({
                        'project_name': proj_name,
                        'html': html_file,
                        'oso_slug': slug
                    })
            
            # Add small delay to avoid rate limits
            time.sleep(1)
        
        print(f"Completed batch {i//batch_size + 1}")

if __name__ == "__main__":
    process_projects()
