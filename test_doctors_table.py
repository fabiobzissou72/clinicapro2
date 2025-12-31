"""
Teste da tabela doctors
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(url, key)

# Tenta listar doctores
try:
    response = supabase.table("doctors").select("*").limit(5).execute()
    print(f"Total doctors: {len(response.data)}")

    if response.data:
        for doc in response.data:
            print(f"  - {doc.get('name')} ({doc.get('email')})")
    else:
        print("Nenhum medico cadastrado ainda")
except Exception as e:
    print(f"Erro: {e}")
