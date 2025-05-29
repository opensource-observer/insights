# OSO Tutorials

This folder contains runnable examples and data science tutorials built on OSO's data platform.

Each tutorial is a standalone Jupyter notebook (`.ipynb`) that can be viewed on Colab and is published to the OSO documentation site once approved.

---

## How to Add a New Tutorial

Follow these steps to contribute your own tutorial to the platform:

### 1. Create & Upload Your Notebook

- Write your tutorial as a Jupyter notebook (`.ipynb`)
- Save it to the `tutorials/` folder in the **`insights`** repository (where this file lives)

### 2. Open a Pull Request

- Open a PR with your new tutorial notebook
- Use the title prefix: **`NEW TUTORIAL:`** so we can easily identify it
- Your PR will run automated checks defined in `.github/workflows/tutorial-checks.yml`. These checks **must pass**:
  - The file is a valid `.ipynb`
  - The notebook is formatted using Prettier
  - **Every cell in the notebook runs successfully**

> ⚠️ **Make sure your tutorial is fully executable! CI will fail if any cell errors out.**

### 3. Add Reviewers

- Request review from [@evanameyer1](https://github.com/evanameyer1) or [@ccerv1](https://github.com/ccerv1)

Once your tutorial is approved and merged, continue to the next step.

---

## Publish Your Tutorial

If you are happy with your tutorial solely exist in our insights repo then you do not need to run either of these workflows. These simply offer ways to build more coverage of your tutorial. 

We support two automation flows via `.github/workflows/tutorial-automation.yml`:

### 1. Generate a Colab Notebook

This creates a Colab link and inserts it into the notebook.

```bash
gh workflow run "Tutorial Automation" \
  --ref main \
  -f command=colab \
  -f notebook="tutorials/your-notebook.ipynb" \
  -f sidebar_position=0
````

* The Colab notebook will be auto-uploaded [here](https://drive.google.com/drive/u/2/folders/1ld_KWqNDMJl4NmzEFquNybCBph96hYDu)
* A line like `**[Open in Colab](https://...link...)**` will be added to the top of the notebook
* The changes are automatically committed and pushed to the same PR branch

### 2. Generate Docs Page (MDX)

This converts your notebook to a `.mdx` file for OSO's docs:

```bash
gh workflow run "Tutorial Automation" \
  --ref main \
  -f command=docs \
  -f notebook="tutorials/your-notebook.ipynb" \
  -f sidebar_position=10  # See below on how to pick this
```

* A new MDX page is created for your tutorial at [https://docs.opensource.observer/docs/tutorials/](https://docs.opensource.observer/docs/tutorials/)
* The tutorials index (`index.mdx`) is updated with an LLM-generated title and description that matches our existing docs style
* A PR will be created on the **`oso`** repo titled `"Add MDX tutorial(s)"`, which must pass OSO’s CI

---

## Sidebar Position Guide

The `sidebar_position` parameter controls where your tutorial appears in the docs sidebar:

* `0` = Top of the list (reserved for "Find a Tutorial")
* To **add your tutorial to the bottom**, find the bottommost tutorial in the docs sidebar:

  * Click **“Edit this page”** on the tutorial
  * Look for its `sidebar_position` in the frontmatter
  * Use that number +1 for your new tutorial

> ⚠️ You **must** pass a `sidebar_position` even when running the `colab` workflow, but you can just use `0` there.

---

## Tip: Quoting Names in GitHub CLI

If you're using the workflow **name** instead of the workflow **ID**, wrap the name in quotes:

```bash
gh workflow run "Tutorial Automation" ...
```

Or, run this to find the workflow ID (recommended):

```bash
gh workflow list
```

---

Thanks for contributing to the OSO community! 🚀
