from collections import Counter
import json
from nltk import ngrams
from nltk.tokenize import word_tokenize
import pandas as pd

from parse_links import Parser


JSON_INPATH = "data/RPGF3/RPGF3_cleaned_applicant_data_final.json"
CSV_OUTPATH = "data/RPGF3/RPGF3_tagged_projects.csv"


PARSER_TAGS = {
    "GitHub": Parser.github, 
    "Contract on OP Mainnet": Parser.etherscan, 
    "Contract on Base": Parser.basescan,
    "NPM Package": Parser.npm, 
    "Twitter": Parser.twitter, 
    "Substack": Parser.substack,
    "Optimism Gov": Parser.optimism_gov,
    "Dune": Parser.dune,
    "Flipside": Parser.flipside,
}
IMPACT_CATEGORIES = {
    'COLLECTIVE_GOVERNANCE': 'Collective Governance',
    'DEVELOPER_ECOSYSTEM': 'Developer Ecosystem', 
    'END_USER_EXPERIENCE_AND_ADOPTION': 'End User Experience and Adoption', 
    'OP_STACK': 'OP Stack'
}
FUNDING_CATEGORIES = {
    'RETROPGF_2': 'RPGF2',
    'RETROPGF_1': 'RPGF1',
    'PARTNER_FUND': 'Partner Fund',
    'GOVERNANCE_FUND': 'Governance Fund',
    'REVENUE': 'Revenue'
}
BIGRAMS = {
    ('base', 'chain'): "Base",
    ('base', 'mainnet'): "Base"
}
WORD_COUNTS = {
    ('base', 3): "Base",
    ('zora', 3): "Zora",
    ('farcaster', 3): "Farcaster"
}


def evaluate_text(text, tag_prefix):
    tags = []
    
    text = text.lower()
    bigram_list = list(ngrams(text.split(), 2))
    tokens = word_tokenize(text, language='english', preserve_line=False)    
    word_counts = Counter(tokens)
    
    for bigram, label in BIGRAMS.items():
        if bigram in bigram_list:
            tags.append(f"{tag_prefix}: {label}")
    
    for (word,count), label in WORD_COUNTS.items():
        if word_counts[word] >= count:
            tags.append(f"{tag_prefix}: {label}")
            
    return tags


def evaluate_link(link, tag_prefix):
    tags = []
    for parser_type, parser in PARSER_TAGS.items():
        result = parser(link)
        if result[0] == 'success':
            new_tag = f"{tag_prefix}: {parser_type}"
            if parser_type == "GitHub":
                owner = result[1].split("/")[0]
                if owner in ['ethereum', 'ethereum-optimism', 'duneanalytics']:
                    new_tag = f"{new_tag} ({owner})"
            tags.append(new_tag)
    return tags


def process_project(project):

    tags = [f"Category: {IMPACT_CATEGORIES[k]}" for k in project['Tags']]
        
    contributions = project['Contributions: Github'] + project['Contributions: Contracts'] + project['Contributions: Other']
    for link in contributions:
        tags.extend(evaluate_link(link, 'Link'))
        
    for link in project['Impact Metrics']:
        tags.extend(evaluate_link(link, 'Link'))
        
    narrative = " ".join([project["Bio"], project["Contribution Description"], project["Impact Description"]])
    tags.extend(evaluate_text(narrative, 'Keywords'))

    tags.extend([f"Funding: {FUNDING_CATEGORIES.get(k, 'Other')}" for k in project['Funding Sources']])

    project['Tags'] = sorted(list(set(tags)))


def tag_projects(join_csv=None):

    with open(JSON_INPATH) as f:
        data = json.load(f)
    
    for project in data:
        process_project(project)

    df = pd.DataFrame(data)
    dummies = df['Tags'].apply(lambda x: ','.join(x)).str.get_dummies(sep=',')
    cols = ['Project ID', 'Project Name', 'Applicant Type', 'Website', 'Bio', 'Payout Address', 'Slug: Primary']
    df = pd.concat([df[cols], dummies], axis=1)
    df.rename(columns={"Slug: Primary": "OSO Slug"}, inplace=True)

    if join_csv:
        df2 = pd.read_csv(join_csv)
        df = df.join(df2.set_index('slug'), on='OSO Slug')

    df['sort'] = df['Project Name'].apply(lambda x: x.lower().strip())
    df.sort_values(by='sort', inplace=True)
    df.drop(columns=['sort'], inplace=True)
    df.to_csv(CSV_OUTPATH, index=False)
    

if __name__ == "__main__":
    tag_projects(join_csv="data/RPGF3/RPGF3_OSO_project_stats_DRAFT.csv")    