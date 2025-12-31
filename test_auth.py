"""
Teste das funções de autenticação direto no banco
"""
import asyncio
from dotenv import load_dotenv
from app.database.models import register_doctor, login_doctor

load_dotenv()

async def test_auth():
    print("=== TESTE DE AUTENTICACAO ===\n")

    # Teste 1: Login com usuário existente
    print("1. Testando login com usuario existente...")
    result = await login_doctor("fabiobz@gmail.com", "senha123")
    if result["status"] == "success":
        print(f"  OK! Usuario: {result['doctor']['name']}")
    else:
        print(f"  ERRO: {result['error']}")

    print()

    # Teste 2: Login com senha errada
    print("2. Testando login com senha errada...")
    result = await login_doctor("fabiobz@gmail.com", "senhaerrada")
    if result["status"] == "error":
        print(f"  OK! Senha rejeitada: {result['error']}")
    else:
        print(f"  ERRO: Deveria ter rejeitado!")

    print()

    # Teste 3: Cadastro de novo médico
    print("3. Testando cadastro de novo medico...")
    result = await register_doctor({
        "name": "Dr. Teste Bot",
        "crm": "99999-SP",
        "email": "teste.bot@clinica.com",
        "password": "senha123456",
        "specialty": "Cardiologia"
    })

    if result["status"] == "success":
        print(f"  OK! Medico criado: {result['doctor']['name']}")
    elif "já cadastrado" in result["error"]:
        print(f"  OK! Email ja existe (esperado): {result['error']}")
    else:
        print(f"  ERRO: {result['error']}")

    print("\n=== TESTES CONCLUIDOS ===")

if __name__ == "__main__":
    asyncio.run(test_auth())
