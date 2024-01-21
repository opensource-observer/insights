# RetroPGF3 Impact Vectors

Bounty details: https://www.bountycaster.xyz/bounty/0x0edbab5a1bd66355eb5c648598793ade9e019c21

## Objective

Identify numeric variables that correlate with positive Optimism RetroPGF3 results.

We have prepared a dataset with lots of numeric (and boolean) values that could be used to predict the results of RetroPGF3, such as team size, GitHub metrics, onchain metrics, etc. You are welcome to combine these variables to create new ones if you want. 

The dependent variables we are interested in the `OP Received` and/or the `# Ballots` a project received.

## Instructions

1. Skim [this post](https://docs.opensource.observer/blog/what-builders-can-learn-from-retropgf3) with our take on RetroPGF3 results, especially the end about "impact vectors"

2. Checkout the CSV file. It includes cleaned data about projects from several sources prepared by Open Source Observer. This is basically the same dataset we used to create our version of impact vectors.

3. Checkout the Python Notebook. It shows how to load, transform, and analyze the data with a few examples.

4. Submit your work as a PR to this repo. You can include a notebook, a markdown file, or anything else that helps you tell the story of the data.

5. The best submissions will find one or more variables that correlate with the dependent variables. Bonus points if you can create a cool data visualization of your results.

Any questions, dm me on [farcaster](https://warpcast.com/cerv1)
