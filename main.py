import agent
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os

app = FastAPI()

DB_PATH = os.getenv("DB_PATH", "proteins_combined.db")
DOMAIN_DB_PATH = os.getenv("DOMAIN_DB_PATH", "proteins_combined1.db") # This is the new database with domain boundaries
STRUCTURES_PATH = os.getenv("STRUCTURES_PATH", "structures/processed")

class ProteinMetadata(BaseModel):
    protein_id: str
    uniprot_id: Optional[str]
    phylum: Optional[str]
    genus: Optional[str]
    species: Optional[str]
    ncbi_annotation: Optional[str]
    aa_len: Optional[int]
    habitat: Optional[str]
    domain_sequence: Optional[str]
    final_classification: Optional[str]

class DomainBoundary(BaseModel):
    class_name: str
    res_start: int
    res_end: int
    confidence: float

@app.get("/search", response_model=List[ProteinMetadata])
def search_proteins(
    query: Optional[str] = "", 
    alp_class: Optional[List[str]] = Query(None)
):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Base Query
    sql = "SELECT * FROM proteins WHERE (protein_id LIKE ? OR species LIKE ? OR ncbi_annotation LIKE ?)"
    params = [f"%{query}%", f"%{query}%", f"%{query}%"]
    
    # Append ALP Group Filter if selected
    if alp_class:
        placeholders = ', '.join(['?'] * len(alp_class))
        sql += f" AND final_classification IN ({placeholders})"
        params.extend(alp_class)
        
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/structure/{protein_id}")
def get_structure(protein_id: str):
    # Search for both .cif and .pdb extensions
    for ext in [".cif", ".pdb"]:
        file_path = os.path.join(STRUCTURES_PATH, f"{protein_id}{ext}")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return f.read()
    
    raise HTTPException(status_code=404, detail="Structure file not found")

@app.get("/classes")
def get_unique_classes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT final_classification FROM proteins WHERE final_classification IS NOT NULL")
    classes = [row for row in cursor.fetchall()]
    conn.close()
    return sorted(classes)

@app.get("/domains/{protein_id}", response_model=List[DomainBoundary])
def get_domains(protein_id: str):
    conn = sqlite3.connect(DOMAIN_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # SQL query to extract the domain types and boundaries
    #print the query for debugging
    print(f"Executing SQL query for domains of {protein_id}:")
    cursor.execute("SELECT class_name, res_start, res_end, confidence FROM domain_boundaries WHERE protein_id = ? ORDER BY res_start ASC", (protein_id.lower(),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- NEW LLM ENDPOINT ---
from pydantic import BaseModel
import agent

class NLQuery(BaseModel):
    query: str

@app.post("/nl_ask")
def ask_database(payload: NLQuery):
    try:
        response = agent.process_nl_query(payload.query, DB_PATH)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

