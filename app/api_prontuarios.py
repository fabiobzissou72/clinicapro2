"""
API de Prontuários - Gerenciamento de Prontuários Médicos
Endpoints para criar, buscar e estudar prontuários
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from app.auth import get_current_active_doctor
from app.database.models import get_supabase_client
from app.crews.study_crew import analyze_case_study

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/prontuarios", tags=["Prontuários"])


# ===== SCHEMAS =====

class ProntuarioCreate(BaseModel):
    """Schema para criar prontuário"""
    patient_id: Optional[str] = None
    patient_name: str = Field(..., min_length=1)
    transcription: str = Field(..., min_length=20)
    analysis: str = Field(..., min_length=50)
    diagnosis: str = Field(..., min_length=3)
    urgency_level: str = Field(default="ROTINA")  # EMERGÊNCIA, URGENTE, ROTINA
    case_id: Optional[str] = None


class ProntuarioResponse(BaseModel):
    """Schema de resposta de prontuário"""
    id: str
    patient_id: Optional[str]
    patient_name: str
    diagnosis: str
    urgency_level: str
    created_at: datetime
    doctor_id: str


class StudyRequest(BaseModel):
    """Schema para solicitar estudo de caso"""
    prontuario_id: str = Field(..., description="ID do prontuário a estudar")


# ===== ENDPOINTS =====

@router.post("/", response_model=ProntuarioResponse, status_code=201)
async def create_prontuario(
    prontuario: ProntuarioCreate,
    background_tasks: BackgroundTasks,
    current_doctor: dict = Depends(get_current_active_doctor)
):
    """
    Cria novo prontuário médico

    Salva análise completa no banco de dados vinculada ao paciente e médico.
    """
    try:
        prontuario_id = str(uuid.uuid4())

        # Prepara dados
        prontuario_data = {
            "id": prontuario_id,
            "patient_id": prontuario.patient_id,
            "patient_name": prontuario.patient_name,
            "doctor_id": current_doctor.get("id"),
            "doctor_name": current_doctor.get("full_name"),
            "transcription": prontuario.transcription,
            "analysis": prontuario.analysis,
            "diagnosis": prontuario.diagnosis,
            "urgency_level": prontuario.urgency_level,
            "case_id": prontuario.case_id or prontuario_id,
            "created_at": datetime.utcnow().isoformat()
        }

        # Salva no Supabase
        supabase = get_supabase_client()
        result = supabase.table("medical_records").insert(prontuario_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Erro ao salvar prontuário")

        logger.info(f"Prontuário {prontuario_id} criado com sucesso")

        return ProntuarioResponse(
            id=prontuario_id,
            patient_id=prontuario.patient_id,
            patient_name=prontuario.patient_name,
            diagnosis=prontuario.diagnosis,
            urgency_level=prontuario.urgency_level,
            created_at=datetime.fromisoformat(prontuario_data["created_at"]),
            doctor_id=current_doctor.get("id")
        )

    except Exception as e:
        logger.error(f"Erro ao criar prontuário: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao criar prontuário: {str(e)}")


@router.get("/{prontuario_id}")
async def get_prontuario(
    prontuario_id: str,
    current_doctor: dict = Depends(get_current_active_doctor)
):
    """
    Busca prontuário específico por ID

    Retorna análise completa salva anteriormente.
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("medical_records").select("*").eq("id", prontuario_id).execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Prontuário não encontrado")

        prontuario = result.data[0]

        # Verifica se o médico tem acesso (pode expandir com controle de acesso)
        # Por enquanto, todos médicos autenticados podem ver

        return prontuario

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar prontuário: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar prontuário: {str(e)}")


@router.post("/{prontuario_id}/study")
async def study_case(
    prontuario_id: str,
    background_tasks: BackgroundTasks,
    current_doctor: dict = Depends(get_current_active_doctor)
):
    """
    Solicita estudo aprofundado de um caso clínico

    Aciona o Study Crew para análise acadêmica detalhada com:
    - Literatura relevante
    - Evidências científicas
    - Alternativas terapêuticas
    - Prognóstico
    - Pontos de aprendizado
    """
    try:
        # Busca prontuário
        supabase = get_supabase_client()
        result = supabase.table("medical_records").select("*").eq("id", prontuario_id).execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Prontuário não encontrado")

        prontuario = result.data[0]

        # Prepara dados para estudo
        case_summary = f"""
        Paciente: {prontuario.get('patient_name')}
        Transcrição: {prontuario.get('transcription')[:500]}...
        """

        diagnosis = prontuario.get('diagnosis')
        doctor_name = current_doctor.get("full_name", "Médico")

        # Executa estudo aprofundado
        logger.info(f"Iniciando estudo de caso {prontuario_id}")

        study_result = await analyze_case_study(
            case_summary=case_summary,
            diagnosis=diagnosis,
            doctor_name=doctor_name
        )

        if study_result["status"] == "error":
            raise HTTPException(status_code=500, detail=study_result.get("error"))

        # Salva estudo no banco (opcional)
        study_id = str(uuid.uuid4())
        study_data = {
            "id": study_id,
            "prontuario_id": prontuario_id,
            "doctor_id": current_doctor.get("id"),
            "study_content": study_result.get("study"),
            "created_at": datetime.utcnow().isoformat()
        }

        supabase.table("case_studies").insert(study_data).execute()

        logger.info(f"Estudo de caso {study_id} criado para prontuário {prontuario_id}")

        return {
            "status": "success",
            "study_id": study_id,
            "prontuario_id": prontuario_id,
            "study": study_result.get("study"),
            "diagnosis": diagnosis
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao estudar caso: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao estudar caso: {str(e)}")
