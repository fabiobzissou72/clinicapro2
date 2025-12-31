"""
Whisper Service - Transcrição de Áudio
Usa OpenAI Whisper API para transcrever consultas médicas
"""

import os
from pathlib import Path
from typing import Optional
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class WhisperService:
    """Serviço de transcrição com Whisper API"""

    def __init__(self, model_size: str = "base"):
        """
        Inicializa serviço Whisper API

        Args:
            model_size: Ignorado (API usa whisper-1)
        """
        # Carrega API key das variáveis de ambiente
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada nas variáveis de ambiente")

        self.client = OpenAI(api_key=api_key)
        logger.info("Whisper API Service inicializado")

    def load_model(self):
        """Não necessário para API"""
        pass

    def transcribe(
        self,
        audio_path: str,
        language: str = "pt",
        initial_prompt: Optional[str] = None
    ) -> dict:
        """
        Transcreve áudio para texto usando OpenAI API

        Args:
            audio_path: Caminho do arquivo de áudio
            language: Código do idioma (pt, en, es, etc.)
            initial_prompt: Prompt inicial para melhorar precisão médica

        Returns:
            Dict com transcrição e metadados
        """
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")

        logger.info(f"Transcrevendo via API: {audio_file.name}")

        # Prompt médico para melhor contexto
        if initial_prompt is None:
            initial_prompt = (
                "Transcrição de consulta médica cardiológica. "
                "Paciente, sintomas, exame físico, dados vitais."
            )

        try:
            with open(audio_path, "rb") as audio:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language=language,
                    prompt=initial_prompt,
                    response_format="text"
                )

            logger.info(f"Transcrição API concluída - Tipo de retorno: {type(transcript)}")

            # Garante que transcript é uma string
            transcript_text = str(transcript) if transcript else ""

            logger.info(f"Texto transcrito: {len(transcript_text)} caracteres")

            result = {
                "status": "success",
                "text": transcript_text,
                "language": language,
                "audio_file": audio_file.name
            }

            logger.info(f"Retornando resultado - tipo: {type(result)}, keys: {result.keys()}")
            return result

        except Exception as e:
            logger.error(f"Erro na transcrição: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "audio_file": audio_file.name
            }

    def transcribe_with_timestamps(
        self,
        audio_path: str,
        language: str = "pt"
    ) -> list:
        """
        Transcreve áudio com timestamps de cada segmento

        Returns:
            Lista de segmentos com start, end e texto
        """
        result = self.transcribe(audio_path, language)

        if result["status"] == "error":
            return []

        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg.get("start"),
                "end": seg.get("end"),
                "text": seg.get("text", "").strip()
            })

        return segments


# ===== FUNÇÕES HELPER =====

async def transcribe_audio_file(audio_path: str, model_size: str = "base") -> str:
    """
    Helper para transcrever áudio (uso simples)

    Args:
        audio_path: Caminho do arquivo
        model_size: Tamanho do modelo

    Returns:
        Texto transcrito
    """
    service = WhisperService(model_size=model_size)
    result = service.transcribe(audio_path)

    if result["status"] == "success":
        return result["text"]
    else:
        raise Exception(f"Erro na transcrição: {result.get('error')}")


# ===== EXEMPLO DE USO =====

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python whisper_service.py <arquivo_audio>")
        print("\nExemplo:")
        print("  python whisper_service.py consulta.mp3")
        sys.exit(1)

    audio_file = sys.argv[1]

    # Configura logging
    logging.basicConfig(level=logging.INFO)

    # Cria serviço
    service = WhisperService(model_size="base")

    # Transcreve
    print(f"\n🎤 Transcrevendo: {audio_file}\n")
    result = service.transcribe(audio_file)

    if result["status"] == "success":
        print("="*60)
        print("TRANSCRIÇÃO:")
        print("="*60)
        print(result["text"])
        print("="*60)
    else:
        print(f"❌ Erro: {result['error']}")
