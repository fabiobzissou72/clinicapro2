"""
Verifica quais tabelas existem no Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# Lista de tabelas para checar
tables = ["patients", "prontuarios", "doctors", "case_analyses"]

print("=== CHECANDO TABELAS ===\n")

for table in tables:
    try:
        response = supabase.table(table).select("*").limit(1).execute()
        print(f"{table}: OK (tem {len(response.data)} registros no select)")
    except Exception as e:
        print(f"{table}: ERRO - {str(e)[:100]}")

print("\n=== FIM ===")
