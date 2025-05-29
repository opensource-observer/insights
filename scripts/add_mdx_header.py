import argparse, pathlib, re

parser = argparse.ArgumentParser()
parser.add_argument("--dir", required=True, help="Directory that contains *.mdx")
parser.add_argument("--pos", required=True, type=int, help="Sidebar position")
args = parser.parse_args()

tut_dir = pathlib.Path(args.dir).resolve()
sidebar_pos = args.pos

for mdx in tut_dir.glob("*.mdx"):
    title = mdx.stem.replace("-", " ").title()
    header = (
        f"---\n"
        f"title: {title}\n"
        f"sidebar_position: {sidebar_pos}\n"
        f"---\n\n"
        "import Tabs from '@theme/Tabs';\n"
        "import TabItem from '@theme/TabItem';\n\n"
    )

    body = mdx.read_text()
    if body.lstrip().startswith("---"):                      # replace, don't double-insert
        body = re.sub(r"^---[\s\S]+?---\s+", header, body, count=1, flags=re.M)
    else:
        body = header + body
    mdx.write_text(body)

print("✓ Front-matter (pos =", sidebar_pos, ") injected into", tut_dir)
