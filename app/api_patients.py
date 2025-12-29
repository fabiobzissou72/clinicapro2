"""
ClinicaPro Cardio - Patient Management API Endpoints
Endpoints para gerenciar pacientes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

from app.database.models import (
    create_patient,
    get_patient_by_cpf,
    get_patient_history,
    update_patient_history,
    get_patient_full_profile
)

# Router para pacientes
router = APIRouter(prefix="/api/v1/patients", tags=["Patients"])


# ===== MODELS =====

class PatientCreate(BaseModel):
    """Modelo para criar paciente"""
    full_name: str = Field(..., min_length=3, description="Nome completo")
    cpf: str = Field(..., min_length=11, max_length=14, description="CPF (com ou sem máscara)")
    phone: Optional[str] = Field(None, description="Telefone")
    email: Optional[str] = Field(None, description="E-mail")
    birth_date: Optional[str] = Field(None, description="Data de nascimento (YYYY-MM-DD)")
    gender: Optional[str] = Field(None, description="Gênero (M/F/Outro)")
    blood_type: Optional[str] = Field(None, description="Tipo sanguíneo")

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

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "João da Silva",
                "cpf": "123.456.789-00",
                "phone": "(11) 98765-4321",
                "email": "joao.silva@email.com",
                "birth_date": "1965-05-15",
                "gender": "M",
                "blood_type": "O+",
                "address_city": "São Paulo",
                "address_state": "SP",
                "emergency_contact_name": "Maria Silva",
                "emergency_contact_phone": "(11) 91234-5678",
                "health_insurance": "Unimed"
            }
        }


class PatientHistoryUpdate(BaseModel):
    """Modelo para atualizar histórico médico"""
    comorbidities: Optional[List[str]] = Field(default=[], description="Lista de comorbidades")
    allergies: Optional[List[str]] = Field(default=[], description="Alergias medicamentosas")
    current_medications: Optional[List[dict]] = Field(default=[], description="Medicações em uso")

    family_history: Optional[str] = None

    smoker: Optional[bool] = None
    smoking_pack_years: Optional[int] = None
    alcohol_use: Optional[str] = None
    physical_activity: Optional[str] = None

    previous_cardiac_events: Optional[List[str]] = Field(default=[])
    cardiac_risk_factors: Optional[List[str]] = Field(default=[])
    previous_surgeries: Optional[List[dict]] = Field(default=[])

    class Config:
        json_schema_extra = {
            "example": {
                "comorbidities": ["Hipertensão Arterial", "Diabetes Mellitus Tipo 2", "Dislipidemia"],
                "allergies": ["Penicilina"],
                "current_medications": [
                    {"name": "Losartana", "dose": "50mg", "frequency": "12/12h"},
                    {"name": "Metformina", "dose": "850mg", "frequency": "12/12h"}
                ],
                "smoker": False,
                "smoking_pack_years": 20,
                "alcohol_use": "Social",
                "cardiac_risk_factors": ["HAS", "DM tipo 2", "Ex-tabagista"],
                "previous_cardiac_events": ["IAM 2020"]
            }
        }


# ===== ENDPOINTS =====

@router.post("/", status_code=201)
async def create_new_patient(patient: PatientCreate):
    """
    Cria novo paciente no sistema

    - **full_name**: Nome completo (obrigatório)
    - **cpf**: CPF do paciente (obrigatório, único)
    - Outros campos opcionais
    """
    # Remove máscara do CPF
    cpf_clean = patient.cpf.replace(".", "").replace("-", "")

    # Verifica se já existe
    existing = await get_patient_by_cpf(cpf_clean)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Paciente com CPF {patient.cpf} já cadastrado"
        )

    # Prepara dados
    patient_data = patient.model_dump()
    patient_data["cpf"] = cpf_clean

    # Cria paciente
    result = await create_patient(patient_data)

    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result["error"]
        )

    return {
        "status": "success",
        "message": "Paciente cadastrado com sucesso",
        "patient_id": result["patient_id"],
        "data": result["data"]
    }


@router.get("/{cpf}")
async def get_patient(cpf: str):
    """
    Busca paciente por CPF

    - **cpf**: CPF do paciente (com ou sem máscara)
    """
    patient = await get_patient_by_cpf(cpf)

    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Paciente com CPF {cpf} não encontrado"
        )

    return {
        "status": "success",
        "data": patient
    }


@router.get("/{patient_id}/profile")
async def get_patient_profile(patient_id: str):
    """
    Recupera perfil completo do paciente (dados + histórico + casos recentes)

    - **patient_id**: ID do paciente (UUID)
    """
    profile = await get_patient_full_profile(patient_id)

    if profile["status"] == "error":
        raise HTTPException(
            status_code=404,
            detail=profile["error"]
        )

    return profile


@router.get("/{patient_id}/history")
async def get_patient_medical_history(patient_id: str):
    """
    Recupera histórico médico do paciente

    - **patient_id**: ID do paciente (UUID)
    """
    history = await get_patient_history(patient_id)

    if not history:
        return {
            "status": "success",
            "message": "Histórico não encontrado",
            "data": None
        }

    return {
        "status": "success",
        "data": history
    }


@router.put("/{patient_id}/history")
async def update_patient_medical_history(patient_id: str, history: PatientHistoryUpdate):
    """
    Atualiza histórico médico do paciente

    - **patient_id**: ID do paciente (UUID)
    - Campos do histórico (comorbidades, alergias, etc.)
    """
    # Valida se paciente existe
    patient = await get_patient_by_cpf(patient_id)  # TODO: Buscar por ID, não CPF
    # if not patient:
    #     raise HTTPException(
    #         status_code=404,
    #         detail="Paciente não encontrado"
    #     )

    # Atualiza histórico
    result = await update_patient_history(
        patient_id=patient_id,
        history_data=history.model_dump()
    )

    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result["error"]
        )

    return {
        "status": "success",
        "message": "Histórico atualizado com sucesso",
        "data": result["data"]
    }
