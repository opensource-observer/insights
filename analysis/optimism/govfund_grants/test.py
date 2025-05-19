import pandas as pd
import numpy as np
from grant_parser import clean_workbook, season_summaries

# First, let's examine the raw data structure of each sheet
xl = pd.ExcelFile('data/Optimism GovFund Grants_ Public Delivery Tracking.xlsx')

for sheet in xl.sheet_names:
    if sheet.lower() in {"status key", "statuskey"}:
        continue
        
    print(f"\n{'='*80}")
    print(f"Sheet: {sheet}")
    print(f"{'='*80}")
    
    # Read first few rows without any header to see structure
    df_raw = pd.read_excel(
        'data/Optimism GovFund Grants_ Public Delivery Tracking.xlsx',
        sheet_name=sheet,
        header=None,
        nrows=5
    )
    
    print("\nFirst 5 rows (no header):")
    print(df_raw)
    
    # Try with different header rows
    for header_row in [0, 1, 2]:
        df = pd.read_excel(
            'data/Optimism GovFund Grants_ Public Delivery Tracking.xlsx',
            sheet_name=sheet,
            header=header_row,
            nrows=5
        )
        print(f"\nWith header_row={header_row}:")
        print("Columns:", df.columns.tolist())

# Use the correct relative path
df = clean_workbook('data/Optimism GovFund Grants_ Public Delivery Tracking.xlsx')

# Print all unique seasons to debug
print("\nAll unique seasons in the data:")
print(df['Grants Season or Mission'].unique())

# Print summary data
print("\nSummary data from sheets:")
for season, data in season_summaries.items():
    print(f"\n{season}:")
    print(f"Total OP Approved: {data.get('Total OP Approved', 'Not found'):,.2f}")
    print(f"Amount of OP Allocated: {data.get('Amount of OP Allocated', 'Not found'):,.2f}")

# Check Season 3 totals
print("\nSeason 3 Calculated Totals:")
season3 = df[df['Grants Season or Mission'] == 'Grants Season 3']
print(f"Total OP Approved (from data): {season3['OP Total Amount'].sum():,.2f}")
print(f"Amount of OP Allocated (from data): {season3['OP Delivered'].sum():,.2f}")
print("\nSeason 3 Projects:")
print(season3[['Project Name', 'OP Total Amount', 'OP Delivered']].sort_values('OP Total Amount', ascending=False))

# Check Season 4 totals (separating Grants and Missions)
print("\nGrants Season 4 Calculated Totals:")
season4 = df[df['Grants Season or Mission'] == 'Grants Season 4']
print(f"Total OP Approved (from data): {season4['OP Total Amount'].sum():,.2f}")
print(f"Amount of OP Allocated (from data): {season4['OP Delivered'].sum():,.2f}")
print("\nGrants Season 4 Projects:")
print(season4[['Project Name', 'OP Total Amount', 'OP Delivered']].sort_values('OP Total Amount', ascending=False))

print("\nMissions Season 4 Calculated Totals:")
missions4 = df[df['Grants Season or Mission'] == 'Missions Season 4']
print(f"Total OP Approved (from data): {missions4['OP Total Amount'].sum():,.2f}")
print(f"Amount of OP Allocated (from data): {missions4['OP Delivered'].sum():,.2f}")
print("\nMissions Season 4 Projects:")
print(missions4[['Project Name', 'OP Total Amount', 'OP Delivered']].sort_values('OP Total Amount', ascending=False))

# Check Season 5 totals
print("\nGrants Season 5 Calculated Totals:")
season5 = df[df['Grants Season or Mission'] == 'Grants Season 5']
print(f"Total OP Approved (from data): {season5['OP Total Amount'].sum():,.2f}")
print(f"Amount of OP Allocated (from data): {season5['OP Delivered'].sum():,.2f}")
print("\nGrants Season 5 Projects:")
print(season5[['Project Name', 'OP Total Amount', 'OP Delivered']].sort_values('OP Total Amount', ascending=False))

# Detailed analysis of Season 5
print("\nDetailed Season 5 Analysis:")
print("\nUnique statuses in Season 5:")
print(season5['Status'].unique())

print("\nProjects with null or zero values:")
null_projects = season5[
    (season5['OP Total Amount'].isna()) | 
    (season5['OP Total Amount'] == 0) |
    (season5['OP Delivered'].isna()) |
    (season5['OP Delivered'] == 0)
]
print(null_projects[['Project Name', 'Status', 'OP Total Amount', 'OP Delivered']].sort_values('Status'))

# Check for any summary rows that might have been missed
print("\nPotential summary rows in Season 5:")
summary_rows = season5[
    season5['Project Name'].fillna('').str.contains('Superchain|Total|Amount', case=False, na=False)
]
print(summary_rows[['Project Name', 'OP Total Amount', 'OP Delivered']])

# Look for grants around 250,000 OP
print("\nChecking raw Excel data for Season 5:")
df_raw = pd.read_excel(
    'data/Optimism GovFund Grants_ Public Delivery Tracking.xlsx',
    sheet_name='Grants Season 5',
    header=None
)
print("\nFirst 20 rows of raw data:")
print(df_raw.head(20))

# Check for any rows containing "250000" or similar values
print("\nRows containing '250000' or similar:")
mask = df_raw.astype(str).apply(lambda x: x.str.contains('250000', na=False))
print(df_raw[mask.any(axis=1)])

# Examine Silo Finance grant specifically
print("\nExamining Silo Finance grant:")
silo_grant = season5[
    season5['Project Name'].str.contains('Silo', case=False, na=False)
]
print("\nSilo Finance grant details:")
print(silo_grant)

# Print all columns for this grant to see if there are any issues
print("\nAll columns for Silo Finance grant:")
for col in silo_grant.columns:
    print(f"{col}: {silo_grant[col].values}")
