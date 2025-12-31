"""
Study Crew - Crew para Estudo Aprofundado de Casos
Análise acadêmica pós-emergência com foco em aprendizado
"""

from crewai import Crew, Task, Process
from typing import Dict, Any
import logging
from datetime import datetime

from app.agents.academic_researcher import create_academic_researcher
from app.agents.coordinator import create_coordinator

logger = logging.getLogger(__name__)


def create_study_crew(
    case_summary: str,
    diagnosis: str,
    doctor_name: str = "Médico"
) -> Crew:
    """
    Cria crew para estudo aprofundado de caso clínico

    Args:
        case_summary: Resumo do caso (paciente, queixa, achados)
        diagnosis: Diagnóstico principal dado na análise inicial
        doctor_name: Nome do médico

    Returns:
        Crew configurado para estudo aprofundado
    """

    logger.info(f"Criando Study Crew para diagnóstico: {diagnosis}")

    researcher = create_academic_researcher()
    coordinator = create_coordinator()

    # Task 1: Análise Acadêmica
    research_task = Task(
        description=f"""
        Realize análise acadêmica aprofundada deste caso:

        CASO:
        {case_summary}

        DIAGNÓSTICO PRINCIPAL:
        {diagnosis}

        Forneça:

        1. **LITERATURA RELEVANTE:**
           - Trials clínicos principais sobre este diagnóstico
           - Guidelines mais recentes (ESC 2024, ACC/AHA 2023, SBC 2024)
           - Artigos de revisão relevantes

        2. **EVIDÊNCIAS CIENTÍFICAS:**
           - Qual o nível de evidência para a conduta sugerida?
           - Existem trials que mudaram a prática recentemente?
           - Quais são os estudos de referência?

        3. **CASOS SIMILARES:**
           - Existem casos clássicos similares descritos?
           - Quais as principais séries de casos?

        4. **ALTERNATIVAS TERAPÊUTICAS:**
           - Quais outras opções existem baseadas em evidências?
           - Quando considerar cada alternativa?
           - Comparação de eficácia (se disponível)

        5. **PROGNÓSTICO BASEADO EM EVIDÊNCIAS:**
           - Scores prognósticos aplicáveis (GRACE, TIMI, NYHA, etc)
           - Dados de sobrevida e desfechos
           - Fatores que modificam prognóstico

        6. **PONTOS DE APRENDIZADO:**
           - O que este caso ensina?
           - Quais são os "red flags" importantes?
           - Armadilhas diagnósticas comuns

        IMPORTANTE:
        - Cite fontes específicas (nome do trial, ano, revista)
        - Indique nível de evidência (IA, IB, IIa, etc)
        - Foque no que é mais útil para aprendizado
        - Seja prático e aplicável
        """,
        agent=researcher,
        expected_output="Análise acadêmica aprofundada com citações"
    )

    # Task 2: Síntese Educacional
    synthesis_task = Task(
        description=f"""
        Sintetize a análise acadêmica em formato educacional claro:

        ---
        # 📚 ESTUDO APROFUNDADO DO CASO

        **Diagnóstico:** {diagnosis}
        **Médico:** Dr(a). {doctor_name}
        **Data:** {datetime.now().strftime("%d/%m/%Y")}

        ---

        ## 📖 LITERATURA DE REFERÊNCIA

        **Trials Clínicos Principais:**
        • [Trial 1]: [Ano] - [Principal achado]
        • [Trial 2]: [Ano] - [Principal achado]

        **Guidelines Atualizadas:**
        • [Guideline 1]: [Recomendação específica - Classe I/II/III]
        • [Guideline 2]: [Recomendação específica]

        **Artigos de Revisão:**
        • [Revisão 1]: [Revista, Ano] - [Foco principal]

        ---

        ## 🔬 EVIDÊNCIAS CIENTÍFICAS

        **Nível de Evidência da Conduta:**
        [Explicar qual o nível de evidência e porquê]

        **Mudanças Recentes na Prática:**
        [Trials ou guidelines que mudaram a abordagem recentemente]

        **Estudos de Referência:**
        [Estudos que todo cardiologista deve conhecer sobre este tema]

        ---

        ## 📊 ALTERNATIVAS TERAPÊUTICAS

        **Opção 1: [Nome]**
        • Evidência: [Nível - IA/IB/IIa/etc]
        • Indicação: [Quando usar]
        • Eficácia: [Dados disponíveis]

        **Opção 2: [Nome]**
        • Evidência: [Nível]
        • Indicação: [Quando usar]
        • Comparação: [vs opção 1]

        ---

        ## 📈 PROGNÓSTICO

        **Scores Aplicáveis:**
        • [Score 1]: [Como calcular e interpretar]
        • [Score 2]: [Valor prognóstico]

        **Sobrevida/Desfechos:**
        [Dados de prognóstico baseados em estudos]

        **Fatores de Melhor Prognóstico:**
        • [Fator 1]
        • [Fator 2]

        **Fatores de Pior Prognóstico:**
        • [Fator 1]
        • [Fator 2]

        ---

        ## 💡 PONTOS-CHAVE DE APRENDIZADO

        **1. [Ponto principal 1]**
        [Explicação clara e aplicável]

        **2. [Ponto principal 2]**
        [Explicação clara e aplicável]

        **3. [Ponto principal 3]**
        [Explicação clara e aplicável]

        ---

        ## ⚠️ ARMADILHAS CLÍNICAS

        **Red Flags a NÃO perder:**
        • [Red flag 1]
        • [Red flag 2]

        **Erros Comuns:**
        • [Erro comum 1]
        • [Como evitar]

        ---

        ## 📚 LEITURA RECOMENDADA

        1. [Trial principal] - [Revista, Ano]
        2. [Guideline] - [Sociedade, Ano]
        3. [Revisão] - [Revista, Ano]

        ---

        **Este estudo foi gerado para fins educacionais e aprofundamento clínico.**

        ---
        """,
        agent=coordinator,
        expected_output="Estudo de caso formatado para aprendizado",
        context=[research_task]
    )

    crew = Crew(
        agents=[researcher, coordinator],
        tasks=[research_task, synthesis_task],
        process=Process.sequential,
        verbose=False,
        memory=False,
        max_rpm=30
    )

    return crew


async def analyze_case_study(
    case_summary: str,
    diagnosis: str,
    doctor_name: str = "Médico"
) -> Dict[str, Any]:
    """
    Executa análise aprofundada de caso clínico

    Args:
        case_summary: Resumo do caso
        diagnosis: Diagnóstico principal
        doctor_name: Nome do médico

    Returns:
        Dict com estudo formatado
    """
    try:
        logger.info(f"Iniciando estudo de caso: {diagnosis}")

        crew = create_study_crew(
            case_summary=case_summary,
            diagnosis=diagnosis,
            doctor_name=doctor_name
        )

        result = crew.kickoff()

        logger.info("Estudo de caso concluído")

        return {
            "status": "success",
            "study": str(result),
            "diagnosis": diagnosis
        }

    except Exception as e:
        logger.error(f"Erro no estudo de caso: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "diagnosis": diagnosis
        }
