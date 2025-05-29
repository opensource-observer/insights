import argparse, json, pathlib, subprocess, sys

parser = argparse.ArgumentParser()
parser.add_argument("--notebook", required=True)
parser.add_argument("--folder", required=True)
args = parser.parse_args()

nb_path = pathlib.Path(args.notebook).resolve()
if not nb_path.exists():
    sys.exit(f"{nb_path} not found")

# upload (returns public link)
link = subprocess.check_output(
    ["python", "scripts/upload_to_drive.py", str(nb_path), "--folder", args.folder],
    text=True,
).strip()

# insert markdown cell if not present
nb = json.loads(nb_path.read_text())
first_src = nb["cells"][0]["source"] if nb["cells"] else []
already = (
    any("open in colab" in line.lower() for line in first_src)
    if isinstance(first_src, list)
    else "open in colab" in first_src.lower()
)
if not already:
    nb["cells"].insert(
        0,
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [f'[Open in Colab]({link})\n'],
        },
    )
    nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print("✓ Colab link embedded")
