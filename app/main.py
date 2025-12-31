"""
ClinicaPro Cardio - API Principal
Sistema de apoio à decisão cardiológica com IA
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configura logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('clinicapro_cardio.log')
    ]
)
logger = logging.getLogger(__name__)

# Importa crew
from app.crews.cardio_crew import analyze_cardio_case

# Importa routers
from app.api_patients import router as patients_router
from app.api_auth import router as auth_router
from app.api_dashboard import router as dashboard_router
from app.api_prontuarios import router as prontuarios_router

# ===== APLICAÇÃO FASTAPI =====
app = FastAPI(
    title="ClinicaPro Cardio API",
    description="""
    Sistema de apoio à decisão cardiológica com inteligência artificial.

    Utiliza CrewAI multi-agente para análise especializada de casos clínicos,
    simulando equipe de cardiologistas (coordenador + 3 especialistas).

    **IMPORTANTE:** Sistema de apoio à decisão. Decisão final é do médico assistente.
    """,
    version="0.1.0-beta",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://clinicapro.fbzia.com.br",
        os.getenv("TELEGRAM_WEBAPP_URL", "")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== ROUTERS =====
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(patients_router)
app.include_router(prontuarios_router)

# ===== MODELS =====
class AnalysisRequest(BaseModel):
    """Request para análise de caso clínico"""
    transcription: str = Field(
        ...,
        min_length=20,
        description="Texto transcrito da consulta cardiológica (mínimo 20 caracteres para casos de emergência)"
    )
    doctor_name: Optional[str] = Field(
        default="Médico",
        description="Nome do médico responsável"
    )
    doctor_crm: Optional[str] = Field(
        default=None,
        description="CRM do médico (para auditoria)"
    )
    patient_id: Optional[str] = Field(
        default=None,
        description="ID do paciente (anonimizado)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "transcription": "Paciente masculino, 58 anos, hipertenso, refere dor torácica em aperto há 2 horas, irradiando para braço esquerdo. PA: 160x100 mmHg, FC: 95 bpm.",
                "doctor_name": "Dr. João Silva",
                "doctor_crm": "12345-SP",
                "patient_id": "PAC-001"
            }
        }


class AnalysisResponse(BaseModel):
    """Response da análise"""
    status: str = Field(description="Status da análise (success/error)")
    case_id: str = Field(description="ID único do caso")
    analysis: Optional[str] = Field(default=None, description="Análise formatada em SOAP")
    doctor_name: str
    timestamp: datetime
    error: Optional[str] = Field(default=None, description="Mensagem de erro, se houver")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str
    services: Dict[str, str]


# ===== ENDPOINTS =====

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "ClinicaPro Cardio API",
        "version": "0.1.0-beta",
        "status": "active",
        "docs": "/docs",
        "webapp": "/webapp",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/v1/analyze"
        }
    }


@app.get("/webapp", tags=["WebApp"])
async def get_webapp():
    """Retorna Telegram Web App"""
    webapp_path = Path(__file__).parent.parent / "webapp_telegram.html"

    if not webapp_path.exists():
        raise HTTPException(status_code=404, detail="Web App não encontrado")

    return FileResponse(webapp_path, media_type="text/html")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Verifica saúde dos serviços

    Returns:
        Status de saúde da API e serviços conectados
    """
    # TODO: Verificar conectividade com Qdrant, Redis, Supabase
    services_status = {
        "api": "healthy",
        "openai": "healthy" if os.getenv("OPENAI_API_KEY") else "not_configured",
        "qdrant": "not_checked",  # Implementar verificação
        "redis": "not_checked",
        "supabase": "healthy" if os.getenv("SUPABASE_URL") else "not_configured"
    }

    return HealthResponse(
        status="healthy" if all(s != "error" for s in services_status.values()) else "degraded",
        version="0.1.0-beta",
        environment=os.getenv("ENVIRONMENT", "development"),
        services=services_status
    )


@app.post("/api/v1/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_case(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analisa caso clínico cardiológico usando CrewAI multi-agente

    - **transcription**: Texto da consulta transcrito (mínimo 50 caracteres)
    - **doctor_name**: Nome do médico (opcional)
    - **doctor_crm**: CRM do médico para auditoria (opcional)
    - **patient_id**: ID anonimizado do paciente (opcional)

    Returns:
        Análise SOAP completa com recomendações baseadas em guidelines

    Raises:
        HTTPException 400: Transcrição muito curta ou inválida
        HTTPException 500: Erro no processamento
    """
    case_id = str(uuid.uuid4())

    try:
        logger.info(
            f"Nova análise iniciada - Caso: {case_id}, "
            f"Médico: {request.doctor_name}, CRM: {request.doctor_crm}"
        )

        # Valida input
        if not request.transcription or len(request.transcription.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Transcrição muito curta. Mínimo 50 caracteres necessários para análise confiável."
            )

        # Executa análise com crew
        result = await analyze_cardio_case(
            transcription=request.transcription,
            doctor_name=request.doctor_name,
            case_id=case_id
        )

        if result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"Erro na análise: {result.get('error', 'Erro desconhecido')}"
            )

        logger.info(f"Análise concluída com sucesso - Caso: {case_id}")

        # TODO: Salvar no Supabase em background
        # background_tasks.add_task(save_analysis_to_db, case_id, result, request)

        return AnalysisResponse(
            status="success",
            case_id=case_id,
            analysis=result["analysis"],
            doctor_name=request.doctor_name,
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Erro inesperado no caso {case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar análise: {str(e)}"
        )


@app.get("/api/v1/cases/{case_id}", tags=["Analysis"])
async def get_case(case_id: str):
    """
    Recupera análise de caso por ID

    TODO: Implementar busca no Supabase
    """
    # Implementar busca no banco
    raise HTTPException(
        status_code=501,
        detail="Endpoint não implementado ainda. Em desenvolvimento."
    )


# ===== STARTUP/SHUTDOWN =====

@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a aplicação"""
    logger.info(">> ClinicaPro Cardio API iniciando...")
    logger.info(f"Ambiente: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Modelo OpenAI: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")

    # Verifica variáveis críticas
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("ERRO: OPENAI_API_KEY nao configurada!")

    logger.info(">> API pronta para receber requisicoes")


@app.on_event("shutdown")
async def shutdown_event():
    """Executado ao encerrar a aplicação"""
    logger.info(">> ClinicaPro Cardio API encerrando...")


# ===== MAIN =====

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
