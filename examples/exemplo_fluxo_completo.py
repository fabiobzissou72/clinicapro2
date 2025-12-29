"""
Exemplo de Fluxo Completo End-to-End
Demonstra fluxo real: Cadastro → Consulta → Análise → Armazenamento
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Adiciona diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
load_dotenv()

from app.database.models import (
    create_patient,
    get_patient_by_cpf,
    update_patient_history,
    save_case_analysis
)
from app.crews.cardio_crew import analyze_cardio_case


async def fluxo_completo():
    """
    Simula fluxo completo de atendimento:
    1. Cadastro de paciente novo
    2. Histórico médico
    3. Consulta (transcrição)
    4. Análise com CrewAI
    5. Salvamento do caso
    """

    print("\n" + "="*80)
    print("🏥 CLINICAPRO CARDIO - FLUXO COMPLETO END-TO-END")
    print("="*80)

    # ===== ETAPA 1: CADASTRO DO PACIENTE =====
    print("\n" + "-"*80)
    print("1️⃣ CADASTRO DE PACIENTE")
    print("-"*80)

    cpf_paciente = "98765432100"

    # Verifica se já existe
    paciente_existente = await get_patient_by_cpf(cpf_paciente)

    if paciente_existente:
        print(f"⚠️  Paciente já cadastrado: {paciente_existente['full_name']}")
        patient_id = paciente_existente['id']
    else:
        print("📝 Cadastrando novo paciente...")

        resultado = await create_patient({
            "full_name": "Carlos Eduardo Mendes",
            "cpf": cpf_paciente,
            "phone": "(11) 97654-3210",
            "email": "carlos.mendes@email.com",
            "birth_date": "1962-03-20",
            "age": 62,
            "gender": "M",
            "blood_type": "A+",
            "address_city": "São Paulo",
            "address_state": "SP",
            "emergency_contact_name": "Ana Mendes",
            "emergency_contact_phone": "(11) 98765-4321",
            "health_insurance": "Bradesco Saúde"
        })

        if resultado["status"] == "success":
            print(f"✅ Paciente cadastrado com sucesso!")
            print(f"   ID: {resultado['patient_id']}")
            patient_id = resultado['patient_id']
        else:
            print(f"❌ Erro: {resultado['error']}")
            return

    # ===== ETAPA 2: HISTÓRICO MÉDICO =====
    print("\n" + "-"*80)
    print("2️⃣ ATUALIZAÇÃO DE HISTÓRICO MÉDICO")
    print("-"*80)

    print("📋 Registrando histórico médico...")

    resultado = await update_patient_history(patient_id, {
        "comorbidities": [
            "Hipertensão Arterial Sistêmica",
            "Diabetes Mellitus Tipo 2",
            "Dislipidemia",
            "Obesidade (IMC 32)"
        ],
        "allergies": ["AAS (reação cutânea)"],
        "current_medications": [
            {"name": "Losartana", "dose": "100mg", "frequency": "1x ao dia"},
            {"name": "Hidroclorotiazida", "dose": "25mg", "frequency": "1x ao dia"},
            {"name": "Metformina", "dose": "1000mg", "frequency": "12/12h"},
            {"name": "Atorvastatina", "dose": "40mg", "frequency": "1x ao dia (noite)"}
        ],
        "smoker": True,
        "smoking_pack_years": 30,
        "alcohol_use": "Social",
        "physical_activity": "Sedentário",
        "cardiac_risk_factors": [
            "HAS",
            "DM tipo 2",
            "Dislipidemia",
            "Tabagismo ativo",
            "Obesidade",
            "Sedentarismo"
        ],
        "previous_cardiac_events": []
    })

    if resultado["status"] == "success":
        print("✅ Histórico atualizado com sucesso!")
    else:
        print(f"❌ Erro: {resultado['error']}")

    # ===== ETAPA 3: CONSULTA (TRANSCRIÇÃO) =====
    print("\n" + "-"*80)
    print("3️⃣ CONSULTA MÉDICA - TRANSCRIÇÃO")
    print("-"*80)

    transcricao_consulta = """
    Paciente masculino, 62 anos, comparece ao consultório com queixa de
    dispneia aos esforços progressiva há 3 semanas.

    HDA: Refere que há 3 semanas iniciou dispneia aos grandes esforços (subir 2 lances
    de escada). Na última semana, passou a apresentar aos médios esforços (caminhar 1 quarteirão
    em aclive). Há 2 dias, apresentou dispneia aos mínimos esforços (vestir-se). Hoje pela
    manhã apresentou episódio de dispneia paroxística noturna. Nega dor torácica. Refere
    edema de membros inferiores até joelhos há 1 semana, pior ao final do dia. Nega febre.

    HPP: Hipertenso há 15 anos, diabético há 10 anos. Nega IAM prévio, AVC ou outras
    complicações cardiovasculares.

    Medicações em uso: Losartana 100mg/dia, Hidroclorotiazida 25mg/dia, Metformina 1000mg 12/12h,
    Atorvastatina 40mg/dia.

    Hábitos: Tabagista (1 maço/dia há 30 anos). Etilista social. Sedentário.

    Exame físico:
    - Estado geral: Paciente em regular estado geral, dispneico aos mínimos esforços
    - PA: 150/90 mmHg (sentado)
    - FC: 110 bpm (irregular)
    - FR: 24 irpm
    - SpO2: 92% em ar ambiente
    - Peso: 95kg, Altura: 1.70m, IMC: 32.9 kg/m²
    - Turgência jugular: +3/4+
    - Ausculta cardíaca: Ritmo irregular, sopro sistólico +2/6+ em foco mitral
    - Ausculta pulmonar: Estertores crepitantes em bases bilateralmente
    - Abdome: Hepatomegalia dolorosa (fígado palpável 4cm abaixo do RCD)
    - Membros inferiores: Edema +3/4+ até raiz de coxas, cacifo positivo
    - Pulsos pedioso e tibial posterior presentes e simétricos

    Impressão clínica: Insuficiência cardíaca descompensada, possível FA de alta resposta.
    """

    print("📄 Transcrição da consulta recebida")
    print(f"   Caracteres: {len(transcricao_consulta)}")

    # ===== ETAPA 4: ANÁLISE COM CREWAI =====
    print("\n" + "-"*80)
    print("4️⃣ ANÁLISE COM CREWAI MULTI-AGENTE")
    print("-"*80)

    print("\n🤖 Iniciando análise cardiológica...")
    print("   Coordenador + Especialistas trabalhando...")
    print("   ⏳ Aguarde 30-60 segundos...\n")

    case_id = f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    resultado_analise = await analyze_cardio_case(
        transcription=transcricao_consulta,
        doctor_name="Dr. Pedro Henrique Cardoso",
        case_id=case_id
    )

    if resultado_analise["status"] == "success":
        print("✅ Análise concluída com sucesso!\n")

        analise = resultado_analise["analysis"]

        # Mostra prévia
        print("="*80)
        print("📊 ANÁLISE CARDIOLÓGICA (PREVIEW)")
        print("="*80)
        print(analise[:500] + "...")
        print("\n[... análise completa ...]\n")

    else:
        print(f"❌ Erro na análise: {resultado_analise.get('error')}")
        return

    # ===== ETAPA 5: SALVAMENTO NO BANCO =====
    print("-"*80)
    print("5️⃣ SALVAMENTO NO BANCO DE DADOS")
    print("-"*80)

    print("💾 Salvando caso no Supabase...")

    resultado_save = await save_case_analysis(
        case_id=case_id,
        doctor_name="Dr. Pedro Henrique Cardoso",
        doctor_crm="54321-SP",
        transcription=transcricao_consulta,
        analysis_result=analise,
        patient_id=str(patient_id)
    )

    if resultado_save["status"] == "success":
        print("✅ Caso salvo com sucesso no banco de dados!")
        print(f"   Case ID: {case_id}")
    else:
        print(f"❌ Erro ao salvar: {resultado_save.get('error')}")

    # ===== RESUMO FINAL =====
    print("\n" + "="*80)
    print("✅ FLUXO COMPLETO EXECUTADO COM SUCESSO!")
    print("="*80)

    print(f"""
📊 RESUMO DO ATENDIMENTO:

👤 Paciente:
   Nome: Carlos Eduardo Mendes
   CPF: {cpf_paciente}
   ID: {patient_id}

📋 Histórico:
   ✅ Comorbidades registradas
   ✅ Medicações atualizadas
   ✅ Fatores de risco documentados

🏥 Consulta:
   ✅ Transcrição processada
   ✅ Análise multi-agente concluída
   ✅ Relatório SOAP gerado

💾 Armazenamento:
   ✅ Caso salvo: {case_id}
   ✅ Vínculo paciente-análise criado

🔍 Próximos passos:
   1. Revisar análise completa
   2. Solicitar exames recomendados
   3. Implementar conduta sugerida
   4. Agendar retorno

📄 Análise completa disponível em:
   - API: GET /api/v1/cases/{case_id}
   - Banco: Tabela case_analyses
    """)

    print("="*80)
    print("\n💡 Dica: Execute novamente para testar com paciente já cadastrado!")


if __name__ == "__main__":
    print("\n🏥 CLINICAPRO CARDIO")
    print("Demonstração de Fluxo Completo End-to-End\n")

    asyncio.run(fluxo_completo())
