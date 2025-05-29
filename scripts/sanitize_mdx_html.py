import pathlib, re, sys

root = pathlib.Path(sys.argv[1])
html_block = re.compile(r"(<style[\s\S]*?</style>|<div[\s\S]*?</div>)", re.I)

for mdx in root.rglob("*.mdx"):
    text = mdx.read_text()
    text = re.sub(html_block, "", text)
    text = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("<")
    )
    mdx.write_text(text)
print("✓ HTML stripped")
