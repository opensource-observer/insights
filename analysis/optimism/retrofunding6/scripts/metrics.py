
PROJECT_UID = 'projectRegUID'

def calculate_metrics(df):

    return [
        {
            'name': 'count_total_attestations',
            'description': 'Number of Attestations',
            'data': df.groupby(PROJECT_UID)['id'].count().to_dict()
        },
        {
            'name': 'count_citizen_attestations',
            'description': 'Number of Attestations by Citizens',
            'data': df[df['is_citizen']].groupby(PROJECT_UID)['id'].count().to_dict()
        },
        {
            'name': 'count_delegate_attestations',
            'description': 'Number of Attestations by Top Delegates',
            'data': df[df['is_top_delegate']].groupby(PROJECT_UID)['id'].count().to_dict()
        },
        {
            'name': 'avg_nps_score',
            'description': 'Average NPS score of Citizens and Top Delegates',
            'data': df.groupby(PROJECT_UID)['nps_score'].mean().to_dict()
        },
        {
            'name': 'most_positive_superlative',
            'description': 'Most positive superlative (20 reviews, 95% high PMF and 95% high NPS)',
            'data': {
                uid: most_positive_superlative(df, uid) 
                for uid in df[PROJECT_UID].unique()
            }
        },
        {
            'name': 'cant_live_without_superlative',
            'description': "Can't live without superlative (20 reviews, 90% high PMF)",
            'data': {
                uid: cant_live_without_superlative(df, uid) 
                for uid in df[PROJECT_UID].unique()
            }
        },
        {
            'name': 'percentage_distributions',
            'description': "Percentage distribution of different ratings by citizens and top delegates",
            'data': {
                uid: ratings_distribution(df, uid) 
                for uid in df[PROJECT_UID].unique()
            }
        },
        {
            'name': 'elected_governance_reviews',
            'description': 'Reviews from elected governance members',
            'data': {
                uid: councils_distribution(df, uid) 
                for uid in df[PROJECT_UID].unique()
            }
        }
    ]

def most_positive_superlative(df, ref_uid):
    """Determine if a project has 20 reviews and 95% positive PMF and NPS."""
    dff = df[df[PROJECT_UID] == ref_uid]
    num_reviews = len(dff)
    pmf_pos_reviews = (dff['pmf_score'] > 2).sum() / num_reviews
    nps_pos_reviews = (dff['nps_score'] > 8).sum() / num_reviews
    
    result = (num_reviews >= 20) and (pmf_pos_reviews >= .95) and (nps_pos_reviews >= .95)
    return result

def cant_live_without_superlative(df, ref_uid):
    """Determine if a project has 20 reviews and 90% positive PMF."""
    dff = df[df[PROJECT_UID] == ref_uid]
    num_reviews = len(dff)
    pmf_pos_reviews = (dff['pmf_score'] > 2).sum() / num_reviews
    result = (num_reviews >= 20) and (pmf_pos_reviews >= .90)
    return result

def ratings_distribution(df, ref_uid):
    """Calculate distribution of ratings by citizens and top delegates."""
    dff = df[df[PROJECT_UID] == ref_uid]
    dff_citizens = dff[dff['is_citizen'] == True]
    dff_delegates = dff[dff['is_top_delegate'] == True]

    def calculate_distribution(group, score):
        total = len(group)
        if not total:
            return None
        return (group['pmf_score'] == score).sum() / total
    
    return {
        'citizens': {
            'extremely_upset': calculate_distribution(dff_citizens, 3),
            'somewhat_upset': calculate_distribution(dff_citizens, 2),
            'neutral': calculate_distribution(dff_citizens, 1)
        },
        'top_delegates': {
            'extremely_upset': calculate_distribution(dff_delegates, 3),
            'somewhat_upset': calculate_distribution(dff_delegates, 2),
            'neutral': calculate_distribution(dff_delegates, 1)
        }
    }

def councils_distribution(df, ref_uid):
    """Calculate distribution of reviews by governance members."""
    dff = df[df[PROJECT_UID] == ref_uid]
    result = {}
    councils = ['Anticapture Commission', 'Code of Conduct', 'Grants Council', 'Security Council']
    for council in councils:
        dff_council = dff[dff['governance_membership'].apply(lambda x: council in x)]
        if dff_council.empty:
            continue
        result.update({
            council.replace(' ', '_').lower(): {
                'count_attestations': len(dff_council),
                'avg_pmf_score': dff_council['pmf_score'].mean(),
                'avg_nps_score': dff_council['nps_score'].mean()
            }
        })
    return result