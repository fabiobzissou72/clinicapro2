# 🏥 ClinicaPro Cardio - Sistema IA para Análise Cardiológica

Sistema de inteligência artificial multi-agente para apoio à decisão clínica em cardiologia, com integração via Telegram Bot e API REST.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Visão Geral

ClinicaPro Cardio utiliza **CrewAI** para simular uma equipe de cardiologistas especializados que analisam casos clínicos e fornecem recomendações baseadas em guidelines internacionais.

### Agentes Especializados

- 🎯 **Coordenador Cardiológico**: Triagem e coordenação
- ❤️ **Especialista Coronariano**: Doença arterial coronariana, IAM, angina
- 💊 **Especialista em IC**: Insuficiência cardíaca aguda e crônica
- ⚡ **Especialista em Arritmias**: FA, flutter, bloqueios, marca-passo

## 🚀 Início Rápido

### 1. Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- OpenAI API Key

### 2. Instalação

```bash
# Clone ou crie o projeto
cd CLINIAPRO

# Crie ambiente virtual
python -m venv venv

# Ative o ambiente
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

### 3. Configuração

Edite o arquivo `.env` (já criado) e verifique as variáveis:

```env
OPENAI_API_KEY=sua-chave-aqui
TELEGRAM_BOT_TOKEN=seu-token-aqui
SUPABASE_URL=sua-url-aqui
# ... outras configurações
```

### 4. Inicie os Serviços

```bash
# Inicia Qdrant e Redis
docker-compose up -d

# Verifica se subiram
docker-compose ps
```

### 5. Configure o Supabase

1. Acesse seu projeto Supabase
2. Vá em **SQL Editor**
3. Execute o script: `scripts/setup_supabase_tables.sql`
4. Verifique em **Table Editor** se as tabelas foram criadas

## 🧪 Testes

### Teste do Crew (Recomendado primeiro)

```bash
python tests/test_cardio_crew.py
```

Escolha um dos casos de teste:
1. IAM (Infarto Agudo do Miocárdio)
2. IC (Insuficiência Cardíaca)
3. FA (Fibrilação Atrial)
4. Todos

### Teste da API

```bash
# Terminal 1: Inicia API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Teste com curl
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "transcription": "Paciente masculino, 58 anos, dor torácica em aperto há 2 horas, irradiando para braço esquerdo. PA: 160x100 mmHg, FC: 95 bpm.",
    "doctor_name": "Dr. Teste"
  }'
```

### Acesse a Documentação Interativa

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📱 Telegram Bot

### Iniciar Bot

```bash
python app/telegram_bot.py
```

### Usar no Telegram

1. Abra: http://t.me/ClinicaPro_Bot
2. Envie `/start`
3. Envie transcrição da consulta como texto
4. Aguarde análise (30-60 segundos)

## 📁 Estrutura do Projeto

```
CLINIAPRO/
├── app/
│   ├── agents/              # Agentes CrewAI
│   │   ├── coordinator.py
│   │   ├── coronary_specialist.py
│   │   ├── heart_failure_specialist.py
│   │   └── arrhythmia_specialist.py
│   ├── crews/               # Orquestração
│   │   └── cardio_crew.py
│   ├── database/            # Supabase models
│   │   └── models.py
│   ├── tools/               # Ferramentas (RAG, etc)
│   ├── main.py              # FastAPI
│   └── telegram_bot.py      # Bot Telegram
├── scripts/
│   └── setup_supabase_tables.sql
├── tests/
│   └── test_cardio_crew.py
├── .env                     # Variáveis de ambiente
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔧 Comandos Úteis

### Docker

```bash
# Iniciar serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down

# Resetar tudo
docker-compose down -v  # Remove volumes também
```

### Python

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar nova dependência
pip install nome-do-pacote
pip freeze > requirements.txt

# Rodar formatação
black app/
```

### API

```bash
# Desenvolvimento (com reload)
uvicorn app.main:app --reload

# Produção
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📊 Exemplos de Uso

### Via Python (direto)

```python
import asyncio
from app.crews.cardio_crew import analyze_cardio_case

async def main():
    result = await analyze_cardio_case(
        transcription="Paciente com dor torácica...",
        doctor_name="Dr. João Silva",
        case_id="CASE-001"
    )
    print(result["analysis"])

asyncio.run(main())
```

### Via API (HTTP)

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/analyze",
        json={
            "transcription": "Paciente com dor torácica...",
            "doctor_name": "Dr. João Silva"
        },
        timeout=120.0
    )
    result = response.json()
    print(result["analysis"])
```

## 🔐 Segurança

- ✅ Credenciais em variáveis de ambiente (`.env`)
- ✅ `.env` no `.gitignore` (nunca commitado)
- ✅ Supabase com Row Level Security (RLS)
- ✅ HTTPS em produção (configure nginx/reverse proxy)
- ⚠️ **IMPORTANTE**: Nunca exponha API keys no código

## 📚 Guidelines Utilizadas

Os agentes são treinados para seguir:

- ACC/AHA (American College of Cardiology / American Heart Association)
- ESC (European Society of Cardiology)
- SBC (Sociedade Brasileira de Cardiologia)
- Trials recentes: DAPA-HF, EMPEROR, PARADIGM-HF, etc.

## ⚠️ Disclaimer

**Este é um sistema de apoio à decisão clínica.**

- NÃO substitui avaliação médica presencial
- NÃO faz diagnósticos definitivos
- Decisão final é sempre do médico assistente
- Deve ser usado como ferramenta complementar

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'crewai'"

```bash
pip install crewai crewai-tools
```

### Erro: "OpenAI API key not found"

Verifique o `.env`:
```bash
cat .env | grep OPENAI_API_KEY
```

### Erro: "Docker não conecta"

```bash
docker-compose down
docker-compose up -d
docker-compose ps
```

### Análise muito lenta

- Verifique rate limit da OpenAI
- Considere usar modelo mais rápido (gpt-3.5-turbo)
- Ajuste `CREWAI_MAX_RPM` no `.env`

## 📈 Próximos Passos

- [ ] Implementar RAG com Qdrant (busca em guidelines)
- [ ] Adicionar transcrição de áudio (Whisper)
- [ ] Criar dashboard de analytics
- [ ] Implementar cache Redis para respostas
- [ ] Adicionar mais especialistas (valvulopatias, etc.)
- [ ] Exportar relatórios em PDF

## 📞 Suporte

Para dúvidas ou problemas:
- Crie uma issue no repositório
- Contate o desenvolvedor

## 📄 Licença

Uso interno - ClinicaPro

---

**Desenvolvido com ❤️ para cardiologistas**

*Powered by CrewAI + GPT-4o-mini*
