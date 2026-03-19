"""
Exécute tous les scripts SQL d'une couche donnée (clean ou analytics).
Usage : python scripts/run_sql_layer.py clean
        python scripts/run_sql_layer.py analytics
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

def run_layer(layer_name):
    sql_dir = os.path.join(os.path.dirname(__file__), "..", "sql", layer_name)

    if not os.path.exists(sql_dir):
        print(f"[ERREUR] Dossier introuvable : sql/{layer_name}/")
        return

    sql_files = sorted([f for f in os.listdir(sql_dir) if f.endswith(".sql")])

    if not sql_files:
        print(f"[INFO] Aucun fichier SQL dans sql/{layer_name}/")
        return

    engine = create_engine(DATABASE_URL)

    print(f"=== Exécution de la couche '{layer_name}' ===\n")
    for filename in sql_files:
        filepath = os.path.join(sql_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            sql = f.read()
        print(f"[RUN] {filename} ...", end=" ")
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print("OK")

    print(f"\n=== Couche '{layer_name}' terminée ! ===")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_sql_layer.py <layer>")
        print("       layer = clean | analytics")
        sys.exit(1)
    run_layer(sys.argv[1])
