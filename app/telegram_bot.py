"""
ClinicaPro Cardio - Telegram Bot Integration
Integra análise cardiológica com bot Telegram
"""

import os
import logging
from pathlib import Path
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import httpx
from dotenv import load_dotenv
import subprocess

# CRÍTICO: Carregar .env ANTES de importar módulos que usam variáveis de ambiente
load_dotenv()

from app.whisper_service import WhisperService
from app.image_analysis_service import image_service
from app.telegram_ai_service import telegram_ai_service
from app.database.models import (
    create_patient, get_patient_by_cpf, login_doctor, register_doctor,
    list_patients, list_case_analyses
)

# Cria diretórios temporários
TEMP_AUDIO_DIR = Path("temp_audio")
TEMP_AUDIO_DIR.mkdir(exist_ok=True)

TEMP_IMAGE_DIR = Path("temp_images")
TEMP_IMAGE_DIR.mkdir(exist_ok=True)

# Inicializa serviços
whisper_service = WhisperService(model_size="base")


# ===== HELPER PARA CONVERSÃO DE ÁUDIO =====
def convert_audio_to_wav(input_path: str, output_path: str) -> bool:
    """
    Converte áudio para WAV usando FFmpeg diretamente

    Args:
        input_path: Caminho do arquivo de entrada
        output_path: Caminho do arquivo WAV de saída

    Returns:
        True se conversão bem-sucedida, False caso contrário
    """
    try:
        # Comando FFmpeg para converter para WAV
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-acodec', 'pcm_s16le',  # Codec PCM 16-bit
            '-ar', '16000',  # Sample rate 16kHz (ideal para Whisper)
            '-ac', '1',  # Mono
            '-y',  # Sobrescrever arquivo
            output_path
        ]

        # Executa FFmpeg
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )

        return result.returncode == 0

    except Exception as e:
        logger.error(f"Erro ao converter áudio: {e}")
        return False


# Configura logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ===== FORMATAÇÃO PARA TELEGRAM =====
def format_for_telegram(text: str) -> str:
    """
    Converte markdown para formato bonito no Telegram
    """
    # Remove separadores excessivos
    text = text.replace('---\n', '')
    text = text.replace('---', '')

    # Converte headers markdown para negrito
    import re
    # ### Título -> 📌 TÍTULO
    text = re.sub(r'^### (.+)$', r'📌 *\1*', text, flags=re.MULTILINE)
    # ## Título -> ▪️ TÍTULO
    text = re.sub(r'^## (.+)$', r'\n▪️ *\1*\n', text, flags=re.MULTILINE)
    # # Título -> 🔹 TÍTULO
    text = re.sub(r'^# (.+)$', r'\n🔹 *\1*\n', text, flags=re.MULTILINE)

    # Limpa múltiplas linhas vazias
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

# Configurações
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"http://localhost:{os.getenv('PORT', 8000)}/api/v1/analyze"


# ===== HANDLERS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para comando /start"""
    user = update.effective_user

    # Verifica se já está logado
    if context.user_data and context.user_data.get('logged_in'):
        doctor = context.user_data.get('doctor')
        keyboard = [
            [InlineKeyboardButton("➕ Novo Paciente", callback_data="new_patient")],
            [InlineKeyboardButton("👥 Ver Pacientes", callback_data="list_patients")],
            [InlineKeyboardButton("📋 Ver Prontuários", callback_data="list_prontuarios")],
            [InlineKeyboardButton("🏥 Novo Prontuário", callback_data="new_prontuario")],
            [InlineKeyboardButton("📊 Dashboard", url=os.getenv("TELEGRAM_WEBAPP_URL", "https://clinicapro.fbzia.com.br"))],
            [InlineKeyboardButton("🚪 Sair", callback_data="logout")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_html(
            f"""
🏥 <b>ClinicaPro Cardio</b>

Bem-vindo de volta, <b>{doctor['name']}</b>!
CRM: {doctor['crm']}

O que você gostaria de fazer?
            """,
            reply_markup=reply_markup
        )
    else:
        # Mostra opções de login/cadastro
        keyboard = [
            [InlineKeyboardButton("🔐 Fazer Login", callback_data="show_login")],
            [InlineKeyboardButton("📝 Criar Conta", callback_data="show_register")],
            [InlineKeyboardButton("ℹ️ Sobre o Sistema", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_html(
            f"""
🏥 <b>ClinicaPro Cardio</b>

Olá, Dr(a). {user.first_name}!

Sistema de apoio à decisão cardiológica com IA.

Para começar, faça login ou crie sua conta:
            """,
            reply_markup=reply_markup
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para comando /help"""
    await update.message.reply_html(
        """
<b>📚 Ajuda - ClinicaPro Cardio</b>

<b>Formas de usar:</b>

1️⃣ <b>Enviar Foto (ECG, Raio-X):</b>
   - Tire foto do ECG/exame
   - Sistema analisa imagem com IA
   - Retorna interpretação técnica
   - Depois envie dados clínicos para análise completa

2️⃣ <b>Enviar Áudio:</b>
   - Grave áudio com dados da consulta
   - O sistema transcreve automaticamente
   - Análise é gerada pelos agentes IA

3️⃣ <b>Enviar Texto:</b>
   - Digite ou cole transcrição da consulta
   - Mínimo 50 caracteres
   - Sistema analisa e retorna SOAP

<b>O que incluir na transcrição:</b>
✅ Queixa principal
✅ História da doença atual
✅ Comorbidades
✅ Medicações em uso
✅ Dados vitais (PA, FC, etc.)
✅ Exame físico relevante

<b>Tempo de resposta:</b>
⏱️ Texto: 60-90 segundos
⏱️ Áudio: 70-120 segundos (inclui transcrição)

<b>Especialistas disponíveis:</b>
🔹 Coordenador Cardiológico
🔹 Especialista Coronariano
🔹 Especialista em IC
🔹 Especialista em Arritmias
        """
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para comando /about"""
    await update.message.reply_html(
        """
<b>ℹ️ Sobre o ClinicaPro Cardio</b>

<b>Versão:</b> 0.1.0-beta

<b>Tecnologias:</b>
• CrewAI (multi-agent system)
• GPT-4o-mini (OpenAI)
• FastAPI (backend)
• Supabase (database)
• Qdrant (vector DB)
• Python Telegram Bot

<b>Desenvolvedores:</b>
Sistema desenvolvido para apoiar cardiologistas
na análise de casos clínicos complexos.

<b>⚠️ Disclaimer:</b>
Este é um sistema de apoio à decisão clínica.
NÃO substitui avaliação médica. A decisão
final sobre diagnóstico e conduta é sempre
do médico assistente.

<b>Privacidade:</b>
Dados são armazenados de forma segura e
criptografada em conformidade com LGPD.
        """
    )


async def search_patient_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para comando /paciente [nome ou CPF]"""
    query = " ".join(context.args) if context.args else None

    if not query:
        await update.message.reply_text(
            "❓ Como usar:\n\n"
            "/paciente [nome ou CPF]\n\n"
            "Exemplos:\n"
            "• /paciente João Silva\n"
            "• /paciente 123.456.789-00"
        )
        return

    status_msg = await update.message.reply_text("🔍 Buscando paciente...")

    try:
        patient = await telegram_ai_service.search_patient_by_query(query)

        if not patient:
            await status_msg.edit_text(
                f"❌ Paciente não encontrado: {query}\n\n"
                "Tente buscar por:\n"
                "• Nome completo\n"
                "• CPF (com ou sem máscara)"
            )
            return

        # Gera resumo do paciente
        summary = await telegram_ai_service.get_patient_summary(patient["id"])

        await status_msg.edit_text(summary)

    except Exception as e:
        logger.error(f"Erro ao buscar paciente: {e}")
        await status_msg.edit_text(f"❌ Erro ao buscar paciente: {str(e)[:100]}")


async def prontuario_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para comando /prontuario - cria prontuário interativo"""
    await update.message.reply_text(
        "📋 CRIAR PRONTUÁRIO\n\n"
        "Você pode criar um prontuário de 3 formas:\n\n"
        "1️⃣ **Por voz:** Grave um áudio ditando a consulta\n"
        "2️⃣ **Por texto:** Digite ou cole os dados clínicos\n"
        "3️⃣ **Por foto + dados:** Envie foto de ECG/exame + dados clínicos\n\n"
        "💡 Inclua sempre:\n"
        "• Queixa principal\n"
        "• História da doença\n"
        "• Dados vitais\n"
        "• Exame físico\n\n"
        "Envie agora os dados da consulta:"
    )

    # Marca contexto para próxima mensagem
    if not context.user_data:
        context.user_data = {}
    context.user_data['awaiting_prontuario'] = True


async def suggest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para comando /sugestao - sugestões clínicas"""
    await update.message.reply_text(
        "💡 SUGESTÕES CLÍNICAS\n\n"
        "Envie os dados do paciente:\n"
        "• Histórico relevante\n"
        "• Sintomas atuais\n"
        "• Exames disponíveis\n\n"
        "A IA irá gerar sugestões de diagnóstico e conduta."
    )

    if not context.user_data:
        context.user_data = {}
    context.user_data['awaiting_suggestion'] = True


async def test_api_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para comando /testar - testa conexão com API"""
    status_msg = await update.message.reply_text("🔍 Testando conexão com API...")

    try:
        # Testa endpoint de health check
        api_base = API_URL.replace('/api/v1/analyze', '')

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Tenta acessar a raiz da API
            response = await client.get(f"{api_base}/docs")

        if response.status_code == 200:
            await status_msg.edit_text(
                f"✅ API está rodando!\n\n"
                f"🌐 URL: {api_base}\n"
                f"📊 Status: {response.status_code}\n\n"
                f"Você pode cadastrar pacientes normalmente."
            )
        else:
            await status_msg.edit_text(
                f"⚠️ API respondeu mas com erro:\n\n"
                f"🌐 URL: {api_base}\n"
                f"📊 Status: {response.status_code}\n\n"
                f"Verifique o servidor."
            )

    except httpx.ConnectError:
        await status_msg.edit_text(
            f"❌ API NÃO ESTÁ RODANDO!\n\n"
            f"🌐 URL tentada: {api_base}\n\n"
            f"🔧 Para iniciar a API:\n"
            f"1. Abra um terminal\n"
            f"2. Execute: python -m app.main\n"
            f"3. Aguarde mensagem 'Uvicorn running'\n"
            f"4. Tente cadastrar novamente"
        )

    except Exception as e:
        await status_msg.edit_text(
            f"❌ Erro ao testar API:\n\n"
            f"{str(e)[:200]}"
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensagens de áudio/voz"""
    status_msg = await update.message.reply_text(
        "🎤 Áudio recebido! Processando...\n\n"
        "⏳ Etapa 1/3: Baixando áudio..."
    )

    voice_file = None
    audio_file_path = None

    try:
        # Detecta tipo de áudio (voice note ou audio file)
        if update.message.voice:
            audio_obj = update.message.voice
            file_ext = "ogg"
        elif update.message.audio:
            audio_obj = update.message.audio
            # Pega extensão do arquivo de áudio (mp3, m4a, etc.)
            file_ext = audio_obj.file_name.split('.')[-1] if audio_obj.file_name else "mp3"
        else:
            raise ValueError("Nenhum áudio encontrado na mensagem")

        # Baixa arquivo de áudio do Telegram
        voice_file = await audio_obj.get_file()
        file_id = audio_obj.file_id
        audio_file_path = TEMP_AUDIO_DIR / f"{file_id}.{file_ext}"
        await voice_file.download_to_drive(audio_file_path)

        logger.info(f"Áudio baixado: {audio_file_path}")

        # Transcreve com Whisper (aceita vários formatos: OGG, MP3, WAV, M4A)
        await status_msg.edit_text(
            "🎤 Áudio recebido! Processando...\n\n"
            "⏳ Etapa 2/2: Transcrevendo com IA...\n"
            "(Isso pode levar alguns segundos)"
        )

        result = whisper_service.transcribe(str(audio_file_path), language="pt")
        logger.info(f"Whisper retornou - Tipo: {type(result)}, Conteúdo: {result if isinstance(result, dict) else str(result)[:100]}")

        # Verifica se o resultado é um dicionário válido
        if not isinstance(result, dict):
            logger.error(f"Erro: whisper retornou tipo inválido: {type(result)}")
            raise Exception(f"Formato de resultado inválido do Whisper: {type(result)}")

        if result.get("status") != "success":
            error_msg = result.get("error", "Erro desconhecido na transcrição")
            logger.error(f"Erro na transcrição: {error_msg}")
            raise Exception(error_msg)

        transcription = result.get("text", "").strip()
        if not transcription:
            raise Exception("Transcrição vazia - áudio pode estar corrompido ou sem fala")

        logger.info(f"Transcrição concluída: {len(transcription)} caracteres")

        # Valida transcrição
        if len(transcription) < 20:
            await status_msg.edit_text(
                "⚠️ Áudio muito curto ou não compreensível.\n\n"
                "Por favor, grave novamente com:\n"
                "• Queixa principal\n"
                "• Dados vitais\n"
                "• Exame físico\n"
                "• Comorbidades"
            )
            return

        # Mostra transcrição para confirmação
        await status_msg.edit_text(
            f"✅ Transcrição concluída!\n\n"
            f"📝 Texto transcrito ({len(transcription)} caracteres):\n\n"
            f'"{transcription[:200]}{"..." if len(transcription) > 200 else ""}"\n\n'
            f"🤖 Analisando com especialistas IA..."
        )

        # CHAMA DIRETO O CREWAI (SEM API) - igual ao handle_text
        user = update.effective_user
        doctor_name = f"Dr(a). {user.first_name} {user.last_name or ''}".strip()

        logger.info(f"🤖 Analisando áudio DIRETO com CrewAI para {doctor_name}")

        # Importa e chama o crew direto
        from app.crews.cardio_crew import analyze_cardio_case

        # Análise direto
        result = await analyze_cardio_case(
            transcription=transcription,
            doctor_name=doctor_name
        )

        if result and result.get('status') == 'success':
            # Extrai a análise
            analysis_text = result.get('analysis', '')

            # Formata para Telegram
            analysis_formatted = format_for_telegram(analysis_text)

            # Edita mensagem de status
            await status_msg.edit_text("✅ Análise concluída com CrewAI!")

            # Envia análise (dividida se necessário)
            MAX_LENGTH = 3900
            if len(analysis_formatted) <= MAX_LENGTH:
                await update.message.reply_text(analysis_formatted, parse_mode='Markdown')
            else:
                num_parts = (len(analysis_formatted) + MAX_LENGTH - 1) // MAX_LENGTH
                for i in range(num_parts):
                    start = i * MAX_LENGTH
                    end = min((i + 1) * MAX_LENGTH, len(analysis_formatted))
                    part = analysis_formatted[start:end]

                    prefix = f"📄 *Parte {i+1}/{num_parts}*\n\n"
                    message = prefix + part

                    if len(message) > 4096:
                        message = message[:4090] + "..."

                    await update.message.reply_text(message, parse_mode='Markdown')

            # ===== PERGUNTA SE QUER SALVAR O PRONTUÁRIO =====
            context.user_data['temp_transcription'] = transcription
            context.user_data['temp_analysis'] = analysis_text
            context.user_data['temp_doctor_name'] = doctor_name

            keyboard = [
                [InlineKeyboardButton("✅ Salvar Prontuário", callback_data="save_prontuario_confirm")],
                [InlineKeyboardButton("❌ Descartar", callback_data="discard_prontuario")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "💾 <b>Deseja salvar este prontuário?</b>\n\n"
                "Se salvar, vou perguntar sobre os dados do paciente.",
                parse_mode='HTML',
                reply_markup=reply_markup
            )

        else:
            await status_msg.edit_text(
                f"❌ Erro na análise.\n\n"
                f"Tente novamente em alguns instantes."
            )

    except httpx.TimeoutException:
        await status_msg.edit_text(
            "⏱️ Timeout na análise.\n\n"
            "O caso pode ser muito complexo. Tente novamente."
        )

    except Exception as e:
        logger.error(f"Erro ao processar áudio: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ Erro ao processar áudio: {str(e)[:100]}\n\n"
            "Tente enviar novamente ou use texto."
        )

    finally:
        # Limpa arquivo temporário
        try:
            if audio_file_path and audio_file_path.exists():
                audio_file_path.unlink()
            logger.info("Arquivo temporário removido")
        except Exception as e:
            logger.warning(f"Erro ao remover arquivo temp: {e}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para imagens/fotos (ECG, raio-x, etc.)"""
    status_msg = await update.message.reply_text(
        "📸 Imagem recebida! Processando...\n\n"
        "⏳ Etapa 1/3: Baixando imagem..."
    )

    photo_path = None

    try:
        # Pega a maior resolução da foto
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()

        # Salva imagem temporária
        file_id = photo.file_id
        photo_path = TEMP_IMAGE_DIR / f"{file_id}.jpg"
        await photo_file.download_to_drive(photo_path)

        logger.info(f"Imagem baixada: {photo_path}")

        # Verifica se há legenda com contexto clínico
        caption = update.message.caption or ""

        # Analisa imagem com GPT-4 Vision
        await status_msg.edit_text(
            "📸 Imagem recebida! Processando...\n\n"
            "⏳ Etapa 2/3: Analisando imagem com IA...\n"
            "(Isso pode levar alguns segundos)"
        )

        # Detecta tipo de imagem pela legenda ou assume ECG
        if "raio" in caption.lower() or "rx" in caption.lower():
            result = image_service.analyze_generic_medical_image(
                str(photo_path),
                image_type="raio-x",
                additional_context=caption if caption else None
            )
        elif "eco" in caption.lower():
            result = image_service.analyze_generic_medical_image(
                str(photo_path),
                image_type="ecocardiograma",
                additional_context=caption if caption else None
            )
        else:
            # Assume ECG por padrão
            result = image_service.analyze_ecg(
                str(photo_path),
                additional_context=caption if caption else None
            )

        if result["status"] != "success":
            raise Exception(result.get("error", "Erro desconhecido na análise"))

        image_analysis = result["analysis"]
        logger.info(f"Análise de imagem concluída: {result['tokens_used']} tokens")

        # Mostra análise da imagem
        await status_msg.edit_text(
            f"✅ Imagem analisada!\n\n"
            f"📊 Análise inicial enviando...\n"
            f"💡 Tokens usados: {result['tokens_used']}"
        )

        # Divide resposta se for muito grande
        MAX_LENGTH = 4000
        if len(image_analysis) <= MAX_LENGTH:
            await update.message.reply_text(
                f"📊 ANÁLISE DA IMAGEM:\n\n{image_analysis}"
            )
        else:
            parts = [image_analysis[i:i+MAX_LENGTH] for i in range(0, len(image_analysis), MAX_LENGTH)]
            for i, part in enumerate(parts, 1):
                prefix = f"📊 Parte {i}/{len(parts)}:\n\n"
                message = prefix + part
                if len(message) > 4096:
                    message = prefix + part[:4096-len(prefix)]
                await update.message.reply_text(message)

        # Pergunta se quer análise completa com os agentes
        await update.message.reply_text(
            "🤖 Deseja que os especialistas IA façam uma análise completa "
            "integrando esta imagem com dados clínicos?\n\n"
            "Se sim, envie uma mensagem de texto com:\n"
            "• Sintomas do paciente\n"
            "• Dados vitais\n"
            "• História clínica\n\n"
            "A análise da imagem acima será integrada automaticamente."
        )

        # Salva análise no contexto do usuário para próxima mensagem
        if not context.user_data:
            context.user_data = {}
        context.user_data['last_image_analysis'] = image_analysis

    except Exception as e:
        logger.error(f"Erro ao processar imagem: {e}", exc_info=True)
        error_msg = str(e)[:200]
        await status_msg.edit_text(
            f"❌ Erro ao processar imagem: {error_msg}\n\n"
            "Tente enviar novamente ou use texto."
        )

    finally:
        # Limpa arquivo temporário
        try:
            if photo_path and photo_path.exists():
                photo_path.unlink()
            logger.info("Arquivo temporário removido")
        except Exception as e:
            logger.warning(f"Erro ao remover arquivo temp: {e}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensagens de texto"""
    transcription = update.message.text

    # === FLUXO DE LOGIN/CADASTRO ===
    if context.user_data and 'awaiting' in context.user_data:
        awaiting = context.user_data.get('awaiting')

        # LOGIN - Email
        if awaiting == 'login_email':
            context.user_data['login_email'] = transcription
            context.user_data['awaiting'] = 'login_password'
            await update.message.reply_text("🔐 Agora digite sua senha:")
            return

        # LOGIN - Senha
        elif awaiting == 'login_password':
            email = context.user_data.get('login_email')
            password = transcription

            status_msg = await update.message.reply_text("🔄 Autenticando...")

            try:
                # LOGIN DIRETO NO BANCO (SEM API)
                result = await login_doctor(email, password)

                if result["status"] == "success":
                    context.user_data['logged_in'] = True
                    context.user_data['doctor'] = result['doctor']
                    context.user_data.pop('awaiting', None)
                    context.user_data.pop('login_email', None)

                    await status_msg.edit_text(
                        f"✅ Login realizado!\n\n"
                        f"Bem-vindo, <b>{result['doctor']['name']}</b>!\n\n"
                        f"Use /start para ver o menu principal.",
                        parse_mode='HTML'
                    )
                else:
                    await status_msg.edit_text(
                        f"❌ {result['error']}\n\n"
                        f"Use /start para tentar novamente."
                    )
                    context.user_data.clear()

            except Exception as e:
                logger.error(f"Erro no login: {e}")
                await status_msg.edit_text(f"❌ Erro: {str(e)[:100]}")
                context.user_data.clear()

            return

        # CADASTRO - Nome
        elif awaiting == 'register_name':
            context.user_data['reg_name'] = transcription
            context.user_data['awaiting'] = 'register_crm'
            await update.message.reply_text("📝 Digite seu CRM (ex: 12345-SP):")
            return

        # CADASTRO - CRM
        elif awaiting == 'register_crm':
            context.user_data['reg_crm'] = transcription
            context.user_data['awaiting'] = 'register_email'
            await update.message.reply_text("📝 Digite seu email:")
            return

        # CADASTRO - Email
        elif awaiting == 'register_email':
            context.user_data['reg_email'] = transcription
            context.user_data['awaiting'] = 'register_password'
            await update.message.reply_text("📝 Digite uma senha (mínimo 8 caracteres):")
            return

        # CADASTRO - Senha
        elif awaiting == 'register_password':
            if len(transcription) < 8:
                await update.message.reply_text("❌ Senha deve ter no mínimo 8 caracteres.\n\nDigite novamente:")
                return

            status_msg = await update.message.reply_text("🔄 Cadastrando...")

            try:
                # CADASTRO DIRETO NO BANCO (SEM API)
                result = await register_doctor({
                    "name": context.user_data.get('reg_name'),
                    "crm": context.user_data.get('reg_crm'),
                    "email": context.user_data.get('reg_email'),
                    "password": transcription,
                    "specialty": "Cardiologia"
                })

                if result["status"] == "success":
                    await status_msg.edit_text(
                        "✅ Cadastro realizado com sucesso!\n\n"
                        "Use /start para fazer login."
                    )
                    context.user_data.clear()
                else:
                    await status_msg.edit_text(
                        f"❌ {result['error']}\n\n"
                        f"Use /start para tentar novamente."
                    )
                    context.user_data.clear()

            except Exception as e:
                logger.error(f"Erro no cadastro: {e}")
                await status_msg.edit_text(f"❌ Erro ao cadastrar: {str(e)[:100]}")
                context.user_data.clear()

            return

        # CRIAR PACIENTE PARA PRONTUÁRIO - Formato: Nome | CPF | Data Nascimento
        elif awaiting == 'new_patient_data_for_pront':
            try:
                # Parse do formato: Nome | CPF | Data Nascimento
                parts = [p.strip() for p in transcription.split('|')]

                if len(parts) < 2:
                    await update.message.reply_text(
                        "❌ Formato incorreto.\n\n"
                        "Use: Nome Completo | CPF | Data Nascimento\n"
                        "Exemplo: João Silva | 12345678901 | 15/03/1965"
                    )
                    return

                full_name = parts[0]
                cpf = parts[1].replace('.', '').replace('-', '').strip()
                birth_date = None
                age = None

                # Se forneceu data de nascimento
                if len(parts) >= 3:
                    try:
                        from datetime import datetime
                        birth_date = datetime.strptime(parts[2].strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
                    except:
                        # Tenta interpretar como idade
                        try:
                            age = int(parts[2].strip())
                        except:
                            pass

                status_msg = await update.message.reply_text("💾 Criando paciente...")

                # Cria paciente no banco
                from app.database.models import create_patient

                patient_data = {
                    "full_name": full_name,
                    "cpf": cpf,
                    "birth_date": birth_date,
                    "age": age
                }

                result = await create_patient(patient_data)

                if result["status"] == "success":
                    patient_id = result["data"]["id"]

                    # Salva prontuário vinculado
                    await save_prontuario_with_patient(context, patient_id)

                    context.user_data.pop('awaiting', None)

                    await status_msg.edit_text(
                        f"✅ <b>Paciente criado e prontuário salvo!</b>\n\n"
                        f"Paciente: {full_name}\n"
                        f"CPF: {cpf}\n\n"
                        f"Use /start para voltar ao menu.",
                        parse_mode='HTML'
                    )
                else:
                    await status_msg.edit_text(
                        f"❌ Erro ao criar paciente: {result.get('error', 'Desconhecido')}\n\n"
                        f"Use /start para tentar novamente."
                    )

            except Exception as e:
                logger.error(f"Erro ao criar paciente: {e}")
                await update.message.reply_text(f"❌ Erro: {str(e)[:100]}")

            return

        # CRIAR PACIENTE - Nome
        elif awaiting == 'new_patient_name':
            context.user_data['patient_name'] = transcription
            context.user_data['awaiting'] = 'new_patient_cpf'
            await update.message.reply_text("📝 Digite o CPF do paciente:")
            return

        # CRIAR PACIENTE - CPF
        elif awaiting == 'new_patient_cpf':
            context.user_data['patient_cpf'] = transcription
            context.user_data['awaiting'] = 'new_patient_phone'
            await update.message.reply_text(
                "📞 Digite o telefone do paciente:\n\n"
                "(Com DDD, ex: 11987654321)\n"
                "(Ou envie 'pular' para cadastrar sem telefone)"
            )
            return

        # CRIAR PACIENTE - Telefone
        elif awaiting == 'new_patient_phone':
            if transcription.lower() != 'pular':
                context.user_data['patient_phone'] = transcription
            context.user_data['awaiting'] = 'new_patient_birth'
            await update.message.reply_text(
                "📝 Digite a data de nascimento OU idade:\n\n"
                "• <b>Data completa:</b> 15/03/1965\n"
                "• <b>Só a idade:</b> 65 (mais rápido em emergências)\n"
                "• <b>Pular:</b> envie 'pular'\n",
                parse_mode='HTML'
            )
            return

        # CRIAR PACIENTE - Data de Nascimento ou Idade
        elif awaiting == 'new_patient_birth':
            # DEBUG: Confirma que está no código novo
            logger.info("🔥 CÓDIGO NOVO - Salvando DIRETO no banco!")

            status_msg = await update.message.reply_text("💾 Salvando paciente DIRETO no banco...")

            birth_date = None
            age = None

            if transcription.lower() != 'pular':
                # Tenta parsear como data (DD/MM/AAAA)
                try:
                    from datetime import datetime
                    birth_date = datetime.strptime(transcription, "%d/%m/%Y").strftime("%Y-%m-%d")
                except:
                    # Se não for data, tenta parsear como idade (número)
                    try:
                        # Remove texto "anos" se tiver
                        age_text = transcription.lower().replace("anos", "").replace("ano", "").strip()
                        age = int(age_text)

                        # Valida idade razoável (0-150)
                        if age < 0 or age > 150:
                            raise ValueError("Idade fora do intervalo válido")
                    except:
                        await status_msg.edit_text(
                            "❌ Formato inválido.\n\n"
                            "Use:\n"
                            "• Data: 15/03/1965\n"
                            "• Idade: 65\n"
                            "• Ou envie 'pular'"
                        )
                        return

            # MODO EMERGÊNCIA - SEM BANCO
            try:
                # Limpa CPF
                cpf_clean = context.user_data.get('patient_cpf', '').replace('.', '').replace('-', '')

                # TEMPORÁRIO: Pula verificação de duplicado
                existing = None
                if False and existing:
                    await status_msg.edit_text(
                        f"⚠️ Paciente já cadastrado!\n\n"
                        f"👤 <b>{existing.get('full_name')}</b>\n"
                        f"📄 CPF: {context.user_data.get('patient_cpf')}\n\n"
                        f"Use /start para voltar ao menu.",
                        parse_mode='HTML'
                    )
                    context.user_data.clear()
                    return

                # Prepara dados
                payload = {
                    "full_name": context.user_data.get('patient_name'),
                    "cpf": cpf_clean,
                    "phone": context.user_data.get('patient_phone'),
                    "birth_date": birth_date,
                    "age": age
                }

                logger.info(f"💾 Salvando paciente direto no Supabase: {payload['full_name']}")

                # Salva direto no banco
                result = await create_patient(payload)

                if result["status"] == "success":
                    patient = result.get('data', {})
                    patient_id = result.get('patient_id', 'N/A')

                    # Calcula idade
                    age_text = ""
                    if age:
                        age_text = f", {age} anos"
                    elif patient.get('birth_date'):
                        from datetime import datetime
                        try:
                            birth = datetime.fromisoformat(patient['birth_date'])
                            today = datetime.now()
                            calc_age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                            age_text = f", {calc_age} anos"
                        except:
                            pass

                    phone_text = f"\n📞 Tel: {patient.get('phone')}" if patient.get('phone') else ""

                    await status_msg.edit_text(
                        f"✅ Paciente cadastrado com sucesso!\n\n"
                        f"👤 <b>{patient.get('full_name', payload['full_name'])}</b>{age_text}\n"
                        f"📄 CPF: {context.user_data.get('patient_cpf')}{phone_text}\n"
                        f"🆔 ID: {patient_id[:8] if patient_id != 'N/A' else 'N/A'}...\n\n"
                        f"✨ Salvo direto no banco!\n\n"
                        f"Use /start para voltar ao menu.",
                        parse_mode='HTML'
                    )

                    logger.info(f"✅ Paciente {patient_id} cadastrado com sucesso!")

                    # Limpa dados
                    context.user_data.pop('patient_name', None)
                    context.user_data.pop('patient_cpf', None)
                    context.user_data.pop('patient_phone', None)
                    context.user_data.pop('awaiting', None)

                else:
                    # Erro ao salvar
                    error = result.get('error', 'Erro desconhecido')
                    logger.error(f"❌ Erro ao cadastrar: {error}")

                    await status_msg.edit_text(
                        f"❌ Erro ao cadastrar:\n\n"
                        f"{error}\n\n"
                        f"Use /start para voltar ao menu."
                    )
                    context.user_data.clear()

            except Exception as e:
                logger.error(f"❌ Erro ao cadastrar paciente: {e}", exc_info=True)
                await status_msg.edit_text(
                    f"❌ Erro ao cadastrar:\n\n"
                    f"{str(e)[:200]}\n\n"
                    f"Contate o suporte."
                )
                context.user_data.clear()

            return

    # Verifica se está aguardando sugestão clínica
    if context.user_data and context.user_data.get('awaiting_suggestion'):
        status_msg = await update.message.reply_text("🤔 Analisando e gerando sugestões...")

        try:
            suggestions = await telegram_ai_service.get_clinical_suggestion(
                patient_history="",
                current_symptoms=transcription
            )

            await status_msg.edit_text("✅ Sugestões geradas!")
            await update.message.reply_text(suggestions)

            # Limpa contexto
            context.user_data['awaiting_suggestion'] = False

        except Exception as e:
            logger.error(f"Erro ao gerar sugestão: {e}")
            await status_msg.edit_text(f"❌ Erro: {str(e)[:100]}")

        return

    # Verifica se está aguardando prontuário
    if context.user_data and context.user_data.get('awaiting_prontuario'):
        status_msg = await update.message.reply_text("📋 Criando prontuário...")

        try:
            user = update.effective_user
            doctor_name = f"Dr(a). {user.first_name} {user.last_name or ''}".strip()

            result = await telegram_ai_service.create_prontuario_from_voice(
                transcription=transcription,
                doctor_name=doctor_name,
                doctor_crm=None
            )

            if result["status"] == "success":
                await status_msg.edit_text("✅ Prontuário criado!")

                # Envia análise
                MAX_LENGTH = 4000
                if len(result["analysis"]) <= MAX_LENGTH:
                    await update.message.reply_text(result["analysis"])
                else:
                    parts = [result["analysis"][i:i+MAX_LENGTH] for i in range(0, len(result["analysis"]), MAX_LENGTH)]
                    for i, part in enumerate(parts, 1):
                        prefix = f"📄 Parte {i}/{len(parts)}:\n\n"
                        message = prefix + part
                        if len(message) > 4096:
                            message = prefix + part[:4096-len(prefix)]
                        await update.message.reply_text(message)
            else:
                await status_msg.edit_text(f"❌ Erro: {result['error'][:100]}")

            # Limpa contexto
            context.user_data['awaiting_prontuario'] = False

        except Exception as e:
            logger.error(f"Erro ao criar prontuário: {e}")
            await status_msg.edit_text(f"❌ Erro: {str(e)[:100]}")

        return

    # Verifica se há análise de imagem prévia para integrar
    if context.user_data and 'last_image_analysis' in context.user_data:
        image_analysis = context.user_data['last_image_analysis']
        transcription = f"""ANÁLISE DE IMAGEM (ECG/RX) PRÉVIA:
---
{image_analysis}
---

DADOS CLÍNICOS ADICIONAIS:
{transcription}
"""
        # Limpa análise usada
        del context.user_data['last_image_analysis']

        await update.message.reply_text(
            "✅ Integrando análise da imagem com dados clínicos...\n"
            "Consultando especialistas..."
        )

    # Se texto muito curto, usa IA conversacional ao invés de dar erro
    if len(transcription) < 20 and 'ANÁLISE DE IMAGEM' not in transcription:
        # Verifica se está logado
        is_logged_in = context.user_data and context.user_data.get('logged_in', False)
        doctor_name = None
        if is_logged_in and 'doctor' in context.user_data:
            doctor_name = context.user_data['doctor'].get('name', 'Doutor')

        # Usa IA para conversar
        chat_result = await telegram_ai_service.chat_with_doctor(
            message=transcription,
            is_logged_in=is_logged_in,
            doctor_name=doctor_name
        )

        # Envia resposta da IA
        await update.message.reply_text(chat_result['response'])
        return

    # Envia confirmação
    status_msg = await update.message.reply_text(
        "🤖 Analisando caso clínico...\n\n"
        "🔄 Consultando especialistas:\n"
        "• Coordenador Cardiológico\n"
        "• Especialistas conforme necessidade\n\n"
        "⏳ Aguarde 60-90 segundos..."
    )

    try:
        # CHAMA DIRETO O CREWAI (SEM API)
        user = update.effective_user
        doctor_name = f"Dr(a). {user.first_name} {user.last_name or ''}".strip()

        logger.info(f"🤖 Analisando caso DIRETO com CrewAI para {doctor_name}")

        # Importa e chama o crew direto
        from app.crews.cardio_crew import analyze_cardio_case

        # Análise direto
        result = await analyze_cardio_case(
            transcription=transcription,
            doctor_name=doctor_name
        )

        if result:
            # Extrai a análise do resultado (pode ser dict ou string)
            if isinstance(result, dict):
                analysis_text = result.get('analysis', str(result))
            else:
                analysis_text = str(result)

            # Formata para Telegram (converte markdown)
            analysis_formatted = format_for_telegram(analysis_text)

            # Edita mensagem de status
            await status_msg.edit_text("✅ Análise concluída com CrewAI!")

            # Envia análise (SEMPRE dividida para evitar erro)
            MAX_LENGTH = 3900  # Margem de segurança (limite Telegram = 4096)

            # Divide em partes
            if len(analysis_formatted) <= MAX_LENGTH:
                # Se cabe em uma mensagem, envia direto com parse_mode Markdown
                await update.message.reply_text(analysis_formatted, parse_mode='Markdown')
            else:
                # Divide em múltiplas partes
                num_parts = (len(analysis_formatted) + MAX_LENGTH - 1) // MAX_LENGTH
                for i in range(num_parts):
                    start = i * MAX_LENGTH
                    end = min((i + 1) * MAX_LENGTH, len(analysis_formatted))
                    part = analysis_formatted[start:end]

                    if num_parts > 1:
                        prefix = f"📄 *Parte {i+1}/{num_parts}*\n\n"
                    else:
                        prefix = ""

                    message = prefix + part

                    # Garante que não excede o limite
                    if len(message) > 4096:
                        message = message[:4090] + "..."

                    await update.message.reply_text(message, parse_mode='Markdown')

            # ===== PERGUNTA SE QUER SALVAR O PRONTUÁRIO =====
            # Salva dados temporários para usar depois se confirmar
            context.user_data['temp_transcription'] = transcription
            context.user_data['temp_analysis'] = analysis_text
            context.user_data['temp_doctor_name'] = doctor_name

            # Botões de confirmação
            keyboard = [
                [InlineKeyboardButton("✅ Salvar Prontuário", callback_data="save_prontuario_confirm")],
                [InlineKeyboardButton("❌ Descartar", callback_data="discard_prontuario")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "💾 <b>Deseja salvar este prontuário?</b>\n\n"
                "Se salvar, vou perguntar sobre os dados do paciente.",
                parse_mode='HTML',
                reply_markup=reply_markup
            )

        else:
            await status_msg.edit_text(
                f"❌ Erro: Análise não retornou resultado.\n\n"
                "Tente novamente."
            )

    except Exception as e:
        logger.error(f"Erro ao analisar caso: {e}", exc_info=True)
        error_msg = str(e)[:200]
        await status_msg.edit_text(
            f"❌ Erro inesperado: {error_msg}\n\n"
            "Contate o suporte."
        )


async def save_prontuario_with_patient(context: ContextTypes.DEFAULT_TYPE, patient_id: Optional[str] = None):
    """
    Salva prontuário no banco com ou sem paciente vinculado

    Args:
        context: Contexto do Telegram
        patient_id: ID do paciente (opcional)
    """
    from app.database.models import get_supabase_client
    import uuid

    transcription = context.user_data.get('temp_transcription', '')
    analysis_text = context.user_data.get('temp_analysis', '')
    doctor_name = context.user_data.get('temp_doctor_name', 'Médico')

    # Gera case_id único
    case_id_generated = str(uuid.uuid4())

    # Salva no Supabase
    supabase = get_supabase_client()

    prontuario_data = {
        "case_id": case_id_generated,
        "doctor_name": doctor_name,
        "doctor_crm": None,
        "patient_id": patient_id,
        "transcription": transcription[:1000],
        "analysis_result": analysis_text
    }

    result = supabase.table("case_analyses").insert(prontuario_data).execute()

    if result.data:
        prontuario_id = result.data[0]["id"]
        context.user_data['last_prontuario_id'] = prontuario_id
        context.user_data['last_case_id'] = case_id_generated
        logger.info(f"✅ Prontuário {prontuario_id} salvo no banco!")

        # Limpa dados temporários
        context.user_data.pop('temp_transcription', None)
        context.user_data.pop('temp_analysis', None)
        context.user_data.pop('temp_doctor_name', None)

        return prontuario_id

    raise Exception("Erro ao salvar no banco de dados")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para botões inline"""
    query = update.callback_query
    await query.answer()

    if query.data == "show_login":
        await query.edit_message_text(
            "🔐 <b>LOGIN</b>\n\n"
            "Digite seu email:\n"
            "(Ex: seuemail@clinica.com)",
            parse_mode='HTML'
        )
        context.user_data['awaiting'] = 'login_email'

    elif query.data == "show_register":
        await query.edit_message_text(
            "📝 <b>CADASTRO</b>\n\n"
            "Digite seu nome completo:\n"
            "(Ex: Dr. João Silva)",
            parse_mode='HTML'
        )
        context.user_data['awaiting'] = 'register_name'

    elif query.data == "about":
        await query.edit_message_text(
            "ℹ️ <b>Sobre o ClinicaPro Cardio</b>\n\n"
            "Sistema de apoio à decisão cardiológica com IA.\n\n"
            "🔹 CrewAI multi-agente\n"
            "🔹 Análise de ECG/exames\n"
            "🔹 Sugestões baseadas em guidelines\n\n"
            "⚠️ Sistema de apoio - decisão final é do médico.",
            parse_mode='HTML'
        )

    elif query.data == "new_patient":
        await query.edit_message_text(
            "➕ <b>NOVO PACIENTE</b>\n\n"
            "📝 Vou pedir:\n\n"
            "1️⃣ <b>Nome completo</b>\n"
            "2️⃣ <b>CPF</b>\n"
            "3️⃣ <b>Telefone</b> (opcional)\n"
            "4️⃣ <b>Idade OU Data</b> (opcional)\n\n"
            "💡 <i>Na emergência, só digite a idade!</i>\n\n"
            "Digite o <b>nome completo</b> do paciente:",
            parse_mode='HTML'
        )
        context.user_data['awaiting'] = 'new_patient_name'

    elif query.data == "list_patients":
        await query.edit_message_text("🔍 Buscando pacientes...")

        try:
            # LISTA DIRETO DO BANCO (SEM API)
            result = await list_patients(limit=10, offset=0)

            if result["status"] == "success":
                patients = result["data"]

                if not patients:
                    await query.edit_message_text(
                        "👥 <b>PACIENTES</b>\n\n"
                        "Nenhum paciente cadastrado ainda.\n\n"
                        "Use /start para voltar ao menu.",
                        parse_mode='HTML'
                    )
                    return

                # Monta lista
                msg = "👥 <b>ÚLTIMOS PACIENTES</b>\n\n"

                for i, p in enumerate(patients[:10], 1):
                    name = p.get('full_name', 'Nome não disponível')
                    age_text = f", {p.get('age')} anos" if p.get('age') else ""
                    cpf = p.get('cpf', 'CPF não informado')

                    msg += f"{i}. <b>{name}</b>{age_text}\n"
                    msg += f"   📄 {cpf}\n\n"

                msg += "\n💡 Use /start para voltar ao menu."

                await query.edit_message_text(msg, parse_mode='HTML')
            else:
                await query.edit_message_text(
                    f"❌ Erro ao buscar pacientes: {result['error'][:100]}\n\n"
                    "Use /start para voltar ao menu."
                )

        except Exception as e:
            logger.error(f"Erro ao listar pacientes: {e}")
            await query.edit_message_text(
                f"❌ Erro: {str(e)[:100]}\n\n"
                "Use /start para voltar ao menu."
            )

    elif query.data == "list_prontuarios":
        await query.edit_message_text("🔍 Buscando prontuários...")

        try:
            # LISTA DIRETO DO BANCO (SEM API) - usa case_analyses
            result = await list_case_analyses(limit=10, offset=0)

            if result["status"] == "success":
                prontuarios = result["data"]

                if not prontuarios:
                    await query.edit_message_text(
                        "📋 <b>PRONTUÁRIOS</b>\n\n"
                        "Nenhum prontuário criado ainda.\n\n"
                        "Use /start para voltar ao menu.",
                        parse_mode='HTML'
                    )
                    return

                # Cria botões para prontuários
                keyboard = []

                for i, pront in enumerate(prontuarios[:10], 1):
                    pront_id = pront.get('id')
                    patient_id = pront.get('patient_id')
                    transcription = pront.get('transcription', '')
                    created = pront.get('created_at', '')

                    # Formata data
                    if created:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                            date_str = dt.strftime("%d/%m %H:%M")
                        except:
                            date_str = created[:10]
                    else:
                        date_str = ""

                    # Tenta pegar nome do paciente
                    patient_name = "Paciente"

                    # Se tem patient_id vinculado, busca o nome
                    if patient_id:
                        try:
                            from app.database.models import get_supabase_client
                            supabase = get_supabase_client()
                            patient_response = supabase.table("patients").select("full_name").eq("id", patient_id).execute()
                            if patient_response.data:
                                patient_name = patient_response.data[0].get('full_name', 'Paciente')[:25]
                        except:
                            pass

                    # Se não tem nome, extrai da transcrição
                    if patient_name == "Paciente" and transcription:
                        # Tenta extrair características do paciente
                        import re
                        trans_lower = transcription.lower()

                        # Procura por "Paciente X anos" ou "masculino/feminino X anos"
                        idade_match = re.search(r'(\d{1,3})\s*anos?', trans_lower)
                        sexo = "M" if "masculino" in trans_lower else ("F" if "feminino" in trans_lower else "")

                        if idade_match and sexo:
                            patient_name = f"{sexo}, {idade_match.group(1)}a"
                        elif idade_match:
                            patient_name = f"{idade_match.group(1)} anos"
                        else:
                            # Pega primeiras 20 chars da transcrição
                            patient_name = transcription[:20].strip()

                    # Botão com nome do paciente e data
                    button_text = f"{i}. {patient_name} - {date_str}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_pront_{pront_id}")])

                # Botão voltar
                keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="back_to_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    "📋 <b>ÚLTIMOS PRONTUÁRIOS</b>\n\n"
                    "Clique para ver o prontuário completo:",
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    f"❌ Erro ao buscar prontuários: {result['error'][:100]}\n\n"
                    "Use /start para voltar ao menu."
                )

        except Exception as e:
            logger.error(f"Erro ao listar prontuários: {e}")
            await query.edit_message_text(
                f"❌ Erro: {str(e)[:100]}\n\n"
                "Use /start para voltar ao menu."
            )

    elif query.data == "new_prontuario":
        await query.edit_message_text(
            "🏥 <b>NOVO PRONTUÁRIO</b>\n\n"
            "📝 Digite ou envie áudio com os dados do paciente:\n\n"
            "Exemplo: 'Paciente masculino, 58 anos, hipertenso, dor torácica em aperto...'",
            parse_mode='HTML'
        )
        context.user_data['awaiting_prontuario'] = True

    elif query.data == "study_case":
        prontuario_id = context.user_data.get('last_prontuario_id')
        diagnosis = context.user_data.get('last_diagnosis', 'Não especificado')

        if not prontuario_id:
            await query.edit_message_text(
                "❌ Prontuário não encontrado.\n\n"
                "Envie um novo caso para análise primeiro."
            )
            return

        await query.edit_message_text("📚 Iniciando estudo aprofundado...\n\n⏳ Isso pode levar 1-2 minutos.")

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                study_response = await client.post(
                    f"{API_URL.replace('/api/v1/analyze', f'/api/v1/prontuarios/{prontuario_id}/study')}",
                )

            if study_response.status_code == 200:
                try:
                    study_result = study_response.json()
                    study_content = study_result.get("study", "")

                    await query.edit_message_text("✅ Estudo concluído!")

                    # Envia estudo
                    MAX_LENGTH = 4000
                    if len(study_content) <= MAX_LENGTH:
                        await query.message.reply_text(study_content)
                    else:
                        parts = [study_content[i:i+MAX_LENGTH] for i in range(0, len(study_content), MAX_LENGTH)]
                        for i, part in enumerate(parts, 1):
                            prefix = f"📚 Estudo - Parte {i}/{len(parts)}:\n\n"
                            message = prefix + part
                            if len(message) > 4096:
                                message = prefix + part[:4096-len(prefix)]
                            await query.message.reply_text(message)

                    await query.message.reply_text(
                        "✅ Estudo completo!\n\n"
                        "Use /start para voltar ao menu."
                    )
                except:
                    await query.edit_message_text(
                        "❌ Erro ao processar estudo.\n\n"
                        "Use /start para voltar."
                    )
            else:
                await query.edit_message_text(
                    f"❌ Erro ao gerar estudo: {study_response.status_code}\n\n"
                    "Tente novamente."
                )

        except httpx.TimeoutException:
            await query.edit_message_text(
                "⏱️ Timeout ao gerar estudo.\n\n"
                "Tente novamente."
            )
        except Exception as e:
            logger.error(f"Erro ao estudar caso: {e}", exc_info=True)
            await query.edit_message_text(
                f"❌ Erro ao gerar estudo.\n\n"
                "Contate o suporte."
            )

    elif query.data.startswith("view_pront_"):
        # Visualizar prontuário específico
        pront_id = query.data.replace("view_pront_", "")

        await query.edit_message_text("🔍 Buscando prontuário...")

        try:
            from app.database.models import get_supabase_client
            supabase = get_supabase_client()

            # Busca prontuário por ID
            response = supabase.table("case_analyses").select("*").eq("id", pront_id).execute()

            if response.data:
                pront = response.data[0]

                # Formata dados
                doctor_name = pront.get('doctor_name', 'Não identificado')
                transcription = pront.get('transcription', 'Não disponível')
                analysis = pront.get('analysis_result', 'Análise não disponível')
                created = pront.get('created_at', '')

                if created:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        date_str = dt.strftime("%d/%m/%Y às %H:%M")
                    except:
                        date_str = created[:16]
                else:
                    date_str = "Data não disponível"

                # Monta mensagem
                msg = f"📋 <b>PRONTUÁRIO</b>\n\n"
                msg += f"👨‍⚕️ <b>Médico:</b> {doctor_name}\n"
                msg += f"📅 <b>Data:</b> {date_str}\n\n"
                msg += f"📝 <b>Dados clínicos:</b>\n{transcription[:200]}...\n\n"
                msg += f"💬 Clique em 'Ver Análise' para ver a análise completa."

                # Botões
                keyboard = [
                    [InlineKeyboardButton("📄 Ver Análise Completa", callback_data=f"view_analysis_{pront_id}")],
                    [InlineKeyboardButton("🔙 Voltar", callback_data="list_prontuarios")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(msg, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await query.edit_message_text(
                    "❌ Prontuário não encontrado.\n\n"
                    "Use /start para voltar."
                )

        except Exception as e:
            logger.error(f"Erro ao buscar prontuário: {e}")
            await query.edit_message_text(f"❌ Erro: {str(e)[:100]}")

    elif query.data.startswith("view_analysis_"):
        # Ver análise completa do prontuário
        pront_id = query.data.replace("view_analysis_", "")

        await query.edit_message_text("📄 Carregando análise...")

        try:
            from app.database.models import get_supabase_client
            supabase = get_supabase_client()

            response = supabase.table("case_analyses").select("analysis_result").eq("id", pront_id).execute()

            if response.data:
                analysis = response.data[0].get('analysis_result', 'Análise não disponível')

                # Formata para Telegram
                analysis_formatted = format_for_telegram(analysis)

                await query.edit_message_text("✅ Análise encontrada!")

                # Envia análise dividida
                MAX_LENGTH = 3900
                if len(analysis_formatted) <= MAX_LENGTH:
                    await query.message.reply_text(analysis_formatted, parse_mode='Markdown')
                else:
                    num_parts = (len(analysis_formatted) + MAX_LENGTH - 1) // MAX_LENGTH
                    for i in range(num_parts):
                        start = i * MAX_LENGTH
                        end = min((i + 1) * MAX_LENGTH, len(analysis_formatted))
                        part = analysis_formatted[start:end]

                        prefix = f"📄 *Parte {i+1}/{num_parts}*\n\n"
                        message = prefix + part

                        if len(message) > 4096:
                            message = message[:4090] + "..."

                        await query.message.reply_text(message, parse_mode='Markdown')

                # Botão voltar
                keyboard = [[InlineKeyboardButton("🔙 Voltar aos Prontuários", callback_data="list_prontuarios")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text("Use o botão abaixo:", reply_markup=reply_markup)

            else:
                await query.edit_message_text("❌ Análise não encontrada.")

        except Exception as e:
            logger.error(f"Erro ao buscar análise: {e}")
            await query.edit_message_text(f"❌ Erro: {str(e)[:100]}")

    elif query.data == "save_prontuario_confirm":
        # Usuário confirmou que quer salvar - pergunta sobre o paciente
        await query.edit_message_text(
            "👤 <b>DADOS DO PACIENTE</b>\n\n"
            "Este prontuário é para:\n\n"
            "• Paciente novo (cadastrar agora)\n"
            "• Paciente existente (vincular)",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Novo Paciente", callback_data="new_patient_for_pront")],
                [InlineKeyboardButton("👤 Paciente Existente", callback_data="existing_patient_for_pront")],
                [InlineKeyboardButton("⏭️ Salvar sem vincular", callback_data="save_without_patient")],
                [InlineKeyboardButton("🔙 Cancelar", callback_data="discard_prontuario")]
            ])
        )

    elif query.data == "discard_prontuario":
        # Usuário decidiu não salvar
        context.user_data.pop('temp_transcription', None)
        context.user_data.pop('temp_analysis', None)
        context.user_data.pop('temp_doctor_name', None)

        await query.edit_message_text(
            "🗑️ Prontuário descartado.\n\n"
            "Use /start para voltar ao menu."
        )

    elif query.data == "new_patient_for_pront":
        # Pede dados do novo paciente
        await query.edit_message_text(
            "📝 <b>NOVO PACIENTE</b>\n\n"
            "Digite os dados no formato:\n"
            "Nome Completo | CPF | Data Nascimento\n\n"
            "Exemplo:\n"
            "João Silva | 12345678901 | 15/03/1965",
            parse_mode='HTML'
        )
        context.user_data['awaiting'] = 'new_patient_data_for_pront'

    elif query.data == "existing_patient_for_pront":
        # Lista pacientes existentes para vincular
        await query.edit_message_text("🔍 Buscando pacientes...")

        try:
            from app.database.models import list_patients
            result = await list_patients(limit=20, offset=0)

            if result["status"] == "success" and result["data"]:
                patients = result["data"]

                keyboard = []
                for patient in patients[:10]:
                    patient_id = patient.get('id')
                    name = patient.get('full_name', 'Sem nome')
                    cpf = patient.get('cpf', '')
                    button_text = f"{name[:20]} - {cpf[:11]}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"link_patient_{patient_id}")])

                keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="save_prontuario_confirm")])

                await query.edit_message_text(
                    "👥 <b>SELECIONE O PACIENTE</b>\n\n"
                    "Clique no paciente para vincular ao prontuário:",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.edit_message_text(
                    "❌ Nenhum paciente cadastrado.\n\n"
                    "Use 'Novo Paciente' para cadastrar.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Voltar", callback_data="save_prontuario_confirm")]
                    ])
                )

        except Exception as e:
            logger.error(f"Erro ao listar pacientes: {e}")
            await query.edit_message_text(f"❌ Erro: {str(e)[:100]}")

    elif query.data.startswith("link_patient_"):
        # Vincula prontuário ao paciente selecionado
        patient_id = query.data.replace("link_patient_", "")

        try:
            # Salva prontuário com patient_id
            await save_prontuario_with_patient(context, patient_id)
            await query.edit_message_text(
                "✅ <b>Prontuário salvo com sucesso!</b>\n\n"
                "Paciente vinculado ao prontuário.\n\n"
                "Use /start para voltar ao menu.",
                parse_mode='HTML'
            )

        except Exception as e:
            logger.error(f"Erro ao salvar prontuário: {e}")
            await query.edit_message_text(f"❌ Erro ao salvar: {str(e)[:100]}")

    elif query.data == "save_without_patient":
        # Salva sem vincular a nenhum paciente
        try:
            await save_prontuario_with_patient(context, patient_id=None)
            await query.edit_message_text(
                "✅ <b>Prontuário salvo!</b>\n\n"
                "(Sem paciente vinculado)\n\n"
                "Use /start para voltar ao menu.",
                parse_mode='HTML'
            )

        except Exception as e:
            logger.error(f"Erro ao salvar prontuário: {e}")
            await query.edit_message_text(f"❌ Erro ao salvar: {str(e)[:100]}")

    elif query.data == "back_to_menu":
        # Volta ao menu principal
        doctor = context.user_data.get('doctor')
        keyboard = [
            [InlineKeyboardButton("➕ Novo Paciente", callback_data="new_patient")],
            [InlineKeyboardButton("👥 Ver Pacientes", callback_data="list_patients")],
            [InlineKeyboardButton("📋 Ver Prontuários", callback_data="list_prontuarios")],
            [InlineKeyboardButton("🏥 Novo Prontuário", callback_data="new_prontuario")],
            [InlineKeyboardButton("🚪 Sair", callback_data="logout")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"🏥 <b>ClinicaPro Cardio</b>\n\n"
            f"Bem-vindo, <b>{doctor.get('name') if doctor else 'Médico'}</b>!\n\n"
            f"O que você gostaria de fazer?",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    elif query.data == "logout":
        context.user_data.clear()
        await query.edit_message_text(
            "🚪 Logout realizado com sucesso!\n\n"
            "Use /start para fazer login novamente."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler global de erros"""
    logger.error(f"Update {update} causou erro {context.error}")


# ===== MAIN =====

def main():
    """Inicia o bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN não configurado!")
        return

    logger.info("🤖 Iniciando ClinicaPro Cardio Bot...")

    # Cria aplicação
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Registra handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("testar", test_api_command))
    app.add_handler(CommandHandler("paciente", search_patient_command))
    app.add_handler(CommandHandler("prontuario", prontuario_command))
    app.add_handler(CommandHandler("sugestao", suggest_command))

    # Handler de botões inline
    app.add_handler(CallbackQueryHandler(button_callback))

    # Handlers de mensagens
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Error handler
    app.add_error_handler(error_handler)

    # Inicia bot
    logger.info("✅ Bot rodando!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
