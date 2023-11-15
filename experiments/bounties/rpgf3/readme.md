# RPGF3 exploratory data analysis bounty

Bounty details: https://www.bountycaster.xyz/bounty/0x03ecf71758f9ae285e2107b1a6a1e6bb2badb63e

## Instructions

1. Checkout the JSON. It includes cleaned data from projects Retro PGF3 applications.

2. Checkout the CSV. It's a dataset of contributions to every GitHub repo included in RPGF3

| id | project|repo|type|user|month|total_amount|
--- | --- | --- | --- | --- | --- | --- |
|0|abi-to-sol-gnidan|gnidan/abi-to-sol|PR|42241.0|2021-11|1.0|
|1|abi-to-sol-gnidan|gnidan/abi-to-sol|Commit|42241.0|2021-11|12.0|
|2|across|across-protocol/frontend-v1|PR|49602.0|2021-11|4.0|
|3|across|across-protocol/frontend-v1|PR|89557.0|2021-11|6.0|

3. The goal is to surface insights about which projects/teams/individuals had the most impact on the optimism ecosystem. Feel free to take this in any direction you like!

4. Submit your work as a PR to this repo. You can include a notebook, a markdown file, or anything else that helps you tell the story of the data.

5. I've included a very crude page rank implementation to give you an idea of the types of things you could do. Feel free to create a better page rank model if you do. (And if you go that direction, read [this first](https://research.protocol.ai/blog/2020/sourcecred-an-introduction-to-calculating-cred-and-grain/).) You can also go in a completely different direction if you like.

6. Whatever you come up with should evaluate to a list of projects and their scores. The scores should be comparable across projects. See the example at the end of the page_rank.py file.

Any questions, dm me on [farcaster](https://warpcast.com/cerv1)
