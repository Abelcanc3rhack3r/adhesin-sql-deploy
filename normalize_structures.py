import os
from pathlib import Path
from Bio.PDB import PDBParser, MMCIFParser
import warnings

# Suppress PDB construction warnings for cleaner output
from Bio.PDB.PDBExceptions import PDBConstructionWarning
warnings.simplefilter('ignore', PDBConstructionWarning)

def normalize_proteins():
    base_dir = Path(r"C:\Users\abel\Documents\adhesin\SQL_database\structures")
    output_dir = base_dir / "processed"
    output_dir.mkdir(exist_ok=True)

    pdb_parser = PDBParser(QUIET=True)
    cif_parser = MMCIFParser(QUIET=True)

    for file_path in base_dir.iterdir():
        if file_path.is_dir() or file_path.suffix == '.py':
            continue

        # Strip all known messy extensions to get the base ID
        # Handles .pdb.cif, .cif.pdb, etc.
        base_name = file_path.name.split('.')[0]
        
        success = False
        
        # 1. Try MMCIF
        try:
            cif_parser.get_structure(base_name, str(file_path))
            new_path = output_dir / f"{base_name}.cif"
            os.replace(file_path, new_path)
            print(f"Normalized: {file_path.name} -> {new_path.name}")
            success = True
        except Exception:
            pass
        
        # 2. Try PDB Fallback
        if not success:
            try:
                pdb_parser.get_structure(base_name, str(file_path))
                new_path = output_dir / f"{base_name}.pdb"
                os.replace(file_path, new_path)
                print(f"Normalized: {file_path.name} -> {new_path.name}")
                success = True
            except Exception:
                print(f"Failed to parse: {file_path.name}")

if __name__ == "__main__":
    normalize_proteins()
