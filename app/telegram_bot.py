"""
ClinicaPro Cardio - Telegram Bot Integration
Integra análise cardiológica com bot Telegram
"""

import os
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import httpx
from dotenv import load_dotenv
import subprocess

from app.whisper_service import WhisperService
from app.image_analysis_service import image_service

load_dotenv()

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

# Configurações
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"http://localhost:{os.getenv('PORT', 8000)}/api/v1/analyze"


# ===== HANDLERS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para comando /start"""
    user = update.effective_user
    await update.message.reply_html(
        f"""
🏥 <b>ClinicaPro Cardio</b>

Olá, Dr(a). {user.first_name}!

Sistema de apoio à decisão cardiológica com IA.

<b>Como usar:</b>
1. 📸 Envie uma foto de ECG/raio-x
2. 🎤 Envie um áudio com a consulta
3. ✍️ Ou envie texto com os dados do paciente
4. Aguarde a análise dos especialistas IA

<b>Comandos:</b>
/start - Iniciar bot
/help - Ajuda
/about - Sobre o sistema

⚠️ <b>IMPORTANTE:</b> Sistema de apoio à decisão.
A decisão final é sempre do médico assistente.
        """
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

        if result["status"] != "success":
            raise Exception(result.get("error", "Erro desconhecido na transcrição"))

        transcription = result["text"].strip()
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

        # Envia para análise (reutiliza lógica do handle_text)
        user = update.effective_user
        doctor_name = f"Dr(a). {user.first_name} {user.last_name or ''}".strip()

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                API_URL,
                json={
                    "transcription": transcription,
                    "doctor_name": doctor_name,
                    "doctor_crm": None
                }
            )

        if response.status_code == 200:
            result_api = response.json()
            analysis = result_api["analysis"]

            await status_msg.edit_text("✅ Análise concluída!")

            # Envia análise (dividida se necessário)
            # Usa texto puro para evitar problemas de parsing HTML
            if len(analysis) <= 4096:
                await update.message.reply_text(analysis)
            else:
                parts = [analysis[i:i+4096] for i in range(0, len(analysis), 4096)]
                for i, part in enumerate(parts, 1):
                    await update.message.reply_text(
                        f"📄 Parte {i}/{len(parts)}:\n\n{part}"
                    )
        else:
            await status_msg.edit_text(
                f"❌ Erro na análise: {response.status_code}\n\n"
                "Tente novamente em alguns instantes."
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
        # Usa texto puro para evitar problemas de parsing
        if len(image_analysis) <= 4096:
            await update.message.reply_text(
                f"📊 ANÁLISE DA IMAGEM:\n\n{image_analysis}"
            )
        else:
            parts = [image_analysis[i:i+4096] for i in range(0, len(image_analysis), 4096)]
            for i, part in enumerate(parts, 1):
                await update.message.reply_text(
                    f"📊 Parte {i}/{len(parts)}:\n\n{part}"
                )

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

    # Valida tamanho mínimo (mais permissivo se tem imagem)
    min_length = 20 if 'ANÁLISE DE IMAGEM' in transcription else 50
    if len(transcription) < min_length:
        await update.message.reply_text(
            "⚠️ Texto muito curto.\n\n"
            "Por favor, envie pelo menos 50 caracteres com:\n"
            "• Queixa principal\n"
            "• Dados vitais\n"
            "• Exame físico\n"
            "• Comorbidades"
        )
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
        # Chama API de análise
        user = update.effective_user
        doctor_name = f"Dr(a). {user.first_name} {user.last_name or ''}".strip()

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                API_URL,
                json={
                    "transcription": transcription,
                    "doctor_name": doctor_name,
                    "doctor_crm": None  # TODO: Obter do cadastro
                }
            )

        if response.status_code == 200:
            result = response.json()
            analysis = result["analysis"]

            # Edita mensagem de status
            await status_msg.edit_text("✅ Análise concluída!")

            # Envia análise (dividida se necessário)
            # Usa texto puro para evitar problemas de parsing HTML
            if len(analysis) <= 4096:
                await update.message.reply_text(analysis)
            else:
                # Telegram tem limite de 4096 caracteres
                parts = [analysis[i:i+4096] for i in range(0, len(analysis), 4096)]
                for i, part in enumerate(parts, 1):
                    await update.message.reply_text(
                        f"📄 Parte {i}/{len(parts)}:\n\n{part}"
                    )

        else:
            await status_msg.edit_text(
                f"❌ Erro na análise: {response.status_code}\n\n"
                "Tente novamente em alguns instantes."
            )

    except httpx.TimeoutException:
        await status_msg.edit_text(
            "⏱️ Timeout na análise.\n\n"
            "O caso pode ser muito complexo. Tente novamente."
        )

    except Exception as e:
        logger.error(f"Erro ao analisar caso: {e}", exc_info=True)
        error_msg = str(e)[:200]  # Limita tamanho do erro
        await status_msg.edit_text(
            f"❌ Erro inesperado: {error_msg}\n\n"
            "Contate o suporte se o problema persistir."
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

    # Handlers de mensagens
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))  # Imagens (ECG, raio-x)
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.AUDIO, handle_voice))  # Suporte para arquivos de áudio
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Error handler
    app.add_error_handler(error_handler)

    # Inicia bot
    logger.info("✅ Bot rodando!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
