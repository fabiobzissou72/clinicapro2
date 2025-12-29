"""
Serviço de Análise de Imagens Médicas (ECG)
Usa OpenAI GPT-4 Vision para interpretar ECGs
"""

import os
import base64
import logging
from pathlib import Path
from typing import Dict, Optional
from PIL import Image
import io

from openai import OpenAI

logger = logging.getLogger(__name__)


class ImageAnalysisService:
    """Serviço para análise de imagens médicas (ECGs) com GPT-4 Vision"""

    def __init__(self):
        """Inicializa serviço com OpenAI API"""
        # Carrega API key das variáveis de ambiente
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada nas variáveis de ambiente")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Suporta visão e é mais barato
        logger.info("Image Analysis Service inicializado")

    def encode_image(self, image_path: str) -> str:
        """
        Converte imagem para base64

        Args:
            image_path: Caminho da imagem

        Returns:
            String base64 da imagem
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def optimize_image(self, image_path: str, max_size: int = 2000) -> str:
        """
        Otimiza imagem para reduzir tamanho e custo da API

        Args:
            image_path: Caminho da imagem
            max_size: Tamanho máximo em pixels

        Returns:
            Caminho da imagem otimizada
        """
        img = Image.open(image_path)

        # Redimensiona se necessário
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Imagem redimensionada para {new_size}")

        # Converte para RGB se necessário
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Salva otimizada
        optimized_path = str(Path(image_path).with_suffix('.optimized.jpg'))
        img.save(optimized_path, 'JPEG', quality=85, optimize=True)

        return optimized_path

    def analyze_ecg(
        self,
        image_path: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Analisa imagem de ECG usando GPT-4 Vision

        Args:
            image_path: Caminho da imagem do ECG
            additional_context: Contexto adicional (sintomas, história)

        Returns:
            Dict com análise do ECG
        """
        try:
            # Verifica se arquivo existe
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

            logger.info(f"Analisando ECG: {image_path}")

            # Otimiza imagem
            optimized_path = self.optimize_image(image_path)

            # Codifica em base64
            base64_image = self.encode_image(optimized_path)

            # Monta prompt específico para ECG
            prompt = """Você é um cardiologista especialista em eletrocardiografia.

Analise esta imagem de ECG e forneça um relatório estruturado:

1. **PARÂMETROS BÁSICOS:**
   - Frequência cardíaca (bpm)
   - Ritmo (sinusal, FA, flutter, etc.)
   - Eixo elétrico (graus)

2. **INTERVALOS E ONDAS:**
   - Intervalo PR (ms) - Normal: 120-200ms
   - Complexo QRS (ms) - Normal: <120ms
   - Intervalo QT/QTc (ms) - Normal QTc: <440ms (H), <460ms (M)
   - Onda P (morfologia)
   - Onda T (alterações?)

3. **ACHADOS PATOLÓGICOS:**
   - Arritmias detectadas
   - Bloqueios (AV, ramo)
   - Sinais de isquemia (infradesnivelamento ST, inversão T)
   - Sinais de IAM (supradesnivelamento ST, onda Q patológica)
   - Hipertrofias (VE, VD, AE, AD)
   - Outras alterações

4. **INTERPRETAÇÃO CLÍNICA:**
   - Diagnóstico eletrocardiográfico principal
   - Diagnósticos diferenciais
   - Urgência (EMERGÊNCIA / URGENTE / ROTINA)

5. **RECOMENDAÇÕES:**
   - Necessidade de intervenção imediata?
   - Exames complementares sugeridos
   - Conduta inicial

IMPORTANTE: Seja preciso e técnico. Cite valores numéricos quando possível.
"""

            if additional_context:
                prompt += f"\n\n**CONTEXTO CLÍNICO ADICIONAL:**\n{additional_context}"

            # Chama API OpenAI Vision
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"  # Alta qualidade para detalhes do ECG
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1  # Baixa para precisão médica
            )

            analysis = response.choices[0].message.content

            # Limpa arquivo otimizado
            if Path(optimized_path).exists():
                Path(optimized_path).unlink()

            logger.info("Análise de ECG concluída")

            return {
                "status": "success",
                "analysis": analysis,
                "model": self.model,
                "tokens_used": response.usage.total_tokens
            }

        except Exception as e:
            logger.error(f"Erro ao analisar ECG: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    def analyze_generic_medical_image(
        self,
        image_path: str,
        image_type: str = "imagem médica",
        additional_context: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Analisa imagem médica genérica

        Args:
            image_path: Caminho da imagem
            image_type: Tipo de imagem (raio-x, eco, etc.)
            additional_context: Contexto adicional

        Returns:
            Dict com análise da imagem
        """
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

            logger.info(f"Analisando {image_type}: {image_path}")

            # Otimiza imagem
            optimized_path = self.optimize_image(image_path)
            base64_image = self.encode_image(optimized_path)

            prompt = f"""Você é um médico especialista.

Analise esta {image_type} e forneça:

1. **DESCRIÇÃO:**
   - O que você vê na imagem?
   - Estruturas anatômicas visíveis

2. **ACHADOS RELEVANTES:**
   - Alterações patológicas
   - Medidas quantitativas (se aplicável)

3. **INTERPRETAÇÃO:**
   - Diagnóstico sugerido
   - Diagnósticos diferenciais

4. **RECOMENDAÇÕES:**
   - Necessidade de exames adicionais
   - Conduta sugerida
"""

            if additional_context:
                prompt += f"\n\n**CONTEXTO CLÍNICO:**\n{additional_context}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.1
            )

            analysis = response.choices[0].message.content

            # Limpa arquivo otimizado
            if Path(optimized_path).exists():
                Path(optimized_path).unlink()

            logger.info(f"Análise de {image_type} concluída")

            return {
                "status": "success",
                "analysis": analysis,
                "model": self.model,
                "tokens_used": response.usage.total_tokens
            }

        except Exception as e:
            logger.error(f"Erro ao analisar imagem: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }


# ===== INSTÂNCIA GLOBAL =====
image_service = ImageAnalysisService()


# ===== FUNÇÕES HELPER =====

async def analyze_ecg_image(image_path: str, context: Optional[str] = None) -> str:
    """
    Helper async para análise de ECG

    Args:
        image_path: Caminho do ECG
        context: Contexto clínico

    Returns:
        Texto da análise
    """
    result = image_service.analyze_ecg(image_path, context)

    if result["status"] == "success":
        return result["analysis"]
    else:
        raise Exception(f"Erro na análise: {result.get('error')}")


# ===== EXEMPLO DE USO =====

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python image_analysis_service.py <caminho_ecg.jpg>")
        sys.exit(1)

    image_path = sys.argv[1]

    # Configura logging
    logging.basicConfig(level=logging.INFO)

    # Cria serviço
    service = ImageAnalysisService()

    # Analisa ECG
    print(f"\n📊 Analisando ECG: {image_path}\n")
    result = service.analyze_ecg(image_path)

    if result["status"] == "success":
        print("="*60)
        print("ANÁLISE DO ECG:")
        print("="*60)
        print(result["analysis"])
        print("="*60)
        print(f"Tokens usados: {result['tokens_used']}")
    else:
        print(f"❌ Erro: {result['error']}")
