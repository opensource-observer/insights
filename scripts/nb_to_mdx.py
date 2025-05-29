import argparse, pathlib, subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--notebook", required=True)
parser.add_argument("--folder", required=True)
parser.add_argument("--outdir", default="mdx_build")
args = parser.parse_args()

nb = pathlib.Path(args.notebook).resolve()
outdir = pathlib.Path(args.outdir)
outdir.mkdir(parents=True, exist_ok=True)
basename = nb.stem

# get Colab link
link = subprocess.check_output(
    ["python", "scripts/upload_to_drive.py", str(nb), "--folder", args.folder],
    text=True,
).strip()

# go from nbconvert to markdown
subprocess.run(
    [
        "jupyter",
        "nbconvert",
        str(nb),
        "--to",
        "markdown",
        "--output",
        basename,
        "--output-dir",
        str(outdir),
    ],
    check=True,
)

md_path = outdir / f"{basename}.md"
mdx_path = outdir / f"{basename}.mdx"

header = f'<a href="{link}" target="_blank">Open in Colab</a>\n\n'
mdx_path.write_text(header + md_path.read_text())

print(f"✓ Wrote {mdx_path}")
