"""
Script de teste para cadastrar médico diretamente via API
"""

import requests

API_URL = "http://localhost:8000"

# Dados do médico
doctor_data = {
    "name": "Fábio Brito Zissou",
    "crm": "12345-SP",
    "email": "fabiobz@gmail.com",
    "password": "senha12345",  # Troque por uma senha segura
    "specialty": "Cardiologia",
    "phone": "11970307000"
}

print("🔄 Cadastrando médico...")
print(f"Nome: {doctor_data['name']}")
print(f"CRM: {doctor_data['crm']}")
print(f"Email: {doctor_data['email']}")
print()

try:
    response = requests.post(
        f"{API_URL}/api/v1/auth/register",
        json=doctor_data
    )

    if response.status_code == 201:
        result = response.json()
        print("✅ SUCESSO!")
        print(f"Médico cadastrado: {result['doctor']['name']}")
        print(f"ID: {result['doctor']['id']}")
        print()
        print("Agora você pode fazer login com:")
        print(f"Email: {doctor_data['email']}")
        print(f"Senha: {doctor_data['password']}")
    else:
        error = response.json()
        print(f"❌ ERRO: {error.get('detail', 'Erro desconhecido')}")
        print(f"Status code: {response.status_code}")

except Exception as e:
    print(f"❌ Erro ao conectar com API: {e}")
    print("Verifique se a API está rodando em http://localhost:8000")
