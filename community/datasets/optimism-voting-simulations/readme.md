# Retro Funding 5-6 Anonymous Voting Data

The CSV file `rf_anon_votes.csv` (available on request, and generated uniquely per request) contains anonymous voting data from Retro Funding Rounds 5 and 6.

The schema is as follows:

- `voter_address`: a random wallet address that represents an actual ballot cast during the round. Each voter has a unique, randomized address per round (even if they appeared in both rounds).
- `project_id`: a random project id that represents an actual project that appeared in the round. Each project has a unique, randomized id per round (even if they appeared in both rounds). 
- `vote`: the voter's percentage allocation to that project. Voters were expected to vote `null` if they had a conflict of interest.
- `voter_tags`: a list of tags including whether the voters is a "Citizen" or "Guest", and "Expert" or "Non-expert" (in RF5 only).

Note that in both rounds, voters were randomly assigned a category and could only vote on projects within their category.