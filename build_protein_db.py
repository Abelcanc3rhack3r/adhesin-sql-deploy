import sqlite3
import pandas as pd
from pathlib import Path
def find_file(protein_id, processed_dir):
    #find a file beginning with the protein_id in the processed_dir
    for f in processed_dir.iterdir():
        if f.is_file() and f.name.startswith(protein_id):
            return f.absolute()
    
    return None
def build_database():
    # Paths
    db_path = "proteins.db"
    metadata_csv = "alp_metadata_v7_with_filenames.csv"
    processed_dir = Path(r"C:\Users\abel\Documents\adhesin\SQL_database\structures\processed")
    
    # 1. Connect and Create Schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS proteins")
    cursor.execute("""
        CREATE TABLE proteins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protein_id TEXT,
            uniprot_id TEXT,
            phylum TEXT,
            genus TEXT,
            species TEXT,
            ncbi_annotation TEXT,
            aa_len INTEGER,
            habitat TEXT,
            file_path TEXT,
            file_type TEXT
        )
    """)
    
    # 2. Load Metadata
    df = pd.read_csv(metadata_csv, sep='\t')
    
    # 3. Scan Processed Folder for matches
    # We create a map of base_name -> full_path
    processed_files = {}
    for f in processed_dir.iterdir():
        if f.is_file():
            # Get base name (matching normalization script logic)
            base = f.name.split('.')[0]
            processed_files[base] = f
            
    # 4. Prepare data for insertion
    insert_data = []
    for _, row in df.iterrows():
        protein_id=row['protein_id']
        file_info = find_file(protein_id, processed_dir)
        if file_info is None: continue
        
        base_name = file_info.stem
        
        if base_name in processed_files:
            file_info = processed_files[base_name]
            record = (
                row['protein_id'],
                row['uniprot_id'],
                row['phylum'],
                row['genus'],
                row['species'],
                row['ncbi_annotation'],
                int(row['aa_len']),
                row['habitat'] if pd.notna(row['habitat']) else "Unknown",
                str(file_info.absolute()),
                file_info.suffix.replace('.', '')
            )
            print("appended", record)
            insert_data.append(record)

    # 5. Insert and Commit
    cursor.executemany("""
        INSERT INTO proteins (protein_id, uniprot_id, phylum, genus, species, ncbi_annotation, aa_len, habitat, file_path, file_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, insert_data)
    
    conn.commit()
    print(f"Success! Imported {len(insert_data)} proteins into {db_path}")
    conn.close()

if __name__ == "__main__":
    build_database()
