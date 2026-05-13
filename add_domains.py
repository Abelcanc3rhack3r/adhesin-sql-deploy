import sqlite3
import pandas as pd

DB_PATH = "proteins_combined1.db"
CSV_PATH = "predicted_domains_yolo1.csv"

# Load the CSV
print("Loading predicted domains...")
df = pd.read_csv(CSV_PATH)

# Lowercase protein_id to match our database convention
if 'protein_id' in df.columns:
    df['protein_id'] = df['protein_id'].str.lower()

conn = sqlite3.connect(DB_PATH)

# Save to a new table (replace if it already exists)
print("Saving to 'domain_boundaries' table...")
df.to_sql('domain_boundaries', conn, if_exists='replace', index=False)

# Add an index to make SQL queries lightning fast
cursor = conn.cursor()
cursor.execute("CREATE INDEX IF NOT EXISTS idx_protein_id ON domain_boundaries (protein_id)")
conn.commit()
conn.close()

print("Success! Domain boundaries added to the database.")
