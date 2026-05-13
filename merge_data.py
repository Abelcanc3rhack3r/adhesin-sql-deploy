import sqlite3
import pandas as pd
import os

# Paths
ORIGINAL_DB = "proteins.db"
NEW_CSV = "curatedALPs_appended.csv"
FINAL_DB = "proteins_combined.db"

# 1. Load data
print("Loading original database...")
conn_old = sqlite3.connect(ORIGINAL_DB)
df_original = pd.read_sql_query("SELECT * FROM proteins", conn_old)
conn_old.close()

print("Loading curated CSV...")
df_new = pd.read_csv(NEW_CSV)

# 2. Lowercase the IDs for a perfect join
df_original['protein_id'] = df_original['protein_id'].str.lower()
df_new['protein_id'] = df_new['protein_id'].str.lower()

# 3. Perform the Join (Keep all original rows, add new columns where ID matches)
# We drop 'protein_len_aa' from the CSV if it's a duplicate of 'aa_len'
if 'protein_len_aa' in df_new.columns:
    df_new = df_new.drop(columns=['protein_len_aa'])

combined_df = pd.merge(df_original, df_new, on='protein_id', how='left')

# 4. Save to a NEW database file
print(f"Saving joined data to {FINAL_DB}...")
conn_new = sqlite3.connect(FINAL_DB)
combined_df.to_sql('proteins', conn_new, if_exists='replace', index=False)
conn_new.close()

print("Success! 'proteins_combined.db' is ready with all data joined.")
