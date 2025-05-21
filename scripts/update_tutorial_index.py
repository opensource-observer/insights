import argparse, os, re, pathlib, textwrap, requests
from google import genai

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mdx-dir",   default="mdx_build/apps/docs/docs/tutorials")
    p.add_argument("--index-url", default="https://raw.githubusercontent.com/opensource-observer/oso/refs/heads/main/apps/docs/docs/tutorials/index.md")
    p.add_argument("--index-path",default="mdx_build/apps/docs/docs/tutorials/index.md")
    return p.parse_args()

def download_index(url, dest, pat):
    hdrs = {"Authorization": f"token {pat}", "Accept": "application/vnd.github.raw"}
    r = requests.get(url, headers=hdrs, timeout=30)
    r.raise_for_status()
    pathlib.Path(dest).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(dest).write_bytes(r.content)
    return r.text

def execute_query(client, link, existing_titles):
    prompt = textwrap.dedent(f"""
        You are updating an **index.md** file that lists OSO data-science tutorials.
        Each line follows this exact pattern:

        - <emoji> [<Title in Title Case>](./<file>.mdx) - <short plain-English description>

        ### Existing examples
        - 🌱 [Quickstart](./quickstart.md) - Learn the basics of pyoso and common query patterns for our most popular models
        - 📊 [Collection View](./collection-view.mdx) - Get a high level view of key metrics for a collection of projects
        - 🔬 [Project Deepdive](./project-deepdive.mdx) - Do a deep dive into a specific project
        - 📦 [Map Dependencies](./dependencies.mdx) - Map software supply chains and package dependencies
        - 🕸️ [Network Graphs](./network-graph.md) - Analyze collaboration patterns and community connections
        - 💸 [Analyze Funding](./funding-data.mdx) - Track funding flows and analyze grant program impact
        - 👥 [Cohort Analysis](./cohort-analysis.mdx) - Track a cohort of projects across a set of metrics over time

        ### Your task
        Generate **exactly ONE** new bullet for the tutorial file **`{link}`**.

        **Rules**
        1. **Format** must match the pattern above, including the dash, emoji, link, and hyphenated description.
        2. **Emoji** should be relevant, unique, and not reuse emojis from existing bullets if possible.
        3. **Title**
            • Title Case (capitalize major words).  
            • 1-4 words, broad and memorable.  
            • Must not duplicate any existing title ({', '.join(sorted(existing_titles))}).
        4. **Description**
            • 10-15 words.  
            • Plain English, non-technical, user-focused (“Learn to…”, “Explore…”, “Visualize…”, etc.).  
            • Sentence case (only first letter capitalized).
        5. Output **only** the bullet line—no extra text.

        Produce your answer now:
    """)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.parsed

def main():
    args = parse_args()
    pat = os.environ["TARGET_PAT"]
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    index_text = download_index(args.index_url, args.index_path, pat)
    existing_titles = set(re.findall(r'\] \- (.*?)$', index_text, flags=re.M))
    existing_links  = set(re.findall(r'\((.*?)\)',      index_text))

    new_bullets = []
    for mdx in pathlib.Path(args.mdx_dir).glob("*.mdx"):
        link = f"./{mdx.name}"
        if link in existing_links:
            continue
        bullet = execute_query(client, link, existing_titles)
        if bullet:
            new_bullets.append(bullet)

    if not new_bullets:
        print("No new bullets to insert.")
        return

    # ensure that new bullets are inserted above "(coming soon)" bullets
    insertion_point = None
    lines = index_text.splitlines()
    for i,l in enumerate(lines):
        if "(coming soon)" in l:
            insertion_point = i
            break
    if insertion_point is None:
        insertion_point = len(lines)

    print(lines[:insertion_point], new_bullets, lines[insertion_point:])
    updated_text = "\n".join(lines[:insertion_point] +
                             new_bullets +
                             lines[insertion_point:])

    pathlib.Path(args.index_path).write_text(updated_text, encoding="utf-8")
    print(f"Inserted {len(new_bullets)} bullet(s) into index.md")

if __name__ == "__main__":
    main()
