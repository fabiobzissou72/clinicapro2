"""
Serviço de IA Avançado para Telegram Bot
Integração com CrewAI para análises inteligentes e interativas
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from openai import AsyncOpenAI

# IMPORTANTE: Carregar .env ANTES de usar os.getenv
# Força carregar o .env do diretório raiz do projeto
from pathlib import Path
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

# DEBUG: Imprimir chave carregada
_openai_key = os.getenv("OPENAI_API_KEY")
print(f"[telegram_ai_service.py] Carregando .env de: {_env_path}")
print(f"[telegram_ai_service.py] OPENAI_API_KEY carregada: ...{_openai_key[-10:] if _openai_key else 'NOT FOUND'}")

from app.database.models import (
    get_supabase_client,
    get_patient_full_profile,
    get_patient_by_cpf,
    create_patient,
    update_patient_history,
    save_case_analysis
)
from app.crews.cardio_crew import analyze_cardio_case
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Cliente OpenAI para análises rápidas
_openai_key = os.getenv("OPENAI_API_KEY")
if not _openai_key:
    logger.error("OPENAI_API_KEY não encontrada nas variáveis de ambiente!")
else:
    logger.info(f"🔑 OpenAI Key carregada: ...{_openai_key[-10:]}")
openai_client = AsyncOpenAI(api_key=_openai_key)


class TelegramAIService:
    """Serviço de IA para o bot do Telegram"""

    def __init__(self):
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def interpret_user_intent(self, text: str) -> Dict[str, Any]:
        """
        Interpreta a intenção do usuário usando IA

        Args:
            text: Texto do usuário

        Returns:
            Dict com intent e parâmetros extraídos
        """
        try:
            prompt = f"""
Você é um assistente médico inteligente. Analise a mensagem do médico e identifique a intenção:

Mensagem: "{text}"

Classifique a intenção em uma das seguintes categorias:
1. "create_prontuario" - Médico quer criar/registrar um prontuário
2. "search_patient" - Médico quer buscar informações de um paciente
3. "clinical_question" - Médico tem uma pergunta clínica/científica
4. "update_history" - Médico quer atualizar histórico de paciente
5. "general_analysis" - Análise geral de caso clínico

Se for busca de paciente, tente extrair:
- CPF (se mencionado)
- Nome do paciente (se mencionado)

Se for prontuário ou análise, identifique:
- Se há dados clínicos suficientes
- Se precisa de mais informações

Responda em JSON puro (sem markdown):
{{
  "intent": "categoria",
  "confidence": 0.0-1.0,
  "extracted_data": {{
    "cpf": "opcional",
    "patient_name": "opcional",
    "has_clinical_data": true/false
  }},
  "needs_more_info": true/false,
  "suggested_question": "pergunta para coletar mais dados se necessário"
}}
"""

            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            import json
            result_text = response.choices[0].message.content.strip()

            # Remove markdown se existir
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            result = json.loads(result_text)

            return result

        except Exception as e:
            logger.error(f"Erro ao interpretar intenção: {e}")
            return {
                "intent": "general_analysis",
                "confidence": 0.5,
                "extracted_data": {},
                "needs_more_info": False
            }

    async def search_patient_by_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Busca paciente por CPF ou nome usando IA para extrair informação

        Args:
            query: Query de busca (ex: "buscar paciente João Silva", "CPF 123.456.789-00")

        Returns:
            Dados do paciente se encontrado
        """
        try:
            # Extrai CPF se houver
            import re
            cpf_match = re.search(r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', query)

            if cpf_match:
                cpf = cpf_match.group(0)
                patient = await get_patient_by_cpf(cpf)
                if patient:
                    return patient

            # Se não encontrou por CPF, busca por nome no Supabase
            supabase = get_supabase_client()

            # Extrai possível nome do paciente
            words = query.lower().replace("paciente", "").replace("buscar", "").strip()

            response = supabase.table("patients")\
                .select("*")\
                .ilike("full_name", f"%{words}%")\
                .limit(1)\
                .execute()

            if response.data:
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"Erro ao buscar paciente: {e}")
            return None

    async def get_patient_summary(self, patient_id: str) -> str:
        """
        Gera resumo inteligente do paciente usando IA

        Args:
            patient_id: ID do paciente

        Returns:
            Resumo formatado do paciente
        """
        try:
            profile = await get_patient_full_profile(patient_id)

            if profile["status"] == "error":
                return "❌ Paciente não encontrado"

            patient = profile["patient"]
            history = profile.get("history", {})
            recent_cases = profile.get("recent_cases", [])

            # Monta contexto para IA
            context = f"""
DADOS DO PACIENTE:
- Nome: {patient['full_name']}
- Idade: {patient.get('age', 'N/A')} anos
- Sexo: {patient.get('gender', 'N/A')}
- Tipo sanguíneo: {patient.get('blood_type', 'N/A')}

HISTÓRICO:
- Comorbidades: {history.get('comorbidities', [])}
- Alergias: {history.get('allergies', [])}
- Medicações atuais: {history.get('current_medications', [])}
- Fatores de risco cardíaco: {history.get('cardiac_risk_factors', [])}

CONSULTAS RECENTES: {len(recent_cases)} consultas registradas
"""

            # Gera resumo com IA
            prompt = f"""
Você é um assistente médico. Gere um resumo clínico conciso e profissional do paciente:

{context}

Formato do resumo:
📋 RESUMO DO PACIENTE

**Identificação:** [nome, idade, sexo]
**Perfil de Risco:** [avaliação breve dos fatores de risco]
**Histórico Relevante:** [comorbidades e alergias principais]
**Acompanhamento:** [quantas consultas, última consulta se houver]

Seja objetivo e clínico.
"""

            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )

            summary = response.choices[0].message.content.strip()

            return summary

        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            return f"❌ Erro ao gerar resumo: {str(e)}"

    async def create_prontuario_from_voice(
        self,
        transcription: str,
        doctor_name: str,
        doctor_crm: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria prontuário a partir de transcrição de voz
        Extrai dados do paciente e cria análise completa

        Args:
            transcription: Texto transcrito
            doctor_name: Nome do médico
            doctor_crm: CRM do médico

        Returns:
            Resultado da criação do prontuário
        """
        try:
            # Usa IA para extrair dados estruturados
            extraction_prompt = f"""
Você é um assistente médico. Extraia os seguintes dados da transcrição da consulta:

Transcrição: "{transcription}"

Identifique e extraia (se mencionado):
1. Nome do paciente
2. Idade
3. Sexo
4. Queixa principal
5. História da doença atual
6. Comorbidades
7. Medicações em uso
8. Sinais vitais (PA, FC, etc.)

Responda em JSON puro:
{{
  "patient_name": "nome ou null",
  "age": número ou null,
  "gender": "M/F/Outro ou null",
  "chief_complaint": "texto",
  "clinical_data_complete": true/false
}}
"""

            extraction_response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.2
            )

            import json
            import re
            extracted_text = extraction_response.choices[0].message.content.strip()

            # Remove markdown de forma robusta
            # Padrão: ```json\n{...}\n``` ou ```{...}``` ou apenas {...}
            extracted_text = re.sub(r'^```(?:json)?\s*', '', extracted_text)
            extracted_text = re.sub(r'\s*```$', '', extracted_text)
            extracted_text = extracted_text.strip()

            extracted = json.loads(extracted_text)

            # Gera análise com CrewAI
            case_id = str(uuid.uuid4())
            analysis_result = await analyze_cardio_case(
                transcription=transcription,
                doctor_name=doctor_name,
                case_id=case_id
            )

            if analysis_result["status"] == "error":
                return analysis_result

            # Salva no banco (se tiver dados do paciente, pode vincular)
            # Por enquanto salva sem vincular a paciente
            await save_case_analysis(
                case_id=case_id,
                doctor_name=doctor_name,
                transcription=transcription,
                analysis_result=analysis_result["analysis"],
                doctor_crm=doctor_crm,
                patient_id=None  # TODO: Criar ou vincular paciente
            )

            return {
                "status": "success",
                "case_id": case_id,
                "analysis": analysis_result["analysis"],
                "extracted_patient_data": extracted,
                "message": "✅ Prontuário criado com sucesso!"
            }

        except Exception as e:
            logger.error(f"Erro ao criar prontuário: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_clinical_suggestion(
        self,
        patient_history: str,
        current_symptoms: str
    ) -> str:
        """
        Gera sugestões clínicas baseadas em histórico e sintomas

        Args:
            patient_history: Histórico do paciente
            current_symptoms: Sintomas atuais

        Returns:
            Sugestões clínicas formatadas
        """
        try:
            prompt = f"""
Você é um cardiologista experiente. Com base no histórico e sintomas atuais, forneça sugestões clínicas:

HISTÓRICO DO PACIENTE:
{patient_history}

SINTOMAS ATUAIS:
{current_symptoms}

Forneça:
1. Hipóteses diagnósticas principais (top 3)
2. Exames complementares sugeridos
3. Condutas iniciais recomendadas
4. Sinais de alerta (red flags)

Formato: Use emojis para organizar, seja objetivo e baseado em guidelines.
"""

            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um cardiologista especialista. Forneça sugestões baseadas em evidências e guidelines."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )

            suggestions = response.choices[0].message.content.strip()

            return f"""
💡 SUGESTÕES CLÍNICAS

{suggestions}

⚠️ IMPORTANTE: Estas são sugestões de apoio à decisão.
A avaliação clínica e conduta final são do médico assistente.
"""

        except Exception as e:
            logger.error(f"Erro ao gerar sugestões: {e}")
            return f"❌ Erro ao gerar sugestões: {str(e)}"

    async def chat_with_doctor(self, message: str, is_logged_in: bool = False, doctor_name: str = None) -> Dict[str, Any]:
        """
        Conversação inteligente com o médico

        Args:
            message: Mensagem do médico
            is_logged_in: Se o médico está logado
            doctor_name: Nome do médico

        Returns:
            Dict com 'response' (texto da resposta) e 'action' (sugestão de ação)
        """
        try:
            if is_logged_in:
                system_prompt = f"""
Você é a IA assistente do ClinicaPro Cardio, conversando com {doctor_name or 'um médico'}.

O médico já está logado no sistema. Você deve:
- Ser amigável, profissional e prestativo
- Se for uma saudação casual (oi, olá, tudo bem), responda de forma amigável e explique as funcionalidades
- Se for dados clínicos curtos, peça mais detalhes educadamente
- Explique que ele pode:
  * Enviar áudio descrevendo a consulta → você transcreve e cria prontuário automaticamente
  * Enviar dados do paciente (sintomas, histórico) → você gera análise cardiológica completa
  * Usar /prontuario para modo interativo guiado
  * Enviar fotos de ECG/exames para análise integrada

Seja breve (máximo 4 linhas) mas informativo.
"""
            else:
                system_prompt = """
Você é a IA assistente do ClinicaPro Cardio.

O médico NÃO está logado ainda. Você deve:
- Ser amigável, profissional e conversacional
- Se ele diz "já tenho conta", diga: "Ótimo! Use /start e clique em 🔐 Fazer Login para acessar o sistema."
- Se pergunta algo sobre funcionalidades, responda normalmente e ao final mencione que precisa fazer login
- Se for saudação casual, seja amigável e mencione brevemente as funcionalidades
- IMPORTANTE: Não fique repetindo a mesma mensagem. Varie as respostas e seja natural.

Seja breve (máximo 3 linhas).
"""

            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=200
            )

            ai_response = response.choices[0].message.content.strip()

            # Determina ação sugerida
            action = None
            if not is_logged_in:
                action = "login_required"
            elif len(message) < 30 and any(word in message.lower() for word in ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'tudo bem']):
                action = "greeting"
            else:
                action = "continue"

            return {
                "response": ai_response,
                "action": action
            }

        except Exception as e:
            logger.error(f"Erro na conversação: {e}")
            return {
                "response": "Desculpe, tive um problema. Tente novamente ou use /help para ver os comandos disponíveis.",
                "action": "error"
            }


# Instância global
telegram_ai_service = TelegramAIService()
