"""
Exemplo de Cadastro de Paciente
Demonstra como cadastrar paciente e histórico médico
"""

import asyncio
import sys
from pathlib import Path

# Adiciona diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
load_dotenv()

from app.database.models import (
    create_patient,
    get_patient_by_cpf,
    update_patient_history,
    get_patient_full_profile
)


async def exemplo_cadastro_completo():
    """Exemplo de cadastro completo de paciente"""

    print("\n" + "="*70)
    print("📋 EXEMPLO: CADASTRO DE PACIENTE")
    print("="*70)

    # ===== 1. CRIAR PACIENTE =====
    print("\n1️⃣ Criando paciente...")

    paciente_data = {
        "full_name": "João da Silva Santos",
        "cpf": "12345678900",  # CPF sem máscara
        "phone": "(11) 98765-4321",
        "email": "joao.santos@email.com",
        "birth_date": "1965-05-15",
        "age": 58,
        "gender": "M",
        "blood_type": "O+",

        # Endereço
        "address_street": "Rua das Flores",
        "address_number": "123",
        "address_city": "São Paulo",
        "address_state": "SP",
        "address_zipcode": "01234-567",

        # Emergência
        "emergency_contact_name": "Maria Santos",
        "emergency_contact_phone": "(11) 91234-5678",
        "emergency_contact_relationship": "Esposa",

        # Convênio
        "health_insurance": "Unimed",
        "insurance_number": "123456789"
    }

    result = await create_patient(paciente_data)

    if result["status"] == "success":
        print(f"✅ Paciente cadastrado com sucesso!")
        print(f"   ID: {result['patient_id']}")
        patient_id = result['patient_id']
    else:
        print(f"❌ Erro: {result['error']}")
        return

    # ===== 2. ADICIONAR HISTÓRICO MÉDICO =====
    print("\n2️⃣ Adicionando histórico médico...")

    historico = {
        "comorbidities": [
            "Hipertensão Arterial Sistêmica",
            "Diabetes Mellitus Tipo 2",
            "Dislipidemia"
        ],

        "allergies": [
            "Penicilina",
            "Dipirona"
        ],

        "current_medications": [
            {
                "name": "Losartana",
                "dose": "50mg",
                "frequency": "12/12h",
                "via": "VO"
            },
            {
                "name": "Metformina",
                "dose": "850mg",
                "frequency": "12/12h",
                "via": "VO"
            },
            {
                "name": "Sinvastatina",
                "dose": "40mg",
                "frequency": "1x ao dia (noite)",
                "via": "VO"
            },
            {
                "name": "AAS",
                "dose": "100mg",
                "frequency": "1x ao dia",
                "via": "VO"
            }
        ],

        "family_history": """
        Pai: Faleceu aos 62 anos por IAM.
        Mãe: Viva, 80 anos, hipertensa.
        Irmãos: 2 irmãos, ambos hipertensos.
        """,

        "smoker": False,
        "smoking_pack_years": 20,  # Ex-tabagista
        "alcohol_use": "Social",
        "physical_activity": "Sedentário",

        "previous_cardiac_events": [
            "IAM inferior em 2020 (tratado com angioplastia + stent)",
            "Angina estável desde 2021"
        ],

        "cardiac_risk_factors": [
            "Hipertensão Arterial",
            "Diabetes Mellitus tipo 2",
            "Dislipidemia",
            "Ex-tabagista (carga tabágica 20 maços/ano)",
            "História familiar positiva para DAC",
            "Sedentarismo"
        ],

        "previous_surgeries": [
            {
                "surgery": "Angioplastia com implante de stent",
                "location": "Coronária direita",
                "year": 2020,
                "hospital": "Hospital do Coração"
            },
            {
                "surgery": "Apendicectomia",
                "year": 1995
            }
        ]
    }

    result = await update_patient_history(patient_id, historico)

    if result["status"] == "success":
        print("✅ Histórico médico atualizado com sucesso!")
    else:
        print(f"❌ Erro: {result['error']}")

    # ===== 3. BUSCAR PERFIL COMPLETO =====
    print("\n3️⃣ Buscando perfil completo do paciente...")

    profile = await get_patient_full_profile(patient_id)

    if profile["status"] == "success":
        print("\n" + "="*70)
        print("📊 PERFIL COMPLETO DO PACIENTE")
        print("="*70)

        patient = profile["patient"]
        history = profile["history"]

        print(f"\n👤 DADOS PESSOAIS:")
        print(f"   Nome: {patient['full_name']}")
        print(f"   CPF: {patient['cpf']}")
        print(f"   Idade: {patient['age']} anos")
        print(f"   Sexo: {patient['gender']}")
        print(f"   Tipo Sanguíneo: {patient['blood_type']}")
        print(f"   Telefone: {patient['phone']}")
        print(f"   E-mail: {patient['email']}")

        print(f"\n📍 ENDEREÇO:")
        print(f"   {patient['address_street']}, {patient['address_number']}")
        print(f"   {patient['address_city']}/{patient['address_state']}")
        print(f"   CEP: {patient['address_zipcode']}")

        print(f"\n🚨 CONTATO DE EMERGÊNCIA:")
        print(f"   {patient['emergency_contact_name']} ({patient['emergency_contact_relationship']})")
        print(f"   Tel: {patient['emergency_contact_phone']}")

        if history:
            print(f"\n🏥 HISTÓRICO MÉDICO:")

            print(f"\n   Comorbidades:")
            for c in history.get('comorbidities', []):
                print(f"   • {c}")

            print(f"\n   Alergias:")
            for a in history.get('allergies', []):
                print(f"   • {a}")

            print(f"\n   Medicações em uso:")
            for m in history.get('current_medications', []):
                print(f"   • {m['name']} {m['dose']} - {m['frequency']}")

            print(f"\n   Eventos cardíacos prévios:")
            for e in history.get('previous_cardiac_events', []):
                print(f"   • {e}")

            print(f"\n   Fatores de risco cardiovascular:")
            for f in history.get('cardiac_risk_factors', []):
                print(f"   • {f}")

        print("\n" + "="*70)

    # ===== 4. BUSCAR POR CPF =====
    print("\n4️⃣ Testando busca por CPF...")

    patient = await get_patient_by_cpf("123.456.789-00")  # Com máscara

    if patient:
        print(f"✅ Paciente encontrado: {patient['full_name']}")
    else:
        print("❌ Paciente não encontrado")

    print("\n" + "="*70)
    print("✅ EXEMPLO CONCLUÍDO!")
    print("="*70)


async def exemplo_busca_rapida():
    """Exemplo de busca rápida de paciente"""

    print("\n" + "="*70)
    print("🔍 EXEMPLO: BUSCA DE PACIENTE")
    print("="*70)

    cpf = "12345678900"

    print(f"\nBuscando paciente com CPF: {cpf}...")

    patient = await get_patient_by_cpf(cpf)

    if patient:
        print(f"\n✅ Paciente encontrado!")
        print(f"   Nome: {patient['full_name']}")
        print(f"   ID: {patient['id']}")
        print(f"   Telefone: {patient.get('phone', 'N/A')}")
    else:
        print("\n❌ Paciente não encontrado no banco de dados.")

    print("\n" + "="*70)


if __name__ == "__main__":
    import sys

    print("\n🏥 CLINICAPRO CARDIO - EXEMPLOS DE CADASTRO DE PACIENTES\n")

    if len(sys.argv) > 1 and sys.argv[1] == "buscar":
        asyncio.run(exemplo_busca_rapida())
    else:
        asyncio.run(exemplo_cadastro_completo())

    print("\n💡 Dica: Execute 'python examples/exemplo_cadastro_paciente.py buscar' para buscar")
