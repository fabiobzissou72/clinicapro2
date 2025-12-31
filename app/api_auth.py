"""
API de Autenticação - Login, Registro e Gestão de Médicos
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from app.auth import (
    register_doctor,
    authenticate_doctor,
    create_doctor_token,
    get_current_active_doctor
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ===== MODELS =====

class DoctorRegisterRequest(BaseModel):
    """Request para registro de médico"""
    name: str = Field(..., min_length=3, description="Nome completo do médico")
    crm: str = Field(..., pattern=r"^\d{4,6}-[A-Z]{2}$", description="CRM no formato 12345-UF")
    email: EmailStr = Field(..., description="Email único do médico")
    password: str = Field(..., min_length=8, max_length=72, description="Senha (8-72 caracteres)")
    specialty: str = Field(default="Cardiologia", description="Especialidade médica")
    phone: Optional[str] = Field(default=None, description="Telefone com DDD")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Dr. João Silva",
                "crm": "12345-SP",
                "email": "joao.silva@clinica.com.br",
                "password": "senhaSegura123",
                "specialty": "Cardiologia",
                "phone": "(11) 98765-4321"
            }
        }


class DoctorLoginRequest(BaseModel):
    """Request para login"""
    email: EmailStr = Field(..., description="Email cadastrado")
    password: str = Field(..., description="Senha")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "joao.silva@clinica.com.br",
                "password": "senhaSegura123"
            }
        }


class TokenResponse(BaseModel):
    """Response com token de acesso"""
    access_token: str = Field(..., description="Token JWT de acesso")
    token_type: str = Field(default="bearer", description="Tipo do token")
    doctor: dict = Field(..., description="Dados do médico autenticado")


class DoctorProfileResponse(BaseModel):
    """Response com perfil do médico"""
    id: str
    name: str
    crm: str
    email: str
    specialty: str
    phone: Optional[str]
    is_active: bool
    created_at: str


class ChangePasswordRequest(BaseModel):
    """Request para mudar senha"""
    current_password: str = Field(..., description="Senha atual")
    new_password: str = Field(..., min_length=8, description="Nova senha (mínimo 8 caracteres)")


# ===== ENDPOINTS =====

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_new_doctor(request: DoctorRegisterRequest):
    """
    Registra novo médico no sistema

    - **name**: Nome completo (mínimo 3 caracteres)
    - **crm**: CRM no formato correto (ex: 12345-SP)
    - **email**: Email único e válido
    - **password**: Senha segura (mínimo 8 caracteres)
    - **specialty**: Especialidade médica (padrão: Cardiologia)
    - **phone**: Telefone de contato (opcional)

    Returns:
        Dados do médico cadastrado (sem senha)
    """
    result = await register_doctor(
        name=request.name,
        crm=request.crm,
        email=request.email,
        password=request.password,
        specialty=request.specialty,
        phone=request.phone
    )

    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return {
        "status": "success",
        "message": "Médico cadastrado com sucesso",
        "doctor": result["doctor"]
    }


@router.post("/login", response_model=TokenResponse)
async def login_doctor(request: DoctorLoginRequest):
    """
    Autentica médico e retorna token JWT

    - **email**: Email cadastrado
    - **password**: Senha

    Returns:
        Token de acesso JWT e dados do médico
    """
    doctor = await authenticate_doctor(request.email, request.password)

    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Cria token JWT
    access_token = await create_doctor_token(doctor)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        doctor=doctor
    )


@router.get("/me", response_model=DoctorProfileResponse)
async def get_my_profile(current_doctor: dict = Depends(get_current_active_doctor)):
    """
    Retorna perfil do médico autenticado

    Requer autenticação (Bearer token)

    Returns:
        Dados completos do perfil
    """
    from app.database.models import get_supabase_client

    try:
        supabase = get_supabase_client()

        # Busca dados completos do médico
        response = supabase.table("doctors")\
            .select("id, name, crm, email, specialty, phone, is_active, created_at")\
            .eq("id", current_doctor["id"])\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médico não encontrado"
            )

        return response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar perfil: {str(e)}"
        )


@router.put("/me", response_model=dict)
async def update_my_profile(
    name: Optional[str] = None,
    specialty: Optional[str] = None,
    phone: Optional[str] = None,
    current_doctor: dict = Depends(get_current_active_doctor)
):
    """
    Atualiza perfil do médico autenticado

    Requer autenticação (Bearer token)

    - **name**: Novo nome (opcional)
    - **specialty**: Nova especialidade (opcional)
    - **phone**: Novo telefone (opcional)

    Returns:
        Dados atualizados do médico
    """
    from app.database.models import get_supabase_client

    try:
        supabase = get_supabase_client()

        # Monta dados para atualização
        update_data = {}
        if name:
            update_data["name"] = name
        if specialty:
            update_data["specialty"] = specialty
        if phone:
            update_data["phone"] = phone

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum dado para atualizar"
            )

        update_data["updated_at"] = datetime.utcnow().isoformat()

        # Atualiza no banco
        response = supabase.table("doctors")\
            .update(update_data)\
            .eq("id", current_doctor["id"])\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao atualizar perfil"
            )

        # Remove password_hash se existir
        updated_doctor = response.data[0]
        updated_doctor.pop("password_hash", None)

        return {
            "status": "success",
            "message": "Perfil atualizado com sucesso",
            "doctor": updated_doctor
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar perfil: {str(e)}"
        )


@router.post("/change-password", response_model=dict)
async def change_password(
    request: ChangePasswordRequest,
    current_doctor: dict = Depends(get_current_active_doctor)
):
    """
    Altera senha do médico autenticado

    Requer autenticação (Bearer token)

    - **current_password**: Senha atual
    - **new_password**: Nova senha (mínimo 8 caracteres)

    Returns:
        Mensagem de sucesso
    """
    from app.database.models import get_supabase_client
    from app.auth import verify_password, get_password_hash

    try:
        supabase = get_supabase_client()

        # Busca médico com senha
        response = supabase.table("doctors")\
            .select("password_hash")\
            .eq("id", current_doctor["id"])\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médico não encontrado"
            )

        # Verifica senha atual
        if not verify_password(request.current_password, response.data[0]["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Senha atual incorreta"
            )

        # Hash da nova senha
        new_password_hash = get_password_hash(request.new_password)

        # Atualiza senha
        update_response = supabase.table("doctors")\
            .update({
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow().isoformat()
            })\
            .eq("id", current_doctor["id"])\
            .execute()

        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao atualizar senha"
            )

        return {
            "status": "success",
            "message": "Senha alterada com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao alterar senha: {str(e)}"
        )
