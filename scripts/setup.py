"""
Script de Setup Inicial do ClinicaPro Cardio
Verifica dependências e configura ambiente
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def check_python_version():
    """Verifica versão do Python"""
    print_header("🐍 Verificando Python")
    version = sys.version_info
    print(f"Versão: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ é necessário!")
        return False

    print("✅ Versão OK")
    return True


def check_docker():
    """Verifica se Docker está instalado"""
    print_header("🐋 Verificando Docker")
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout.strip())
        print("✅ Docker instalado")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker não encontrado")
        print("Instale em: https://www.docker.com/get-started")
        return False


def check_docker_compose():
    """Verifica se Docker Compose está instalado"""
    print_header("🐋 Verificando Docker Compose")
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout.strip())
        print("✅ Docker Compose instalado")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker Compose não encontrado")
        return False


def check_env_file():
    """Verifica arquivo .env"""
    print_header("📄 Verificando .env")

    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Arquivo .env não encontrado!")
        return False

    print("✅ Arquivo .env existe")

    # Verifica variáveis críticas
    critical_vars = [
        "OPENAI_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY"
    ]

    missing = []
    with open(env_path) as f:
        content = f.read()
        for var in critical_vars:
            if f"{var}=" not in content or f"{var}=your-" in content or f"{var}=sk-proj-" in content:
                missing.append(var)

    if missing:
        print(f"\n⚠️  Variáveis não configuradas:")
        for var in missing:
            print(f"   - {var}")
        print("\nEdite o arquivo .env antes de continuar.")
        return False

    print("✅ Variáveis críticas configuradas")
    return True


def check_venv():
    """Verifica se está em ambiente virtual"""
    print_header("📦 Verificando Ambiente Virtual")

    if hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    ):
        print("✅ Ambiente virtual ativo")
        return True
    else:
        print("⚠️  Não está em ambiente virtual")
        print("\nRecomendado criar e ativar:")
        print("  python -m venv venv")
        print("  venv\\Scripts\\activate  (Windows)")
        print("  source venv/bin/activate  (Linux/Mac)")
        return False


def install_dependencies():
    """Instala dependências"""
    print_header("📦 Instalando Dependências")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=True
        )
        print("✅ pip atualizado")

        print("\nInstalando requirements.txt...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("✅ Dependências instaladas")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar: {e}")
        return False


def start_docker_services():
    """Inicia serviços Docker"""
    print_header("🐋 Iniciando Serviços Docker")

    try:
        print("Iniciando Qdrant e Redis...")
        subprocess.run(
            ["docker-compose", "up", "-d"],
            check=True
        )
        print("✅ Serviços iniciados")

        print("\nVerificando status...")
        subprocess.run(["docker-compose", "ps"])
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao iniciar: {e}")
        return False


def main():
    """Setup principal"""
    print("\n" + "="*60)
    print("  🏥 CLINICAPRO CARDIO - SETUP")
    print("="*60)

    checks = {
        "Python 3.11+": check_python_version(),
        "Docker": check_docker(),
        "Docker Compose": check_docker_compose(),
        ".env configurado": check_env_file(),
        "Ambiente Virtual": check_venv()
    }

    # Resumo
    print_header("📊 Resumo das Verificações")
    all_ok = True
    for check, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check}")
        if not status:
            all_ok = False

    if not all_ok:
        print("\n⚠️  Resolva os problemas acima antes de continuar.")
        sys.exit(1)

    # Instalação
    print_header("🚀 Configuração")
    response = input("\nDeseja instalar dependências? (s/n): ").lower()

    if response == 's':
        if not install_dependencies():
            sys.exit(1)

    # Docker
    response = input("\nDeseja iniciar serviços Docker? (s/n): ").lower()

    if response == 's':
        if not start_docker_services():
            sys.exit(1)

    # Finalização
    print_header("✅ SETUP CONCLUÍDO!")
    print("\n📋 Próximos passos:")
    print("\n1. Configure Supabase:")
    print("   - Acesse seu projeto Supabase")
    print("   - Execute: scripts/setup_supabase_tables.sql")
    print("\n2. Teste o sistema:")
    print("   python tests/test_cardio_crew.py")
    print("\n3. Inicie a API:")
    print("   uvicorn app.main:app --reload")
    print("\n4. Acesse documentação:")
    print("   http://localhost:8000/docs")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()
