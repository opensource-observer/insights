---
name: PLDG Proof-of-Work Submission
about: Submit your PLDG data pipeline health check notebook for review
title: "[PLDG Submission]: Data Source - @username"
labels: c:community
assignees: ccerv1

---

# PLDG Proof-of-Work Submission

## Contributor
- **GitHub Username:** @username
- **Discord Username (if applicable):**

## Gist Link
**Link to your notebook gist:** https://gist.github.com/username/...

## Data Source Audited
**Pipeline audited:**
- Staging: `oso.stg_[source]__[table]`
- Intermediate: `oso.int_[model]`
- Mart: `oso.[model]_v0`

## Key Findings
Provide a 2-3 sentence summary of your analysis:

-
-
-

## Checklist
Before submitting, verify that your notebook:

- [ ] Runs successfully with `uv run marimo edit your_notebook.py`
- [ ] Passes structure validation with `uv run marimo check your_notebook.py`
- [ ] Includes all 3 required checks (presence, date coverage, duplicates)
- [ ] Audits all 3 pipeline stages (staging → intermediate → mart)
- [ ] Contains visualizations using plotly
- [ ] Has clear markdown documentation explaining analysis
- [ ] Separates concerns (markdown, SQL, and Python in separate cells)
- [ ] Follows naming convention: `{data_source}_{username}.py`
- [ ] Pipeline documentation section is complete

## Additional Notes
Any additional context, questions, or issues encountered:


---

**Next Steps:** OSO maintainers will review your submission. If approved, you'll be asked to submit a PR with your notebook.
