import json
import requests


url = 'https://www.fil-retropgf.io/api/trpc/projects.search?input=%7B%22json%22%3A%20%7B%22limit%22%3A%201000%7D%7D'
response = requests.get(url)
data = response.json()
projects = data['result']['data']['json']

for p in projects:
    r = requests.get(p['metadataPtr'])
    app = json.loads(r.content)
    p.update({'app': app})

with open("data/FIL_RetroPGF1_applications.json", "w") as f:
    json.dump(projects, f, indent=2)