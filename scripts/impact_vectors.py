import numpy as np
import pandas as pd


MODELS = {
    'linear': lambda x: x,
    'log': lambda x: np.log(x + 1e-9)
}


def apply_transform(dataframe, column, transform_func, threshold):
    """Apply transformation function to a dataframe column with threshold filtering."""
    filtered_series = dataframe[column].dropna()
    transformed_series = transform_func(filtered_series[filtered_series >= threshold])
    return transformed_series

def standardize_series(series):
    """Standardize series (z-score normalization)."""
    return (series - series.mean()) / series.std()

def calculate_weighted_impacts(dataframe, impact_vectors, threshold=0):
    """Calculate weighted impacts for specified vectors."""
    weighted_impacts = pd.DataFrame(index=dataframe.index)
    
    for column, (transform, weight) in impact_vectors.items():
        transform_func = MODELS.get(transform, lambda x: x)
        transformed_series = apply_transform(dataframe, column, transform_func, threshold)
        standardized_series = standardize_series(transformed_series)
        weighted_impacts[f"wtd_{column}"] = standardized_series * weight
        
    weighted_impacts['pool_score'] = weighted_impacts.sum(axis=1)
    return weighted_impacts

def create_impact_pool(dataframe, impact_vectors, name_col='project_name'):
    """Create a pool of impacts based on specified vectors and their weights."""
    weighted_impacts = calculate_weighted_impacts(dataframe, impact_vectors)
    cols = [name_col] + list(impact_vectors.keys())
    new_df = dataframe[cols].join(weighted_impacts)
    new_df.sort_values(by='pool_score', ascending=False, inplace=True)
    return new_df