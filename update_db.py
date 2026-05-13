import sqlite3
import pandas as pd

DB_PATH = "proteins.db"
CSV_PATH = "curatedALPs_appended.csv"

# Load and lowercase the CSV data
df = pd.read_csv(CSV_PATH)
df['protein_id'] = df['protein_id'].str.lower()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Step 1: Ensure existing protein IDs are lowercased for the join
cursor.execute("UPDATE proteins SET protein_id = LOWER(protein_id)")
conn.commit()

# Step 2: Save the CSV data to a new table
df.to_sql('alp_features', conn, if_exists='replace', index=False)

conn.close()
print("Database updated: 'alp_features' table created and IDs lowercased.")
