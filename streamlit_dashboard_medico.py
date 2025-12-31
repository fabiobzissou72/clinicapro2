"""
Dashboard do Médico - ClinicaPro Cardio
Interface web para médicos visualizarem pacientes, prontuários e estatísticas
"""

import streamlit as st
import requests
from datetime import datetime
import pandas as pd
from pathlib import Path

# Configurações
st.set_page_config(
    page_title="ClinicaPro - Dashboard Médico",
    page_icon="👨‍⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL da API
API_URL = "http://localhost:8000"

# Inicializa session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'doctor' not in st.session_state:
    st.session_state.doctor = None


# ===== FUNÇÕES DE API =====

def login(email: str, password: str):
    """Faz login e retorna token"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            return data['access_token'], data['doctor']
        else:
            return None, None
    except Exception as e:
        st.error(f"Erro ao conectar com API: {e}")
        return None, None


def register(name: str, crm: str, email: str, password: str, specialty: str, phone: str):
    """Registra novo médico"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/auth/register",
            json={
                "name": name,
                "crm": crm,
                "email": email,
                "password": password,
                "specialty": specialty,
                "phone": phone
            }
        )
        if response.status_code == 201:
            return True, "Cadastro realizado com sucesso!"
        else:
            error = response.json().get('detail', 'Erro desconhecido')
            return False, error
    except Exception as e:
        return False, str(e)


def get_headers():
    """Retorna headers com token de autenticação"""
    return {"Authorization": f"Bearer {st.session_state.token}"}


def get_stats():
    """Busca estatísticas do médico"""
    try:
        response = requests.get(
            f"{API_URL}/api/v1/dashboard/stats",
            headers=get_headers()
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Erro: {e}")
        return None


def get_patients(search="", limit=50):
    """Busca lista de pacientes"""
    try:
        params = {"limit": limit}
        if search:
            params["search"] = search

        response = requests.get(
            f"{API_URL}/api/v1/dashboard/patients",
            headers=get_headers(),
            params=params
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Erro: {e}")
        return []


def get_prontuarios(patient_id=None, limit=20):
    """Busca prontuários"""
    try:
        params = {"limit": limit}
        if patient_id:
            params["patient_id"] = patient_id

        response = requests.get(
            f"{API_URL}/api/v1/dashboard/prontuarios",
            headers=get_headers(),
            params=params
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Erro: {e}")
        return []


def get_prontuario_details(case_id: str):
    """Busca detalhes de um prontuário"""
    try:
        response = requests.get(
            f"{API_URL}/api/v1/dashboard/prontuarios/{case_id}",
            headers=get_headers()
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Erro: {e}")
        return None


def get_patient_timeline(patient_id: str):
    """Busca timeline do paciente"""
    try:
        response = requests.get(
            f"{API_URL}/api/v1/dashboard/patient/{patient_id}/timeline",
            headers=get_headers()
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Erro: {e}")
        return []


# ===== PÁGINA DE LOGIN =====

def show_login_page():
    """Mostra página de login/registro"""

    # Logo (se existir)
    logo_path = Path("imagem/logo.png")
    if logo_path.exists():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(str(logo_path), width=300)

    st.title("🏥 ClinicaPro Cardio")
    st.markdown("### Sistema de Apoio à Decisão Cardiológica")

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Cadastro"])

    with tab1:
        st.subheader("Login")

        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Senha", type="password", key="login_password")

        if st.button("Entrar", type="primary", use_container_width=True, key="btn_login"):
            if login_email and login_password:
                with st.spinner("Autenticando..."):
                    token, doctor = login(login_email, login_password)

                    if token:
                        st.session_state.token = token
                        st.session_state.doctor = doctor
                        st.success(f"✅ Bem-vindo, {doctor['name']}!")
                        st.rerun()
                    else:
                        st.error("❌ Email ou senha inválidos")
            else:
                st.warning("Preencha email e senha")

    with tab2:
        st.subheader("Cadastro de Novo Médico")

        col1, col2 = st.columns(2)

        with col1:
            reg_name = st.text_input("Nome Completo", key="reg_name")
            reg_crm = st.text_input("CRM (ex: 12345-SP)", key="reg_crm")
            reg_email = st.text_input("Email", key="reg_email")

        with col2:
            reg_specialty = st.selectbox(
                "Especialidade",
                ["Cardiologia", "Clínica Médica", "Medicina Interna"],
                key="reg_specialty"
            )
            reg_phone = st.text_input("Telefone (opcional)", key="reg_phone")
            reg_password = st.text_input("Senha (mín. 8 caracteres)", type="password", key="reg_password")

        if st.button("Cadastrar", type="primary", use_container_width=True, key="btn_register"):
            # Debug: mostrar valores
            if not reg_name or not reg_crm or not reg_email or not reg_password:
                st.warning("⚠️ Preencha todos os campos obrigatórios")
                if not reg_name:
                    st.error("❌ Nome não preenchido")
                if not reg_crm:
                    st.error("❌ CRM não preenchido")
                if not reg_email:
                    st.error("❌ Email não preenchido")
                if not reg_password:
                    st.error("❌ Senha não preenchida")
            elif len(reg_password) < 8:
                st.error("❌ Senha deve ter no mínimo 8 caracteres")
            else:
                with st.spinner("Cadastrando..."):
                    success, message = register(reg_name, reg_crm, reg_email, reg_password, reg_specialty, reg_phone)

                    if success:
                        st.success(f"✅ {message}")
                        st.info("💡 Agora você pode fazer login na aba 'Login'")
                    else:
                        st.error(f"❌ {message}")


# ===== PÁGINA PRINCIPAL (AUTENTICADO) =====

def show_dashboard():
    """Mostra dashboard principal"""

    # Sidebar
    with st.sidebar:
        # Logo menor
        logo_path = Path("imagem/logo.png")
        if logo_path.exists():
            st.image(str(logo_path), width=150)

        st.title("👨‍⚕️ Dashboard")

        st.markdown(f"**Dr(a). {st.session_state.doctor['name']}**")
        st.caption(f"CRM: {st.session_state.doctor['crm']}")

        st.markdown("---")

        page = st.radio(
            "Navegação",
            ["📊 Visão Geral", "👥 Pacientes", "📋 Prontuários", "📅 Agenda"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.token = None
            st.session_state.doctor = None
            st.rerun()

    # Conteúdo principal
    if page == "📊 Visão Geral":
        show_overview_page()
    elif page == "👥 Pacientes":
        show_patients_page()
    elif page == "📋 Prontuários":
        show_prontuarios_page()
    elif page == "📅 Agenda":
        show_agenda_page()


# ===== PÁGINA: VISÃO GERAL =====

def show_overview_page():
    """Mostra visão geral com estatísticas"""

    st.title("📊 Visão Geral")

    # Busca estatísticas
    with st.spinner("Carregando estatísticas..."):
        stats = get_stats()

    if stats:
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total de Pacientes",
                stats['total_patients'],
                help="Total de pacientes cadastrados"
            )

        with col2:
            st.metric(
                "Consultas Totais",
                stats['total_consultations'],
                help="Total de análises realizadas"
            )

        with col3:
            st.metric(
                "Este Mês",
                stats['consultations_this_month'],
                delta=f"+{stats['consultations_today']} hoje",
                help="Consultas realizadas neste mês"
            )

        with col4:
            st.metric(
                "Média por Dia",
                f"{stats['avg_consultations_per_day']:.1f}",
                help="Média de consultas por dia (últimos 30 dias)"
            )

        st.markdown("---")

        # Prontuários recentes
        st.subheader("📋 Prontuários Recentes")

        prontuarios = get_prontuarios(limit=5)

        if prontuarios:
            for p in prontuarios:
                with st.expander(
                    f"📄 {p['patient_name'] or 'Paciente não vinculado'} - {p['created_at'][:10]}"
                ):
                    st.markdown(f"**Case ID:** `{p['case_id']}`")
                    st.markdown(f"**Resumo:** {p['summary']}")

                    if st.button(f"Ver detalhes", key=f"view_{p['id']}"):
                        details = get_prontuario_details(p['case_id'])
                        if details:
                            st.markdown("### Análise Completa")
                            st.markdown(details['analysis'])
        else:
            st.info("Nenhum prontuário encontrado")
    else:
        st.error("Erro ao carregar estatísticas. Verifique se a API está rodando.")


# ===== PÁGINA: PACIENTES =====

def show_patients_page():
    """Mostra lista de pacientes"""

    st.title("👥 Pacientes")

    # Busca
    search = st.text_input("🔍 Buscar paciente (nome ou CPF)", placeholder="Digite para buscar...")

    # Busca pacientes
    with st.spinner("Buscando pacientes..."):
        patients = get_patients(search=search)

    if patients:
        st.caption(f"Encontrados {len(patients)} pacientes")

        # Lista de pacientes
        for patient in patients:
            with st.expander(
                f"👤 {patient['full_name']} - {patient['age'] or '?'} anos"
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**ID:** `{patient['id']}`")
                    st.markdown(f"**Idade:** {patient['age'] or 'Não informada'} anos")
                    st.markdown(f"**Última consulta:** {patient['last_consultation'] or 'Nunca'}")

                with col2:
                    risk_color = {
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🔴"
                    }.get(patient.get('risk_level', 'low'), "⚪")

                    st.markdown(f"**Nível de risco:** {risk_color} {patient.get('risk_level', 'low').upper()}")

                # Botões de ação
                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button("📋 Ver prontuários", key=f"pront_{patient['id']}"):
                        st.session_state.selected_patient_id = patient['id']
                        st.session_state.selected_patient_name = patient['full_name']

                with col_b:
                    if st.button("📅 Ver timeline", key=f"timeline_{patient['id']}"):
                        timeline = get_patient_timeline(patient['id'])
                        if timeline:
                            st.markdown("### Timeline do Paciente")
                            for event in timeline:
                                st.markdown(f"**{event['date'][:10]}** - {event['summary']}")
                        else:
                            st.info("Nenhum evento encontrado")

        # Se paciente foi selecionado, mostra prontuários
        if hasattr(st.session_state, 'selected_patient_id'):
            st.markdown("---")
            st.subheader(f"📋 Prontuários de {st.session_state.selected_patient_name}")

            prontuarios = get_prontuarios(patient_id=st.session_state.selected_patient_id)

            for p in prontuarios:
                with st.expander(f"📄 {p['created_at'][:10]} - {p['summary'][:50]}..."):
                    details = get_prontuario_details(p['case_id'])
                    if details:
                        st.markdown(details['analysis'])

    else:
        st.info("Nenhum paciente encontrado")


# ===== PÁGINA: PRONTUÁRIOS =====

def show_prontuarios_page():
    """Mostra lista de prontuários"""

    st.title("📋 Prontuários")

    # Busca prontuários
    with st.spinner("Carregando prontuários..."):
        prontuarios = get_prontuarios(limit=50)

    if prontuarios:
        st.caption(f"Total: {len(prontuarios)} prontuários")

        for p in prontuarios:
            patient_info = p['patient_name'] or "Paciente não vinculado"
            date = p['created_at'][:10] if p['created_at'] else "Data desconhecida"

            with st.expander(f"📄 {date} - {patient_info}"):
                st.markdown(f"**Case ID:** `{p['case_id']}`")
                st.markdown(f"**Resumo:** {p['summary']}")

                if st.button("📖 Ver análise completa", key=f"details_{p['id']}"):
                    details = get_prontuario_details(p['case_id'])

                    if details:
                        st.markdown("---")
                        st.markdown("### Transcrição da Consulta")
                        st.text(details['transcription'])

                        st.markdown("---")
                        st.markdown("### Análise SOAP")
                        st.markdown(details['analysis'])

                        if details.get('patient'):
                            st.markdown("---")
                            st.markdown("### Dados do Paciente")
                            st.json(details['patient'])
    else:
        st.info("Nenhum prontuário encontrado")


# ===== PÁGINA: AGENDA =====

def show_agenda_page():
    """Mostra agenda do médico"""

    st.title("📅 Agenda")

    st.info("⚠️ Funcionalidade de agenda em desenvolvimento")

    st.markdown("""
    **Em breve você poderá:**
    - Ver compromissos agendados
    - Agendar novas consultas
    - Marcar retornos
    - Receber notificações no Telegram
    """)


# ===== MAIN =====

def main():
    """Função principal"""

    # Verifica se está autenticado
    if st.session_state.token is None:
        show_login_page()
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
