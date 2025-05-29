import pathlib, re, sys

tut_dir = pathlib.Path(sys.argv[1]).resolve()
index_md = tut_dir / "index.md"
if not index_md.exists():
    sys.exit("index.md not found")

mapping = {}
for pos, line in enumerate(index_md.read_text().splitlines(), start=1):
    m = re.match(r"- .*?\[(.+?)\]\(\./(.+?)\.mdx\)", line.strip())
    if m:
        mapping[f"{m.group(2)}.mdx"] = (pos, m.group(1))

for mdx in tut_dir.glob("*.mdx"):
    sidebar, title = mapping.get(mdx.name, (0, mdx.stem.title()))
    header = f"""---\ntitle: {title}\nsidebar_position: {sidebar}\n---\n\nimport Tabs from '@theme/Tabs';\nimport TabItem from '@theme/TabItem';\n\n"""
    body = mdx.read_text()

    if body.lstrip().startswith("---"):
        body = re.sub(r"^---[\s\S]+?---\s+", header, body, count=1, flags=re.M)
    else:
        body = header + body
    mdx.write_text(body)
print("✓ Front-matter injected")
