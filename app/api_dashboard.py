"""
API do Dashboard do Médico
Endpoints para visualização de pacientes, prontuários, analytics e agenda
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.auth import get_current_active_doctor
from app.database.models import get_supabase_client

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


# ===== MODELS =====

class PatientListItem(BaseModel):
    """Item da lista de pacientes"""
    id: str
    full_name: str
    age: Optional[int]
    last_consultation: Optional[str]
    risk_level: Optional[str]  # "low", "medium", "high"


class ProntuarioItem(BaseModel):
    """Item de prontuário/análise"""
    id: str
    case_id: str
    patient_id: Optional[str]
    patient_name: Optional[str]
    created_at: str
    summary: str  # Resumo da análise


class DashboardStats(BaseModel):
    """Estatísticas do dashboard"""
    total_patients: int
    total_consultations: int
    consultations_this_month: int
    consultations_today: int
    avg_consultations_per_day: float
    most_common_diagnosis: Optional[str]
    high_risk_patients: int


class AppointmentItem(BaseModel):
    """Item de agenda"""
    id: str
    patient_name: str
    patient_id: str
    datetime: str
    type: str  # "consulta", "retorno", "emergencia"
    status: str  # "scheduled", "completed", "cancelled"


# ===== ENDPOINTS =====

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_doctor: dict = Depends(get_current_active_doctor)
):
    """
    Retorna estatísticas gerais do médico

    Requer autenticação

    Returns:
        Estatísticas: total de pacientes, consultas, etc.
    """
    try:
        supabase = get_supabase_client()

        # Total de análises do médico
        analyses_response = supabase.table("case_analyses")\
            .select("*", count="exact")\
            .eq("doctor_crm", current_doctor["crm"])\
            .execute()

        total_consultations = analyses_response.count if analyses_response.count else 0

        # Análises deste mês
        first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0).isoformat()
        month_analyses = supabase.table("case_analyses")\
            .select("*", count="exact")\
            .eq("doctor_crm", current_doctor["crm"])\
            .gte("created_at", first_day_month)\
            .execute()

        consultations_this_month = month_analyses.count if month_analyses.count else 0

        # Análises hoje
        today_start = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
        today_analyses = supabase.table("case_analyses")\
            .select("*", count="exact")\
            .eq("doctor_crm", current_doctor["crm"])\
            .gte("created_at", today_start)\
            .execute()

        consultations_today = today_analyses.count if today_analyses.count else 0

        # Total de pacientes únicos
        patients_response = supabase.table("patients")\
            .select("*", count="exact")\
            .execute()

        total_patients = patients_response.count if patients_response.count else 0

        # Média de consultas por dia (últimos 30 dias)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        last_30_days = supabase.table("case_analyses")\
            .select("*", count="exact")\
            .eq("doctor_crm", current_doctor["crm"])\
            .gte("created_at", thirty_days_ago)\
            .execute()

        avg_per_day = (last_30_days.count / 30) if last_30_days.count else 0

        # Pacientes de alto risco (simulado - pode ser implementado com base em análises)
        high_risk_patients = 0

        return DashboardStats(
            total_patients=total_patients,
            total_consultations=total_consultations,
            consultations_this_month=consultations_this_month,
            consultations_today=consultations_today,
            avg_consultations_per_day=round(avg_per_day, 1),
            most_common_diagnosis=None,  # TODO: Implementar análise de diagnósticos
            high_risk_patients=high_risk_patients
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar estatísticas: {str(e)}"
        )


@router.get("/patients", response_model=List[PatientListItem])
async def list_patients(
    current_doctor: dict = Depends(get_current_active_doctor),
    search: Optional[str] = Query(None, description="Buscar por nome ou CPF"),
    limit: int = Query(50, ge=1, le=100, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação")
):
    """
    Lista pacientes do médico

    Requer autenticação

    - **search**: Termo de busca (nome ou CPF)
    - **limit**: Quantidade de resultados (1-100)
    - **offset**: Paginação

    Returns:
        Lista de pacientes
    """
    try:
        supabase = get_supabase_client()

        # Query base
        query = supabase.table("patients").select("*")

        # Filtro de busca
        if search:
            # Busca por nome (ilike = case insensitive)
            query = query.or_(f"full_name.ilike.%{search}%,cpf.ilike.%{search}%")

        # Paginação
        query = query.range(offset, offset + limit - 1)

        # Executa query
        response = query.execute()

        patients = []
        for patient in response.data:
            # Busca última consulta do paciente
            last_analysis = supabase.table("case_analyses")\
                .select("created_at")\
                .eq("patient_id", patient["id"])\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            last_consultation = None
            if last_analysis.data:
                last_consultation = last_analysis.data[0]["created_at"]

            patients.append(PatientListItem(
                id=patient["id"],
                full_name=patient["full_name"],
                age=patient.get("age"),
                last_consultation=last_consultation,
                risk_level="low"  # TODO: Calcular risco baseado em análises
            ))

        return patients

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar pacientes: {str(e)}"
        )


@router.get("/prontuarios", response_model=List[ProntuarioItem])
async def list_prontuarios(
    current_doctor: dict = Depends(get_current_active_doctor),
    patient_id: Optional[str] = Query(None, description="Filtrar por paciente"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Lista prontuários/análises do médico

    Requer autenticação

    - **patient_id**: Filtrar por paciente específico (opcional)
    - **limit**: Quantidade de resultados
    - **offset**: Paginação

    Returns:
        Lista de prontuários
    """
    try:
        supabase = get_supabase_client()

        # Query base
        query = supabase.table("case_analyses")\
            .select("*")\
            .eq("doctor_crm", current_doctor["crm"])

        # Filtro por paciente
        if patient_id:
            query = query.eq("patient_id", patient_id)

        # Ordenação e paginação
        query = query.order("created_at", desc=True)\
            .range(offset, offset + limit - 1)

        response = query.execute()

        prontuarios = []
        for analysis in response.data:
            # Busca nome do paciente se tiver patient_id
            patient_name = None
            if analysis.get("patient_id"):
                patient = supabase.table("patients")\
                    .select("full_name")\
                    .eq("id", analysis["patient_id"])\
                    .execute()

                if patient.data:
                    patient_name = patient.data[0]["full_name"]

            # Extrai resumo da análise (primeiras linhas)
            analysis_text = analysis.get("analysis_result", "")
            summary = analysis_text[:200] + "..." if len(analysis_text) > 200 else analysis_text

            prontuarios.append(ProntuarioItem(
                id=analysis["id"],
                case_id=analysis["case_id"],
                patient_id=analysis.get("patient_id"),
                patient_name=patient_name,
                created_at=analysis["created_at"],
                summary=summary
            ))

        return prontuarios

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar prontuários: {str(e)}"
        )


@router.get("/prontuarios/{case_id}", response_model=dict)
async def get_prontuario_details(
    case_id: str,
    current_doctor: dict = Depends(get_current_active_doctor)
):
    """
    Retorna detalhes completos de um prontuário/análise

    Requer autenticação

    Args:
        case_id: ID do caso

    Returns:
        Prontuário completo
    """
    try:
        supabase = get_supabase_client()

        # Busca análise
        response = supabase.table("case_analyses")\
            .select("*")\
            .eq("case_id", case_id)\
            .eq("doctor_crm", current_doctor["crm"])\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Prontuário não encontrado"
            )

        analysis = response.data[0]

        # Busca dados do paciente se tiver
        patient = None
        if analysis.get("patient_id"):
            patient_response = supabase.table("patients")\
                .select("*")\
                .eq("id", analysis["patient_id"])\
                .execute()

            if patient_response.data:
                patient = patient_response.data[0]

        return {
            "case_id": analysis["case_id"],
            "transcription": analysis["transcription"],
            "analysis": analysis["analysis_result"],
            "created_at": analysis["created_at"],
            "patient": patient
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar prontuário: {str(e)}"
        )


@router.get("/agenda", response_model=List[AppointmentItem])
async def get_agenda(
    current_doctor: dict = Depends(get_current_active_doctor),
    date: Optional[str] = Query(None, description="Data (YYYY-MM-DD)"),
    days_ahead: int = Query(7, ge=1, le=30, description="Dias à frente")
):
    """
    Retorna agenda do médico

    NOTA: Por enquanto retorna agenda simulada.
    TODO: Implementar sistema completo de agendamento

    Requer autenticação

    - **date**: Data inicial (padrão: hoje)
    - **days_ahead**: Quantos dias mostrar (1-30)

    Returns:
        Lista de compromissos
    """
    # Por enquanto retorna agenda simulada
    # TODO: Criar tabela 'appointments' no Supabase

    appointments = [
        AppointmentItem(
            id="1",
            patient_name="João Silva",
            patient_id="patient-1",
            datetime=(datetime.now() + timedelta(hours=2)).isoformat(),
            type="consulta",
            status="scheduled"
        ),
        AppointmentItem(
            id="2",
            patient_name="Maria Santos",
            patient_id="patient-2",
            datetime=(datetime.now() + timedelta(days=1, hours=10)).isoformat(),
            type="retorno",
            status="scheduled"
        )
    ]

    return appointments


@router.get("/patient/{patient_id}/timeline", response_model=List[dict])
async def get_patient_timeline(
    patient_id: str,
    current_doctor: dict = Depends(get_current_active_doctor)
):
    """
    Retorna linha do tempo de um paciente
    (consultas, exames, diagnósticos em ordem cronológica)

    Requer autenticação

    Args:
        patient_id: ID do paciente

    Returns:
        Timeline de eventos do paciente
    """
    try:
        supabase = get_supabase_client()

        # Busca todas as análises do paciente
        response = supabase.table("case_analyses")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .order("created_at", desc=False)\
            .execute()

        timeline = []
        for analysis in response.data:
            # Extrai diagnóstico resumido
            analysis_text = analysis.get("analysis_result", "")
            diagnosis = "Análise cardiológica"

            # Tenta extrair diagnóstico do SOAP
            if "AVALIAÇÃO:" in analysis_text:
                parts = analysis_text.split("AVALIAÇÃO:")
                if len(parts) > 1:
                    diagnosis_section = parts[1].split("PLANO:")[0]
                    diagnosis = diagnosis_section.strip()[:100]

            timeline.append({
                "id": analysis["id"],
                "type": "consultation",
                "date": analysis["created_at"],
                "doctor": analysis["doctor_name"],
                "summary": diagnosis,
                "case_id": analysis["case_id"]
            })

        return timeline

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar timeline: {str(e)}"
        )
