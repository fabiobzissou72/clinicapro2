"""
Script de teste de conexão com Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Carrega .env
load_dotenv()

def test_connection():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    print(f"Testando conexao...")
    print(f"URL: {url}")
    print(f"Key: {key[:20]}..." if key else "Key: None")

    try:
        # Tenta criar cliente
        supabase = create_client(url, key)
        print("Cliente Supabase criado!")

        # Tenta fazer uma query simples
        response = supabase.table("patients").select("*").limit(1).execute()
        print(f"Conexao OK! Found {len(response.data)} patients")
        return True

    except Exception as e:
        print(f"ERRO: {e}")
        print(f"Tipo do erro: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_connection()
