import os
import json
import sqlite3
from google import genai

def process_nl_query(nl_text: str, db_path: str):
    domain_db_path = os.getenv("DOMAIN_DB_PATH", "proteins_combined1.db")
    client = genai.Client()
    
    prompt = f"""
    You are a structural bioinformatics SQL agent.
    
    Database Schema:
    - main.proteins (protein_id, uniprot_id, species, ncbi_annotation, final_classification)
    - domain_db.domain_boundaries (protein_id, class_name, res_start, res_end, confidence)

    User Query: "{nl_text}"

    TASKS & CRITICAL INSTRUCTIONS:
    1. SQL Generation: Write the SQLite query.
       - Use LOWER() and LIKE for all ID and text searches (e.g., WHERE LOWER(p.protein_id) LIKE '%stad-1%').
       - Use a LEFT JOIN on domain_db.domain_boundaries.
       - If a species is mentioned, search 'species' or 'ncbi_annotation'.
    2. Target Selection: Identify if the user wants a specific protein visualized (extract the ID).
    3. Color Rules: Identify any specific coloring rules for domains. The domain keys MUST be UPPERCASE (e.g., "ABD").

    Return ONLY raw JSON:
    {{
        "sql_query": "SELECT ...",
        "target_protein": "extracted_id_or_null",
        "color_rules": {{"DOMAIN_NAME_UPPERCASE": "color_name_or_hex"}}
    }}
    """
    
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=prompt,
    )
    
    raw_json = response.text.replace("```json", "").replace("```", "").strip()
    
    try:
        plan = json.loads(raw_json)
        print(f"\n[AI GENERATED SQL]:\n{plan['sql_query']}")
        print(f"[AI GENERATED COLORS]:\n{plan.get('color_rules', {})}\n")
    except Exception as e:
        raise ValueError(f"LLM did not return valid JSON: {raw_json}")

    absolute_db_path = os.path.abspath(db_path)
    absolute_domain_path = os.path.abspath(domain_db_path)
    
    ro_uri_main = f"file:{absolute_db_path}?mode=ro"
    conn = sqlite3.connect(ro_uri_main, uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        ro_uri_domain = f"file:{absolute_domain_path}?mode=ro"
        cursor.execute(f"ATTACH DATABASE '{ro_uri_domain}' AS domain_db")
        
        cursor.execute(plan["sql_query"])
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        
        print(f"[DATABASE RETURNED {len(results)} ROWS]")
            
    except sqlite3.Error as e:
        conn.close()
        raise RuntimeError(f"Safe SQL Execution Failed: {e}")
        
    conn.close()
    
    return {
        "results": results,
        "target_protein": plan.get("target_protein"),
        "color_rules": plan.get("color_rules", {})
    }
