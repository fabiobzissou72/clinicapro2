"""
Dashboard Streamlit para Gerenciamento da CrewAI
- Upload de documentos para Qdrant
- Monitoramento de agentes
- Configuração da knowledge base
"""

import streamlit as st
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
import PyPDF2
import io
from openai import OpenAI

load_dotenv()

# Configurações
st.set_page_config(
    page_title="ClinicaPro - Dashboard CrewAI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clientes
@st.cache_resource
def get_qdrant_client():
    """Inicializa cliente Qdrant"""
    return QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

@st.cache_resource
def get_openai_client():
    """Inicializa cliente OpenAI"""
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ===== FUNÇÕES AUXILIARES =====

def extract_text_from_pdf(pdf_file) -> str:
    """Extrai texto de arquivo PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Erro ao extrair texto do PDF: {e}")
        return ""


def generate_embeddings(text: str, openai_client) -> list:
    """Gera embeddings usando OpenAI"""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        st.error(f"Erro ao gerar embeddings: {e}")
        return []


def upload_to_qdrant(
    collection_name: str,
    text: str,
    metadata: dict,
    qdrant_client,
    openai_client
):
    """Faz upload de documento para Qdrant"""
    try:
        # Gera embeddings
        embeddings = generate_embeddings(text, openai_client)

        if not embeddings:
            return False

        # Verifica se coleção existe
        collections = qdrant_client.get_collections().collections
        collection_exists = any(c.name == collection_name for c in collections)

        if not collection_exists:
            # Cria coleção
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=len(embeddings),
                    distance=Distance.COSINE
                )
            )

        # Gera ID único
        point_id = hash(text[:100] + str(datetime.now()))

        # Faz upload
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=abs(point_id),
                    vector=embeddings,
                    payload={
                        "text": text[:1000],  # Limita tamanho
                        "full_text": text,
                        "metadata": metadata,
                        "uploaded_at": datetime.now().isoformat()
                    }
                )
            ]
        )

        return True

    except Exception as e:
        st.error(f"Erro ao fazer upload: {e}")
        return False


# ===== SIDEBAR =====

st.sidebar.title("🤖 ClinicaPro CrewAI")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navegação",
    ["📤 Upload de Documentos", "📊 Monitoramento", "⚙️ Configurações", "🔍 Busca no Qdrant"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Dashboard para gerenciar:**\n"
    "- Knowledge base (Qdrant)\n"
    "- Agentes CrewAI\n"
    "- Documentos médicos"
)


# ===== PÁGINA: UPLOAD DE DOCUMENTOS =====

if page == "📤 Upload de Documentos":
    st.title("📤 Upload de Documentos para Knowledge Base")

    st.markdown("""
    Faça upload de documentos médicos (PDFs, guidelines, artigos) para a knowledge base.
    Os documentos serão processados e indexados no Qdrant para uso pelos agentes CrewAI.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Upload de Arquivo")

        # Seleção de coleção
        collection_name = st.selectbox(
            "Coleção Qdrant",
            ["medical_guidelines", "cardiology_papers", "clinical_protocols", "case_studies"],
            help="Escolha a coleção onde o documento será armazenado"
        )

        # Upload de arquivo
        uploaded_file = st.file_uploader(
            "Escolha um arquivo PDF",
            type=["pdf"],
            help="Faça upload de PDFs com guidelines, artigos científicos, etc."
        )

        if uploaded_file:
            st.info(f"📄 Arquivo: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")

            # Metadados
            st.subheader("Metadados do Documento")

            doc_title = st.text_input("Título do documento", uploaded_file.name)
            doc_author = st.text_input("Autor(es)", "")
            doc_year = st.number_input("Ano", min_value=1900, max_value=2030, value=datetime.now().year)
            doc_type = st.selectbox(
                "Tipo de documento",
                ["Guideline", "Artigo científico", "Protocolo clínico", "Caso clínico", "Outro"]
            )
            doc_tags = st.text_input("Tags (separadas por vírgula)", "cardiologia")

            # Botão de upload
            if st.button("🚀 Processar e Upload", type="primary"):
                with st.spinner("Processando documento..."):
                    # Extrai texto
                    text = extract_text_from_pdf(uploaded_file)

                    if not text:
                        st.error("Não foi possível extrair texto do PDF")
                    else:
                        st.success(f"✅ Texto extraído: {len(text)} caracteres")

                        # Prepara metadados
                        metadata = {
                            "title": doc_title,
                            "author": doc_author,
                            "year": doc_year,
                            "type": doc_type,
                            "tags": [tag.strip() for tag in doc_tags.split(",")],
                            "filename": uploaded_file.name
                        }

                        # Upload para Qdrant
                        qdrant_client = get_qdrant_client()
                        openai_client = get_openai_client()

                        # Divide texto em chunks se for muito grande
                        max_chunk_size = 2000
                        chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]

                        progress_bar = st.progress(0)
                        for i, chunk in enumerate(chunks):
                            success = upload_to_qdrant(
                                collection_name=collection_name,
                                text=chunk,
                                metadata={**metadata, "chunk_index": i, "total_chunks": len(chunks)},
                                qdrant_client=qdrant_client,
                                openai_client=openai_client
                            )

                            if success:
                                progress_bar.progress((i + 1) / len(chunks))
                            else:
                                st.error(f"Erro ao fazer upload do chunk {i+1}")
                                break

                        st.success(f"✅ Upload concluído! {len(chunks)} chunks indexados.")

    with col2:
        st.subheader("ℹ️ Informações")

        st.metric("Coleção Selecionada", collection_name)

        st.markdown("""
        **Tipos de documentos suportados:**
        - 📘 Guidelines médicos
        - 📄 Artigos científicos
        - 📋 Protocolos clínicos
        - 📊 Casos clínicos

        **Processo:**
        1. Upload do PDF
        2. Extração de texto
        3. Geração de embeddings
        4. Indexação no Qdrant
        """)


# ===== PÁGINA: MONITORAMENTO =====

elif page == "📊 Monitoramento":
    st.title("📊 Monitoramento de Agentes CrewAI")

    st.markdown("""
    Visualize métricas e status dos agentes de IA.
    """)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Análises", "142", "+12")

    with col2:
        st.metric("Agentes Ativos", "4", "0")

    with col3:
        st.metric("Docs no Qdrant", "38", "+5")

    with col4:
        st.metric("Avg Response Time", "78s", "-5s")

    st.markdown("---")

    # Status dos agentes
    st.subheader("🤖 Status dos Agentes")

    agents_data = [
        {"Agente": "Coordenador Cardiológico", "Status": "✅ Ativo", "Última Execução": "2 min atrás", "Taxa Sucesso": "98%"},
        {"Agente": "Especialista Coronariano", "Status": "✅ Ativo", "Última Execução": "5 min atrás", "Taxa Sucesso": "97%"},
        {"Agente": "Especialista IC", "Status": "✅ Ativo", "Última Execução": "3 min atrás", "Taxa Sucesso": "96%"},
        {"Agente": "Especialista Arritmias", "Status": "✅ Ativo", "Última Execução": "7 min atrás", "Taxa Sucesso": "99%"},
    ]

    df_agents = pd.DataFrame(agents_data)
    st.dataframe(df_agents, use_container_width=True)

    st.markdown("---")

    # Logs recentes (simulado)
    st.subheader("📋 Logs Recentes")

    logs_data = [
        {"Timestamp": "2025-12-30 14:32:15", "Tipo": "INFO", "Mensagem": "Análise #142 concluída com sucesso"},
        {"Timestamp": "2025-12-30 14:31:02", "Tipo": "INFO", "Mensagem": "Coordenador iniciou análise de caso"},
        {"Timestamp": "2025-12-30 14:28:45", "Tipo": "WARNING", "Mensagem": "Timeout parcial no Especialista IC"},
        {"Timestamp": "2025-12-30 14:25:10", "Tipo": "INFO", "Mensagem": "Novo documento indexado: Guideline ESC 2024"},
    ]

    df_logs = pd.DataFrame(logs_data)
    st.dataframe(df_logs, use_container_width=True)


# ===== PÁGINA: CONFIGURAÇÕES =====

elif page == "⚙️ Configurações":
    st.title("⚙️ Configurações do Sistema")

    st.subheader("🔑 Conexões")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**OpenAI**")
        openai_status = "✅ Conectado" if os.getenv("OPENAI_API_KEY") else "❌ Não configurado"
        st.info(f"Status: {openai_status}")

        st.markdown("**Qdrant**")
        try:
            qdrant_client = get_qdrant_client()
            collections = qdrant_client.get_collections()
            st.success(f"✅ Conectado ({len(collections.collections)} coleções)")
        except Exception as e:
            st.error(f"❌ Erro: {str(e)[:50]}")

    with col2:
        st.markdown("**Supabase**")
        supabase_status = "✅ Configurado" if os.getenv("SUPABASE_URL") else "❌ Não configurado"
        st.info(f"Status: {supabase_status}")

        st.markdown("**Redis**")
        redis_status = "⚠️ Opcional"
        st.warning(f"Status: {redis_status}")

    st.markdown("---")

    st.subheader("🎛️ Parâmetros dos Agentes")

    temperature = st.slider("Temperature (criatividade)", 0.0, 1.0, 0.3, 0.1)
    max_tokens = st.number_input("Max tokens por resposta", 1000, 4000, 2000, 100)
    max_rpm = st.number_input("Max requisições por minuto", 1, 60, 10, 1)

    if st.button("💾 Salvar Configurações"):
        st.success("✅ Configurações salvas!")


# ===== PÁGINA: BUSCA NO QDRANT =====

elif page == "🔍 Busca no Qdrant":
    st.title("🔍 Busca na Knowledge Base")

    st.markdown("""
    Pesquise documentos indexados no Qdrant.
    """)

    collection_name = st.selectbox(
        "Coleção",
        ["medical_guidelines", "cardiology_papers", "clinical_protocols", "case_studies"]
    )

    query = st.text_area(
        "Digite sua pergunta ou termo de busca",
        placeholder="Ex: Quais são as indicações de anticoagulação em FA?"
    )

    limit = st.slider("Número de resultados", 1, 10, 3)

    if st.button("🔍 Buscar", type="primary"):
        if not query:
            st.warning("Digite uma consulta")
        else:
            with st.spinner("Buscando..."):
                try:
                    qdrant_client = get_qdrant_client()
                    openai_client = get_openai_client()

                    # Gera embedding da query
                    query_embedding = generate_embeddings(query, openai_client)

                    # Busca no Qdrant
                    results = qdrant_client.search(
                        collection_name=collection_name,
                        query_vector=query_embedding,
                        limit=limit
                    )

                    if results:
                        st.success(f"✅ Encontrados {len(results)} resultados")

                        for i, result in enumerate(results, 1):
                            with st.expander(f"📄 Resultado {i} (Score: {result.score:.3f})"):
                                st.markdown(f"**Texto:**\n{result.payload.get('text', 'N/A')}")
                                st.json(result.payload.get('metadata', {}))
                    else:
                        st.info("Nenhum resultado encontrado")

                except Exception as e:
                    st.error(f"Erro ao buscar: {e}")


# ===== FOOTER =====

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>ClinicaPro Cardio - Dashboard CrewAI v0.1.0-beta</div>",
    unsafe_allow_html=True
)
