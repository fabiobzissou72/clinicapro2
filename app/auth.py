"""
Sistema de Autenticação JWT para ClinicaPro
Gerenciamento de autenticação, autorização e tokens
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

load_dotenv()

# Configurações
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Context para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


# ===== PASSWORD HASHING =====

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se senha em texto plano corresponde ao hash

    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash armazenado no banco

    Returns:
        True se senha válida, False caso contrário
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera hash bcrypt de senha

    Args:
        password: Senha em texto plano

    Returns:
        Hash bcrypt da senha
    """
    # Bcrypt tem limite de 72 bytes - trunca se necessário
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')

    return pwd_context.hash(password)


# ===== JWT TOKEN MANAGEMENT =====

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria token JWT de acesso

    Args:
        data: Dados a serem codificados no token (ex: {"sub": "user_id"})
        expires_delta: Tempo de expiração customizado

    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica e valida token JWT

    Args:
        token: Token JWT a ser decodificado

    Returns:
        Payload do token se válido, None caso contrário
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ===== AUTHENTICATION DEPENDENCY =====

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency para obter usuário autenticado do token JWT

    Args:
        credentials: Credenciais HTTP Bearer (token)

    Returns:
        Dados do usuário autenticado

    Raises:
        HTTPException 401: Token inválido ou expirado
    """
    token = credentials.credentials

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extrai dados do usuário do payload
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Retorna dados do payload (incluindo role, email, etc.)
    return {
        "id": user_id,
        "email": payload.get("email"),
        "name": payload.get("name"),
        "role": payload.get("role", "doctor"),
        "crm": payload.get("crm")
    }


async def get_current_active_doctor(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency para garantir que usuário é médico ativo

    Args:
        current_user: Usuário autenticado

    Returns:
        Dados do médico autenticado

    Raises:
        HTTPException 403: Usuário não é médico
    """
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a médicos"
        )

    return current_user


# ===== DOCTOR REGISTRATION & LOGIN =====

from app.database.models import get_supabase_client


async def register_doctor(
    name: str,
    crm: str,
    email: str,
    password: str,
    specialty: str = "Cardiologia",
    phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Registra novo médico no sistema

    Args:
        name: Nome completo
        crm: CRM (formato: 12345-UF)
        email: Email único
        password: Senha (será hasheada)
        specialty: Especialidade médica
        phone: Telefone (opcional)

    Returns:
        Dict com resultado da operação
    """
    try:
        supabase = get_supabase_client()

        # Verifica se CRM já existe
        existing_crm = supabase.table("doctors").select("id").eq("crm", crm).execute()
        if existing_crm.data:
            return {
                "status": "error",
                "error": "CRM já cadastrado no sistema"
            }

        # Verifica se email já existe
        existing_email = supabase.table("doctors").select("id").eq("email", email).execute()
        if existing_email.data:
            return {
                "status": "error",
                "error": "Email já cadastrado no sistema"
            }

        # Hash da senha
        hashed_password = get_password_hash(password)

        # Insere médico
        doctor_data = {
            "name": name,
            "crm": crm,
            "email": email,
            "password_hash": hashed_password,
            "specialty": specialty,
            "phone": phone,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }

        response = supabase.table("doctors").insert(doctor_data).execute()

        if response.data:
            doctor = response.data[0]
            # Remove password_hash da resposta
            doctor.pop("password_hash", None)

            return {
                "status": "success",
                "doctor": doctor,
                "message": "Médico cadastrado com sucesso"
            }
        else:
            return {
                "status": "error",
                "error": "Erro ao cadastrar médico"
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


async def authenticate_doctor(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Autentica médico por email e senha

    Args:
        email: Email do médico
        password: Senha em texto plano

    Returns:
        Dados do médico se autenticado, None caso contrário
    """
    try:
        supabase = get_supabase_client()

        # Busca médico por email
        response = supabase.table("doctors").select("*").eq("email", email).execute()

        if not response.data:
            return None

        doctor = response.data[0]

        # Verifica se está ativo
        if not doctor.get("is_active", True):
            return None

        # Verifica senha
        if not verify_password(password, doctor["password_hash"]):
            return None

        # Remove password_hash antes de retornar
        doctor.pop("password_hash", None)

        return doctor

    except Exception as e:
        return None


async def create_doctor_token(doctor: Dict[str, Any]) -> str:
    """
    Cria token JWT para médico autenticado

    Args:
        doctor: Dados do médico

    Returns:
        Token JWT
    """
    token_data = {
        "sub": doctor["id"],
        "email": doctor["email"],
        "name": doctor["name"],
        "crm": doctor["crm"],
        "role": "doctor"
    }

    access_token = create_access_token(data=token_data)
    return access_token
