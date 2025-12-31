from crewai import Crew, Task, Process
from app.agents.coordinator import create_coordinator
from app.agents.coronary_specialist import create_coronary_specialist
from app.agents.heart_failure_specialist import create_heart_failure_specialist
from app.agents.arrhythmia_specialist import create_arrhythmia_specialist

def create_cardio_crew(transcription: str, doctor_name: str = "Médico"):
    """Cria crew de cardiologia - VERSÃO FINAL"""

    coordinator = create_coordinator()
    coronary_spec = create_coronary_specialist()
    hf_spec = create_heart_failure_specialist()
    arrhythmia_spec = create_arrhythmia_specialist()

    # Task 1: Triagem
    triage_task = Task(
        description=f"""
        Analise: {transcription}

        Identifique:
        1. Queixa, idade, comorbidades
        2. Sinais vitais (PA, FC)
        3. Suspeita diagnóstica
        4. Urgência
        """,
        agent=coordinator,
        expected_output="Análise inicial"
    )

    # Task 2: Especialista
    specialist_task = Task(
        description="""
        Análise especializada com:
        1. Diagnósticos diferenciais
        2. Exames necessários
        3. Conduta (Guidelines)
        4. Red flags
        """,
        agent=coronary_spec,
        expected_output="Análise especializada",
        context=[triage_task]
    )

    # Task 3: Relatório FINAL
    synthesis_task = Task(
        description=f"""
        Relatório COMPLETO e SEGURO:

        ---
        # 📋 ANÁLISE CARDIOLÓGICA

        Médico: Dr(a). {doctor_name}
        Data: [hoje]

        ---

        ## 📝 CASO

        Paciente: [idade, sexo, comorbidades]
        Queixa: [resumo]

        Sinais Vitais:
        • PA: [valor]
        • FC: [valor]

        Exame: [achados]

        ---

        ## 🎯 DIAGNÓSTICO

        Principal: [diagnóstico]

        Diferenciais:
        1. [Opção 1] - Probabilidade [Alta/Média/Baixa]
        2. [Opção 2] - Probabilidade [Alta/Média/Baixa]
        3. [Opção 3] - Probabilidade [Alta/Média/Baixa]

        Classificação:
        • NYHA [I/II/III/IV] se IC
        • GRACE [alto/médio/baixo] se IAM

        Justificativa: [explicação com guidelines]

        Urgência: 🚨 EMERGÊNCIA ou ⚠️ URGENTE ou ✅ ROTINA

        ---

        ## ⚠️ ATENÇÃO ESPECIAL

        SE PACIENTE JOVEM (<50 anos) COM PA >180/120:

        Investigar CAUSAS SECUNDÁRIAS:
        • Feocromocitoma (cefaleia + palpitações + sudorese)
        • Uso de drogas (cocaína, anfetaminas, energéticos)
        • Medicamentos (anticoncepcionais, descongestionantes)
        • Estenose renal
        • Hiperaldosteronismo

        ---

        SE PA BAIXA (<110 sistólica):
        • ❌ Evitar vasodilatadores
        • ❌ Cuidado com diuréticos
        • ❌ NÃO iniciar IECA/BRA
        • ✅ Considerar inotrópicos se PA <90
        • ✅ Suspender anti-hipertensivos

        ---

        SE PA ALTA (>180/120) + SINTOMAS NEUROLÓGICOS:
        • 🚨 EMERGÊNCIA HIPERTENSIVA
        • ⚠️ NÃO usar nitroglicerina (risco ↑ PIC)
        • ✅ Usar Labetalol ou Nicardipino

        ---

        ## ⏰ AÇÃO IMEDIATA (se emergência)

        SE IAM:

        🚨 AGORA (10min):
        • ECG 12 derivações
        • AAS 200mg VO (mastigar)
        • Clopidogrel 600mg VO
        • Troponina

        Se supra ST: Código Infarto, hemodinâmica <90min

        ---

        SE CRISE HIPERTENSIVA (PA >180/120 + sintomas):

        🚨 PRIMEIROS 10 MIN:
        • Acesso venoso (2 vias)
        • Monitorização
        • TC crânio SEM contraste (URGENTE!)
        • Fundoscopia
        • ⚠️ NÃO baixar PA antes da TC!

        DEPOIS DA TC (sem sangramento):
        • Labetalol 20mg IV (bolus)
        • Meta: ↓ 25% em 1h
        • ⚠️ Nunca >25% na 1ª hora!

        SE SINTOMAS NEUROLÓGICOS:
        • ❌ NÃO usar nitroglicerina
        • ✅ Labetalol ou Nicardipino

        ---

        SE IC DESCOMPENSADA:

        COM PA NORMAL/ALTA (>110):
        • Furosemida 40-80mg IV
        • IECA/BRA manter

        COM PA BAIXA (<110):
        • Furosemida CAUTELA (20-40mg)
        • ❌ Suspender IECA/BRA
        • Se PA <90: Dobutamina 2-5mcg/kg/min
        • UTI obrigatória

        ---

        ## 🔬 EXAMES

        ⚡ URGENTE:
        • [exame crítico 1]
        • [exame crítico 2]

        📋 PRIORITÁRIO:
        • [exame importante]

        🔍 COMPLEMENTAR:
        • [exame rotina]

        ---

        ## 💊 MEDICAÇÕES

        IMEDIATO:
        • [remédio 1]: [dose] - [motivo]
        • [remédio 2]: [dose] - [motivo]

        MANUTENÇÃO:
        • [remédio 3]: [dose] [horário]

        ❌ EVITAR:
        • [se houver contraindicações]

        Metas:
        • PA: [meta específica]
        • FC: [meta específica]

        ---

        ## 🏥 INTERNAÇÃO

        UTI se:
        • [critério]

        Enfermaria se:
        • [critério]

        Ambulatório se:
        • [critério]

        ---

        ## ⚠️ SINAIS DE ALERTA

        🚨 RETORNO IMEDIATO:
        • [red flag 1]
        • [red flag 2]

        👀 MONITORAR:
        • [atenção 1]
        • [atenção 2]

        ---

        📚 Referências: [Guidelines com ano]

        ⚠️ Sistema de apoio. Decisão: Dr(a). {doctor_name}

        ---
        """,
        agent=coordinator,
        expected_output="Relatório completo",
        context=[triage_task, specialist_task]
    )

    crew = Crew(
        agents=[coordinator, coronary_spec, hf_spec, arrhythmia_spec],
        tasks=[triage_task, specialist_task, synthesis_task],
        process=Process.sequential,
        verbose=True
    )

    return crew

async def analyze_cardio_case(transcription: str, doctor_name: str = "Médico", case_id: str = None):
    """Executa análise cardiológica completa"""
    try:
        crew = create_cardio_crew(transcription, doctor_name)
        result = crew.kickoff()

        return {
            "status": "success",
            "analysis": str(result)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
