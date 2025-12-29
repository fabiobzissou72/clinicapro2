"""
Cardio Crew - Orquestração de Agentes Cardiológicos
Sistema multi-agente para análise de casos clínicos
"""

from crewai import Crew, Task, Process
from typing import Dict, Any
import logging
from datetime import datetime

from app.agents.coordinator import create_coordinator
from app.agents.coronary_specialist import create_coronary_specialist
from app.agents.heart_failure_specialist import create_heart_failure_specialist
from app.agents.arrhythmia_specialist import create_arrhythmia_specialist

logger = logging.getLogger(__name__)


def create_cardio_crew(transcription: str, doctor_name: str = "Médico", case_id: str = None) -> Crew:
    """
    Cria crew de cardiologia para analisar caso clínico

    Args:
        transcription: Texto transcrito da consulta
        doctor_name: Nome do médico (para personalização)
        case_id: ID do caso (para logging/tracking)

    Returns:
        Crew configurado e pronto para execução
    """

    logger.info(f"Criando Cardio Crew para caso {case_id or 'N/A'}")

    # Data atual formatada
    data_atual = datetime.now().strftime("%d/%m/%Y")

    # Cria todos os agentes
    coordinator = create_coordinator()
    coronary_spec = create_coronary_specialist()
    hf_spec = create_heart_failure_specialist()
    arrhythmia_spec = create_arrhythmia_specialist()

    # ===== TASK 1: ANÁLISE ESPECIALIZADA =====
    specialist_analysis_task = Task(
        description=f"""
        Analise a transcrição da consulta cardiológica e forneça análise clínica detalhada.

        TRANSCRIÇÃO:
        ---
        {transcription}
        ---

        ESTRUTURA DA ANÁLISE:

        1. DIAGNÓSTICOS DIFERENCIAIS:
           - Liste de 3 a 5 diagnósticos possíveis
           - Ranqueie por probabilidade (mais provável primeiro)
           - Justifique cada um com base nos achados clínicos

        2. PROPEDÊUTICA COMPLEMENTAR:
           - Exames laboratoriais indicados (priorize por urgência)
           - Exames de imagem/funcionais necessários
           - Outros procedimentos diagnósticos
           - Justifique cada exame

        3. CONDUTA TERAPÊUTICA INICIAL:
           - Medidas gerais (dieta, repouso, etc.)
           - Farmacoterapia sugerida (com doses)
           - Contraindicações a considerar
           - Baseie em Guidelines (cite ano e fonte)

        4. RED FLAGS E SINAIS DE ALARME:
           - Sinais que indicam piora clínica
           - Critérios para retorno imediato
           - Complicações potenciais a monitorar

        5. CRITÉRIOS DE INTERNAÇÃO/ENCAMINHAMENTO:
           - Quando internar?
           - Quando encaminhar para emergência?
           - Quando encaminhar para especialista?

        IMPORTANTE:
        - SEMPRE cite Guidelines específicas (ex: "ESC 2023", "SBC 2024", "ACC/AHA 2022")
        - Use terminologia médica apropriada
        - Indique nível de evidência quando disponível (IA, IB, IIa, etc.)
        - NÃO faça diagnóstico definitivo, apenas sugira possibilidades
        - Lembre-se: esta é uma ferramenta de APOIO à decisão

        FORMATO: Use markdown para organizar informações.
        """,
        agent=coronary_spec,
        expected_output="""Análise clínica especializada detalhada com:
        1. Diagnósticos diferenciais ranqueados
        2. Exames complementares priorizados
        3. Conduta terapêutica baseada em guidelines
        4. Red flags identificadas
        5. Critérios de internação/encaminhamento"""
    )

    # ===== TASK 2: SÍNTESE FINAL (SOAP) =====
    synthesis_task = Task(
        description=f"""
        Sintetize a análise especializada em relatório médico estruturado SOAP.

        TRANSCRIÇÃO ORIGINAL:
        ---
        {transcription}
        ---

        Use EXATAMENTE este formato:

        ---
        # 📋 RELATÓRIO DE ANÁLISE CARDIOLÓGICA

        **Caso:** {case_id or "N/A"}
        **Data:** {data_atual}
        **Médico Responsável:** Dr(a). {doctor_name}

        ---

        ## 📝 SUBJETIVO
        [Resumo conciso da queixa principal, história da doença atual e sintomas-chave]

        ## 🔍 OBJETIVO
        **Dados Vitais:**
        - PA: [valor]
        - FC: [valor]
        - Outros relevantes...

        **Exame Físico:**
        [Achados relevantes do exame cardiovascular e sistêmico]

        ---

        ## 🧠 AVALIAÇÃO

        ### Diagnóstico Sugerido Principal:
        [Diagnóstico mais provável]

        ### Diagnósticos Diferenciais:
        1. [DD1] - Probabilidade: [Alta/Média/Baixa]
        2. [DD2] - Probabilidade: [Alta/Média/Baixa]
        3. [DD3] - Probabilidade: [Alta/Média/Baixa]

        ### Fundamentação:
        [Breve justificativa baseada em Guidelines e evidências]

        **Nível de Urgência:** [EMERGÊNCIA/URGENTE/ROTINA]

        ---

        ## 📝 PLANO

        ### 1. Propedêutica Complementar (em ordem de prioridade):
        - [ ] Exame 1 - Justificativa
        - [ ] Exame 2 - Justificativa
        - [ ] Exame 3 - Justificativa

        ### 2. Conduta Terapêutica Sugerida:
        **Medidas Gerais:**
        - [Medida 1]
        - [Medida 2]

        **Farmacoterapia:**
        - [Droga 1] [dose] [via] [frequência] - Indicação
        - [Droga 2] [dose] [via] [frequência] - Indicação

        ### 3. Critérios de Internação/Encaminhamento:
        - **Internar se:** [critérios]
        - **Encaminhar para emergência se:** [critérios]

        ### 4. ⚠️ Red Flags para Monitorar:
        - [Sinal 1]
        - [Sinal 2]
        - [Sinal 3]

        ---

        ## 📚 REFERÊNCIAS
        - [Guideline 1 - Ano]
        - [Guideline 2 - Ano]
        - [Trial relevante - se aplicável]

        ---

        ## ⚠️ DISCLAIMER IMPORTANTE

        Este relatório foi gerado por sistema de inteligência artificial como
        **ferramenta de apoio à decisão clínica**. As sugestões apresentadas
        devem ser interpretadas e validadas pelo médico assistente.

        **A decisão final sobre diagnóstico e conduta é de responsabilidade
        exclusiva de Dr(a). {doctor_name}.**

        ---
        *Sistema: ClinicaPro Cardio v0.1*
        *Powered by CrewAI + GPT-4o-mini*
        ---

        IMPORTANTE: Use formatação markdown limpa e profissional.
        """,
        agent=coordinator,
        expected_output="""Relatório médico completo no formato SOAP modificado,
        pronto para ser apresentado ao médico assistente""",
        context=[specialist_analysis_task]
    )

    # ===== MONTA O CREW =====
    crew = Crew(
        agents=[
            coordinator,
            coronary_spec,
            hf_spec,
            arrhythmia_spec
        ],
        tasks=[
            specialist_analysis_task,
            synthesis_task
        ],
        process=Process.sequential,
        verbose=False,  # Desativa logs verbosos para melhor performance
        memory=False,
        max_rpm=30,  # Aumentado de 10 para 30 para melhor throughput
    )

    return crew


async def analyze_cardio_case(
    transcription: str,
    doctor_name: str = "Médico",
    case_id: str = None
) -> Dict[str, Any]:
    """
    Executa análise cardiológica completa

    Args:
        transcription: Texto transcrito da consulta
        doctor_name: Nome do médico
        case_id: ID do caso (opcional)

    Returns:
        Dict com análise formatada e metadados
    """
    try:
        logger.info(f"Iniciando análise do caso {case_id or 'N/A'}")

        # Cria e executa o crew
        crew = create_cardio_crew(
            transcription=transcription,
            doctor_name=doctor_name,
            case_id=case_id
        )

        # Kickoff executa todas as tasks em sequência
        result = crew.kickoff()

        logger.info("Análise concluída com sucesso")

        return {
            "status": "success",
            "analysis": str(result),
            "case_id": case_id,
            "doctor_name": doctor_name
        }

    except Exception as e:
        logger.error(f"Erro na análise do caso: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "case_id": case_id
        }
