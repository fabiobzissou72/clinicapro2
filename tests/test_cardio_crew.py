"""
Teste do Cardio Crew
Executa análise de caso clínico de exemplo
"""

import asyncio
import sys
import os
from pathlib import Path

# Adiciona diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
load_dotenv()

from app.crews.cardio_crew import analyze_cardio_case


# ===== CASOS CLÍNICOS DE TESTE =====

CASO_IAM = """
Paciente masculino, 58 anos, hipertenso e diabético tipo 2 há 10 anos.

Queixa principal: Dor torácica há 2 horas.

HDA: Refere dor torácica em aperto, de forte intensidade (8/10), iniciada há 2 horas
durante atividade física leve (subir escadas). Dor irradia para braço esquerdo e
mandíbula. Refere sudorese fria profusa e náuseas. Nega dispneia.

História patológica pregressa:
- Hipertensão arterial há 15 anos
- Diabetes mellitus tipo 2 há 10 anos
- Dislipidemia
- Ex-tabagista (parou há 5 anos, carga tabágica 20 maços/ano)

Medicações em uso:
- Losartana 50mg 12/12h
- Metformina 850mg 12/12h
- Sinvastatina 40mg à noite
- AAS 100mg/dia

Exame físico:
- PA: 160x100 mmHg
- FC: 95 bpm
- FR: 20 irpm
- SpO2: 96% em ar ambiente
- Paciente ansioso, sudoreico, pálido
- Ausculta cardíaca: RCR 2T, sem sopros
- Ausculta pulmonar: MV preservado bilateralmente, sem RA
- Extremidades: pulsos periféricos simétricos, sem edema
"""

CASO_IC = """
Paciente feminina, 72 anos, com insuficiência cardíaca conhecida.

Queixa principal: Piora da falta de ar há 3 dias.

HDA: Refere dispneia progressiva há 3 dias, inicialmente aos esforços moderados
e atualmente aos mínimos esforços e em repouso. Nega dor torácica. Refere
ortopneia (dorme com 3 travesseiros) e dispneia paroxística noturna. Relata
edema de membros inferiores progressivo e ganho de 4kg na última semana.
Nega febre.

Comorbidades:
- Insuficiência cardíaca NYHA III (etiologia isquêmica)
- IAM prévio há 3 anos
- Hipertensão arterial
- Diabetes mellitus tipo 2
- FA crônica

Medicações:
- Carvedilol 12,5mg 12/12h
- Enalapril 10mg 12/12h
- Furosemida 40mg/dia
- Espironolactona 25mg/dia
- Rivaroxabana 20mg/dia
- Metformina 850mg 12/12h

Exame físico:
- PA: 110x70 mmHg
- FC: 110 bpm (irregular)
- FR: 28 irpm
- SpO2: 88% em ar ambiente
- Turgência jugular ++/4+
- Ausculta cardíaca: arrítmico, sopro sistólico ++/6+ em foco mitral
- Ausculta pulmonar: estertores crepitantes bibasais
- Abdome: hepatomegalia dolorosa
- MMII: edema ++/4+ até raiz de coxas
"""

CASO_FA = """
Paciente masculino, 65 anos, previamente hígido.

Queixa principal: Palpitações e tontura há 6 horas.

HDA: Refere início súbito de palpitações há 6 horas, associadas a tontura e mal-estar.
Nega dor torácica, dispneia ou síncope. Nega episódios prévios semelhantes.

Comorbidades:
- Hipertensão arterial bem controlada
- Nega diabetes, dislipidemia

Medicações:
- Losartana 50mg/dia

Hábitos:
- Etilista social
- Nega tabagismo

Exame físico:
- PA: 140x90 mmHg
- FC: 140 bpm (irregular)
- FR: 16 irpm
- SpO2: 97% em ar ambiente
- Bom estado geral, lúcido e orientado
- Ausculta cardíaca: arrítmico, sem sopros
- Ausculta pulmonar: MV preservado
- Sem sinais de insuficiência cardíaca
"""


async def test_case(caso_nome: str, transcription: str):
    """Testa um caso específico"""
    print("\n" + "="*80)
    print(f"🧪 TESTANDO CASO: {caso_nome}")
    print("="*80)
    print("\n📋 TRANSCRIÇÃO:")
    print("-"*80)
    print(transcription)
    print("-"*80)
    print("\n🤖 Iniciando análise CrewAI...\n")

    try:
        result = await analyze_cardio_case(
            transcription=transcription,
            doctor_name="Dr. Teste Sistema",
            case_id=f"TEST-{caso_nome}"
        )

        if result["status"] == "success":
            print("\n" + "="*80)
            print("✅ ANÁLISE CONCLUÍDA COM SUCESSO")
            print("="*80)
            print("\n📄 RESULTADO:\n")
            print(result["analysis"])
            print("\n" + "="*80)
            return True
        else:
            print("\n❌ ERRO NA ANÁLISE:")
            print(result.get("error", "Erro desconhecido"))
            return False

    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Executa testes"""
    print("\n" + "="*80)
    print("🏥 CLINICAPRO CARDIO - TESTES DO CREW")
    print("="*80)
    print("\nConfigurações:")
    print(f"- Modelo OpenAI: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    print(f"- Ambiente: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"- OpenAI API Key: {'✅ Configurada' if os.getenv('OPENAI_API_KEY') else '❌ Não configurada'}")

    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERRO: OPENAI_API_KEY não configurada no .env")
        print("Configure antes de executar os testes.")
        return

    # Menu de escolha
    print("\n" + "="*80)
    print("Escolha qual caso testar:")
    print("1. IAM (Infarto Agudo do Miocárdio)")
    print("2. IC (Insuficiência Cardíaca Descompensada)")
    print("3. FA (Fibrilação Atrial Aguda)")
    print("4. TODOS os casos")
    print("="*80)

    choice = input("\nEscolha (1-4): ").strip()

    casos = {
        "1": ("IAM", CASO_IAM),
        "2": ("IC", CASO_IC),
        "3": ("FA", CASO_FA)
    }

    if choice in casos:
        nome, transcricao = casos[choice]
        await test_case(nome, transcricao)

    elif choice == "4":
        print("\n🔄 Executando todos os casos...\n")
        for nome, transcricao in casos.values():
            success = await test_case(nome, transcricao)
            if success:
                input("\n⏸️  Pressione ENTER para próximo caso...")

    else:
        print("❌ Opção inválida")

    print("\n" + "="*80)
    print("✅ TESTES FINALIZADOS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
