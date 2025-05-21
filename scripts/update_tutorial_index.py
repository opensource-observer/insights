import argparse, os, re, pathlib, requests, base64
from google import genai

OWNER = "opensource-observer"
REPO = "oso"
BRANCH = "main"
PATH = "apps/docs/docs/tutorials/index.md"

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mdx-dir",   default="mdx_build/apps/docs/docs/tutorials")
    p.add_argument("--index-url", default="https://raw.githubusercontent.com/opensource-observer/oso/refs/heads/main/apps/docs/docs/tutorials/index.md")
    p.add_argument("--index-path",default="mdx_build/apps/docs/docs/tutorials/index.md")
    return p.parse_args()

def download_index(dest: str, pat: str) -> str:
    api_url = (
        f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}"
        f"?ref={BRANCH}"
    )
    headers = {"Authorization": f"token {pat}"}
    resp = requests.get(api_url, headers=headers, timeout=30)
    resp.raise_for_status()

    content_b64 = resp.json()["content"]
    content = base64.b64decode(content_b64).decode("utf-8")

    pathlib.Path(dest).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(dest).write_text(content, encoding="utf-8")
    return content

def execute_query(client, link, existing_titles):
    prompt = f"""
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
    """

    print(prompt)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    print(response, response.parsed)
    return response.parsed

def main():
    args = parse_args()
    pat = os.environ["TARGET_PAT"]
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    index_text = download_index(args.index_path, pat)
    existing_titles = set(re.findall(r'\] \- (.*?)$', index_text, flags=re.M))
    existing_links  = set(re.findall(r'\((.*?)\)',      index_text))

    print(f"[DEBUG] Existing titles ({len(existing_titles)}): {sorted(existing_titles)}")
    print(f"[DEBUG] Existing links  ({len(existing_links)}): {sorted(existing_links)[:5]} ...")

    new_bullets = []
    for mdx in pathlib.Path(args.mdx_dir).glob("*.mdx"):
        link = f"./{mdx.name}"
        print(f"[DEBUG] Checking {link}")

        if link in existing_links:
            print("  ↳ already in index, skipping.")
            continue
        
        print(client, link, existing_titles)
        bullet = execute_query(client, link, existing_titles)
        if bullet:
            print(f"  ↳ Gemini bullet: {bullet}")
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
