"""
Database Models para Supabase
Schema para armazenar análises e histórico
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import os
from supabase import create_client, Client

# ===== CLIENTE SUPABASE =====

def get_supabase_client() -> Client:
    """
    Cria cliente Supabase

    Returns:
        Cliente Supabase configurado
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devem estar configurados")

    return create_client(url, key)


# ===== MODELS =====

class CaseAnalysis(BaseModel):
    """Modelo para análise de caso"""
    id: Optional[str] = None
    case_id: str
    doctor_name: str
    doctor_crm: Optional[str] = None
    patient_id: Optional[str] = None
    transcription: str
    analysis_result: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "uuid-here",
                "doctor_name": "Dr. João Silva",
                "doctor_crm": "12345-SP",
                "patient_id": "PAC-001",
                "transcription": "Texto da consulta...",
                "analysis_result": "Análise SOAP..."
            }
        }


class Doctor(BaseModel):
    """Modelo para médico"""
    id: Optional[str] = None
    name: str
    crm: str
    specialty: Optional[str] = "Cardiologia"
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None


class Patient(BaseModel):
    """Modelo para paciente"""
    id: Optional[str] = None
    full_name: str
    cpf: str
    phone: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[str] = None  # YYYY-MM-DD
    age: Optional[int] = None
    gender: Optional[str] = None  # M, F, Outro
    blood_type: Optional[str] = None  # A+, B+, AB+, O+, A-, B-, AB-, O-

    # Endereço
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zipcode: Optional[str] = None

    # Emergência
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

    # Convênio
    health_insurance: Optional[str] = None
    insurance_number: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PatientHistory(BaseModel):
    """Histórico médico do paciente"""
    id: Optional[str] = None
    patient_id: str

    # Comorbidades
    comorbidities: Optional[list] = None  # Lista de doenças crônicas
    allergies: Optional[list] = None  # Alergias medicamentosas
    current_medications: Optional[list] = None  # Medicações em uso

    # História familiar
    family_history: Optional[str] = None

    # Hábitos
    smoker: Optional[bool] = None
    smoking_pack_years: Optional[int] = None
    alcohol_use: Optional[str] = None  # Nunca, Social, Diário
    physical_activity: Optional[str] = None

    # Dados cardiológicos
    previous_cardiac_events: Optional[list] = None  # IAM, AVC, etc.
    cardiac_risk_factors: Optional[list] = None  # HAS, DM, dislipidemia

    # Cirurgias prévias
    previous_surgeries: Optional[list] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ===== DATABASE OPERATIONS =====

async def save_case_analysis(
    case_id: str,
    doctor_name: str,
    transcription: str,
    analysis_result: str,
    doctor_crm: Optional[str] = None,
    patient_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Salva análise de caso no Supabase

    Args:
        case_id: ID único do caso
        doctor_name: Nome do médico
        transcription: Texto transcrito
        analysis_result: Resultado da análise
        doctor_crm: CRM do médico (opcional)
        patient_id: ID do paciente (opcional)

    Returns:
        Dict com resultado da operação
    """
    try:
        supabase = get_supabase_client()

        data = {
            "case_id": case_id,
            "doctor_name": doctor_name,
            "doctor_crm": doctor_crm,
            "patient_id": patient_id,
            "transcription": transcription,
            "analysis_result": analysis_result,
            "created_at": datetime.utcnow().isoformat()
        }

        response = supabase.table("case_analyses").insert(data).execute()

        return {
            "status": "success",
            "data": response.data
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


async def get_case_by_id(case_id: str) -> Optional[Dict[str, Any]]:
    """
    Recupera caso por ID

    Args:
        case_id: ID do caso

    Returns:
        Dict com dados do caso ou None
    """
    try:
        supabase = get_supabase_client()

        response = supabase.table("case_analyses")\
            .select("*")\
            .eq("case_id", case_id)\
            .execute()

        if response.data:
            return response.data[0]
        return None

    except Exception as e:
        return None


async def get_doctor_cases(doctor_crm: str, limit: int = 50) -> list:
    """
    Recupera casos de um médico

    Args:
        doctor_crm: CRM do médico
        limit: Número máximo de casos

    Returns:
        Lista de casos
    """
    try:
        supabase = get_supabase_client()

        response = supabase.table("case_analyses")\
            .select("*")\
            .eq("doctor_crm", doctor_crm)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()

        return response.data or []

    except Exception as e:
        return []


# ===== PATIENT OPERATIONS =====

async def create_patient(patient_data: dict) -> Dict[str, Any]:
    """
    Cria novo paciente

    Args:
        patient_data: Dados do paciente (dict conforme modelo Patient)

    Returns:
        Dict com resultado da operação
    """
    try:
        supabase = get_supabase_client()

        # Validações básicas
        if not patient_data.get("full_name") or not patient_data.get("cpf"):
            return {
                "status": "error",
                "error": "Nome completo e CPF são obrigatórios"
            }

        response = supabase.table("patients").insert(patient_data).execute()

        return {
            "status": "success",
            "data": response.data[0] if response.data else None,
            "patient_id": response.data[0]["id"] if response.data else None
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


async def get_patient_by_cpf(cpf: str) -> Optional[Dict[str, Any]]:
    """
    Busca paciente por CPF

    Args:
        cpf: CPF do paciente (com ou sem máscara)

    Returns:
        Dict com dados do paciente ou None
    """
    try:
        # Remove máscara do CPF
        cpf_clean = cpf.replace(".", "").replace("-", "")

        supabase = get_supabase_client()

        response = supabase.table("patients")\
            .select("*")\
            .eq("cpf", cpf_clean)\
            .execute()

        if response.data:
            return response.data[0]
        return None

    except Exception as e:
        return None


async def get_patient_history(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Recupera histórico médico do paciente

    Args:
        patient_id: ID do paciente

    Returns:
        Dict com histórico ou None
    """
    try:
        supabase = get_supabase_client()

        response = supabase.table("patient_history")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .execute()

        if response.data:
            return response.data[0]
        return None

    except Exception as e:
        return None


async def update_patient_history(patient_id: str, history_data: dict) -> Dict[str, Any]:
    """
    Atualiza histórico médico do paciente

    Args:
        patient_id: ID do paciente
        history_data: Dados do histórico

    Returns:
        Dict com resultado da operação
    """
    try:
        supabase = get_supabase_client()

        # Verifica se já existe histórico
        existing = await get_patient_history(patient_id)

        if existing:
            # Update
            response = supabase.table("patient_history")\
                .update(history_data)\
                .eq("patient_id", patient_id)\
                .execute()
        else:
            # Insert
            history_data["patient_id"] = patient_id
            response = supabase.table("patient_history")\
                .insert(history_data)\
                .execute()

        return {
            "status": "success",
            "data": response.data
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


async def get_patient_full_profile(patient_id: str) -> Dict[str, Any]:
    """
    Recupera perfil completo do paciente (dados + histórico)

    Args:
        patient_id: ID do paciente

    Returns:
        Dict com dados completos
    """
    try:
        supabase = get_supabase_client()

        # Busca dados do paciente
        patient_response = supabase.table("patients")\
            .select("*")\
            .eq("id", patient_id)\
            .execute()

        if not patient_response.data:
            return {
                "status": "error",
                "error": "Paciente não encontrado"
            }

        patient_data = patient_response.data[0]

        # Busca histórico
        history = await get_patient_history(patient_id)

        # Busca casos (análises) do paciente
        cases_response = supabase.table("case_analyses")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()

        return {
            "status": "success",
            "patient": patient_data,
            "history": history,
            "recent_cases": cases_response.data or []
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# ===== DOCTOR AUTH OPERATIONS (SEM API) =====

async def register_doctor(doctor_data: dict) -> Dict[str, Any]:
    """
    Cadastra novo médico DIRETO no banco

    Args:
        doctor_data: Dict com name, crm, email, password, specialty

    Returns:
        Dict com status e dados do médico
    """
    try:
        import bcrypt

        supabase = get_supabase_client()

        # Validações
        if not doctor_data.get("name") or not doctor_data.get("email"):
            return {
                "status": "error",
                "error": "Nome e email são obrigatórios"
            }

        if not doctor_data.get("password") or len(doctor_data["password"]) < 8:
            return {
                "status": "error",
                "error": "Senha deve ter no mínimo 8 caracteres"
            }

        # Verifica se email já existe
        existing = supabase.table("doctors").select("id").eq("email", doctor_data["email"]).execute()
        if existing.data:
            return {
                "status": "error",
                "error": "Email já cadastrado"
            }

        # Hash da senha
        password = doctor_data.pop("password")
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Prepara dados
        insert_data = {
            "name": doctor_data["name"],
            "crm": doctor_data.get("crm", ""),
            "email": doctor_data["email"],
            "password_hash": password_hash,
            "specialty": doctor_data.get("specialty", "Cardiologia")
        }

        # Insere no banco
        response = supabase.table("doctors").insert(insert_data).execute()

        if response.data:
            doctor = response.data[0]
            # Remove password_hash da resposta
            doctor.pop("password_hash", None)

            return {
                "status": "success",
                "doctor": doctor
            }
        else:
            return {
                "status": "error",
                "error": "Erro ao criar médico"
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


async def login_doctor(email: str, password: str) -> Dict[str, Any]:
    """
    Faz login do médico DIRETO no banco

    Args:
        email: Email do médico
        password: Senha

    Returns:
        Dict com status e dados do médico
    """
    try:
        import bcrypt

        supabase = get_supabase_client()

        # Busca médico por email
        response = supabase.table("doctors").select("*").eq("email", email).execute()

        if not response.data:
            return {
                "status": "error",
                "error": "Email ou senha inválidos"
            }

        doctor = response.data[0]
        password_hash = doctor.get("password_hash", "")

        # Verifica senha
        if not password_hash or not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            return {
                "status": "error",
                "error": "Email ou senha inválidos"
            }

        # Remove password_hash da resposta
        doctor.pop("password_hash", None)

        return {
            "status": "success",
            "doctor": doctor
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# ===== LISTAGEM OPERATIONS (SEM API) =====

async def list_patients(limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    """
    Lista pacientes DIRETO do banco

    Args:
        limit: Número máximo de pacientes
        offset: Offset para paginação

    Returns:
        Dict com lista de pacientes
    """
    try:
        supabase = get_supabase_client()

        response = supabase.table("patients")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .offset(offset)\
            .execute()

        return {
            "status": "success",
            "data": response.data or []
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


async def list_case_analyses(limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    """
    Lista prontuários (case_analyses) DIRETO do banco

    Args:
        limit: Número máximo de prontuários
        offset: Offset para paginação

    Returns:
        Dict com lista de prontuários
    """
    try:
        supabase = get_supabase_client()

        response = supabase.table("case_analyses")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .offset(offset)\
            .execute()

        return {
            "status": "success",
            "data": response.data or []
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
