# 🏥 ClinicaPro Cardio - Novos Recursos Implementados

## ✨ Resumo das Implementações

### 1. 🔐 Sistema de Autenticação JWT para Médicos

**Arquivos criados:**
- `app/auth.py` - Sistema completo de autenticação e autorização
- `app/api_auth.py` - Endpoints de login, registro e gestão de perfil
- `database/schema_doctors.sql` - Schema SQL para tabela de médicos

**Funcionalidades:**
- ✅ Registro de médicos com validação de CRM
- ✅ Login com email e senha (hash bcrypt)
- ✅ Tokens JWT com expiração configurável
- ✅ Middleware de autenticação para rotas protegidas
- ✅ Gestão de perfil (visualizar, atualizar, mudar senha)
- ✅ Role-based access control (RBAC)

**Endpoints disponíveis:**
```
POST /api/v1/auth/register - Registrar novo médico
POST /api/v1/auth/login - Fazer login
GET  /api/v1/auth/me - Ver perfil (requer auth)
PUT  /api/v1/auth/me - Atualizar perfil (requer auth)
POST /api/v1/auth/change-password - Mudar senha (requer auth)
```

**Exemplo de uso:**
```bash
# Registrar médico
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. João Silva",
    "crm": "12345-SP",
    "email": "joao@clinica.com",
    "password": "senhaSegura123",
    "specialty": "Cardiologia",
    "phone": "(11) 98765-4321"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@clinica.com",
    "password": "senhaSegura123"
  }'

# Usar token em requisições autenticadas
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

---

### 2. 📊 Dashboard do Médico

**Arquivo criado:**
- `app/api_dashboard.py` - API completa para dashboard

**Funcionalidades:**
- ✅ Estatísticas gerais (total pacientes, consultas, média por dia)
- ✅ Lista de pacientes com busca e paginação
- ✅ Lista de prontuários/análises
- ✅ Visualização detalhada de prontuários
- ✅ Timeline de eventos do paciente
- ✅ Agenda de consultas (estrutura pronta)

**Endpoints disponíveis:**
```
GET /api/v1/dashboard/stats - Estatísticas gerais
GET /api/v1/dashboard/patients - Lista de pacientes
GET /api/v1/dashboard/prontuarios - Lista de prontuários
GET /api/v1/dashboard/prontuarios/{case_id} - Detalhes de prontuário
GET /api/v1/dashboard/agenda - Agenda do médico
GET /api/v1/dashboard/patient/{patient_id}/timeline - Timeline do paciente
```

**Exemplo de uso:**
```bash
# Ver estatísticas
curl -X GET http://localhost:8000/api/v1/dashboard/stats \
  -H "Authorization: Bearer SEU_TOKEN"

# Listar pacientes
curl -X GET http://localhost:8000/api/v1/dashboard/patients?search=João&limit=10 \
  -H "Authorization: Bearer SEU_TOKEN"

# Ver timeline do paciente
curl -X GET http://localhost:8000/api/v1/dashboard/patient/PATIENT_ID/timeline \
  -H "Authorization: Bearer SEU_TOKEN"
```

---

### 3. 🤖 IA Avançada no Telegram

**Arquivos criados/modificados:**
- `app/telegram_ai_service.py` - Serviço de IA avançado
- `app/telegram_bot.py` - Bot atualizado com novos comandos

**Funcionalidades:**
- ✅ Interpretação inteligente de intenções do usuário
- ✅ Criação de prontuários por voz/texto com extração automática de dados
- ✅ Busca de pacientes por nome ou CPF
- ✅ Resumo inteligente de histórico do paciente
- ✅ Sugestões clínicas baseadas em sintomas e histórico
- ✅ Contexto conversacional (bot lembra do estado da conversa)

**Novos comandos do bot:**
```
/paciente [nome ou CPF] - Buscar e ver resumo do paciente
/prontuario - Iniciar criação de prontuário interativo
/sugestao - Obter sugestões clínicas baseadas em IA
```

**Fluxo de uso:**

1. **Buscar paciente:**
   ```
   /paciente João Silva
   ou
   /paciente 123.456.789-00
   ```
   Bot retorna resumo completo do paciente com histórico e risco.

2. **Criar prontuário:**
   ```
   /prontuario
   [Bot pede dados]
   [Enviar áudio ou texto com dados da consulta]
   [Bot cria prontuário automaticamente]
   ```

3. **Sugestões clínicas:**
   ```
   /sugestao
   [Bot pede dados]
   [Enviar sintomas e histórico]
   [Bot gera sugestões diagnósticas e condutas]
   ```

---

### 4. 🎛️ Dashboard Streamlit para CrewAI

**Arquivo criado:**
- `streamlit_crewai_dashboard.py` - Dashboard completo

**Funcionalidades:**
- ✅ Upload de documentos médicos (PDFs) para Qdrant
- ✅ Extração automática de texto e geração de embeddings
- ✅ Indexação em coleções organizadas
- ✅ Monitoramento de agentes CrewAI
- ✅ Visualização de métricas e logs
- ✅ Busca semântica na knowledge base
- ✅ Configurações do sistema

**Como executar:**
```bash
streamlit run streamlit_crewai_dashboard.py
```

**Páginas disponíveis:**

1. **📤 Upload de Documentos**
   - Upload de PDFs (guidelines, artigos, protocolos)
   - Metadados automáticos
   - Divisão em chunks e indexação no Qdrant
   - Suporte a múltiplas coleções

2. **📊 Monitoramento**
   - Status dos 4 agentes CardiologAI
   - Métricas de performance
   - Logs em tempo real
   - Taxa de sucesso

3. **⚙️ Configurações**
   - Status de conexões (OpenAI, Qdrant, Supabase, Redis)
   - Parâmetros dos agentes (temperature, max tokens, RPM)
   - Salvamento de configurações

4. **🔍 Busca no Qdrant**
   - Busca semântica em documentos indexados
   - Seleção de coleção
   - Top-K resultados com score
   - Visualização de metadados

---

## 🗄️ Schema do Banco de Dados

**Executar no Supabase:**

```sql
-- Executar o arquivo database/schema_doctors.sql
```

Isso criará:
- Tabela `doctors` com autenticação
- Índices para performance
- Row Level Security (RLS)
- Triggers para updated_at
- Relação com `case_analyses`

---

## 📦 Instalação e Configuração

### 1. Atualizar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente (.env)

Certifique-se que o `.env` tem:
```env
SECRET_KEY=seu-secret-key-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Criar tabela no Supabase

Execute o SQL em `database/schema_doctors.sql` no SQL Editor do Supabase.

### 4. Iniciar serviços

**API Principal:**
```bash
python -m app.main
# ou
uvicorn app.main:app --reload --port 8000
```

**Bot do Telegram:**
```bash
python -m app.telegram_bot
```

**Dashboard Streamlit:**
```bash
streamlit run streamlit_crewai_dashboard.py
```

---

## 🎯 Casos de Uso

### Caso 1: Médico se registra e faz login

```python
# 1. Registro
POST /api/v1/auth/register
{
  "name": "Dr. Maria Santos",
  "crm": "54321-RJ",
  "email": "maria@hospital.com.br",
  "password": "senhaSegura456",
  "specialty": "Cardiologia",
  "phone": "(21) 99999-8888"
}

# 2. Login
POST /api/v1/auth/login
{
  "email": "maria@hospital.com.br",
  "password": "senhaSegura456"
}

# Resposta:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "doctor": {
    "id": "uuid-here",
    "name": "Dr. Maria Santos",
    "crm": "54321-RJ",
    "email": "maria@hospital.com.br"
  }
}
```

### Caso 2: Médico usa Telegram para criar prontuário

```
Médico: /prontuario

Bot: 📋 CRIAR PRONTUÁRIO
Envie os dados da consulta...

Médico: [Grava áudio]
"Paciente João Silva, 58 anos, hipertenso,
dor torácica há 2 horas, PA 160x100, FC 95..."

Bot: 🎤 Processando áudio...
     ✅ Transcrição concluída!
     🤖 Analisando com especialistas...
     ✅ Prontuário criado!

[Bot envia análise SOAP completa com diagnóstico e conduta]
```

### Caso 3: Médico busca paciente

```
Médico: /paciente 123.456.789-00

Bot: 🔍 Buscando paciente...

📋 RESUMO DO PACIENTE

**Identificação:** João Silva, 58 anos, masculino
**Perfil de Risco:** Alto - HAS, tabagista, histórico familiar
**Histórico Relevante:**
- Hipertensão há 10 anos
- Diabetes Mellitus tipo 2
- Sem alergias conhecidas
**Acompanhamento:** 12 consultas, última em 25/12/2025
```

### Caso 4: Gestor faz upload de guideline no Streamlit

1. Acessa dashboard: `http://localhost:8501`
2. Vai em "📤 Upload de Documentos"
3. Seleciona coleção: "medical_guidelines"
4. Faz upload do PDF: "ESC_Guidelines_2024.pdf"
5. Preenche metadados:
   - Título: "ESC Guidelines for Acute Coronary Syndromes 2024"
   - Autor: "European Society of Cardiology"
   - Ano: 2024
   - Tipo: Guideline
   - Tags: "acs, infarto, cardiologia"
6. Clica em "🚀 Processar e Upload"
7. Sistema extrai texto, gera embeddings e indexa no Qdrant
8. Agentes CrewAI agora podem consultar esse guideline

---

## 🔒 Segurança

### Implementações de Segurança

1. **Senhas:**
   - Hash bcrypt (trabalho factor alto)
   - Nunca retorna password_hash nas respostas

2. **Tokens JWT:**
   - Assinados com SECRET_KEY
   - Expiração configurável (padrão: 30 min)
   - Incluem apenas dados não-sensíveis

3. **Row Level Security (RLS):**
   - Médicos só veem seus próprios dados
   - Service role tem acesso total (apenas backend)

4. **HTTPS:**
   - Recomendado em produção
   - Configure certificado SSL no Nginx/Caddy

5. **Rate Limiting:**
   - Configurar no nginx ou usar FastAPI limiter
   - Protege contra brute force

---

## 📊 Métricas e Monitoramento

O dashboard Streamlit fornece:

- **Total de análises:** Contador de casos processados
- **Agentes ativos:** Status de cada agente
- **Docs no Qdrant:** Quantidade de documentos indexados
- **Response time:** Tempo médio de resposta
- **Taxa de sucesso:** % de análises bem-sucedidas
- **Logs:** Histórico de eventos e erros

---

## 🚀 Próximos Passos Sugeridos

1. **Frontend Web:**
   - Criar dashboard web React/Vue para médicos
   - Integrar com API de autenticação e dashboard

2. **Agenda Completa:**
   - Implementar tabela `appointments` no Supabase
   - Endpoints CRUD de agendamentos
   - Notificações por Telegram

3. **Analytics Avançados:**
   - Gráficos de diagnósticos mais comuns
   - Mapas de calor de sintomas
   - Predição de risco com ML

4. **Integrações:**
   - Integrar com sistemas hospitalares (HL7/FHIR)
   - Export para PDF/Word
   - Assinatura digital de prontuários

5. **IA Avançada:**
   - Fine-tuning de modelo específico para cardiologia
   - RAG (Retrieval Augmented Generation) com Qdrant
   - Multi-modal: imagens + texto + áudio

---

## 📞 Suporte

Para dúvidas ou problemas:
- Verificar logs em `clinicapro_cardio.log`
- Consultar documentação da API: `http://localhost:8000/docs`
- Testar endpoints no Swagger UI

---

## 📝 Changelog

### v0.2.0-beta (2025-12-30)

**Adicionado:**
- ✅ Sistema completo de autenticação JWT
- ✅ Dashboard API para médicos (pacientes, prontuários, analytics, agenda)
- ✅ IA avançada no Telegram com novos comandos (/paciente, /prontuario, /sugestao)
- ✅ Serviço de IA para interpretação de intenções e sugestões clínicas
- ✅ Dashboard Streamlit para gerenciar CrewAI
- ✅ Upload de documentos para Qdrant com embeddings
- ✅ Busca semântica na knowledge base
- ✅ Monitoramento de agentes e métricas

**Melhorado:**
- Bot do Telegram agora é conversacional e inteligente
- Prontuários podem ser criados por voz, texto ou imagem
- Sistema busca e resume pacientes automaticamente

---

## 🏆 Tecnologias Utilizadas

- **Backend:** FastAPI, Python 3.13
- **Autenticação:** JWT, bcrypt, python-jose
- **Database:** Supabase (PostgreSQL)
- **Vector DB:** Qdrant
- **LLM:** OpenAI GPT-4o-mini
- **Embeddings:** OpenAI text-embedding-3-small
- **Bot:** python-telegram-bot
- **Dashboard:** Streamlit
- **AI Framework:** CrewAI

---

Desenvolvido com ❤️ para revolucionar o atendimento cardiológico.
