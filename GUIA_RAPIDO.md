# 🚀 GUIA RÁPIDO - ClinicaPro Cardio

## ⚡ Setup em 5 Minutos

### 1. Instale Dependências

```bash
# Ative ambiente virtual
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Instale tudo
pip install -r requirements.txt
```

### 2. Configure .env

Abra `.env` e verifique se está tudo configurado:
- ✅ `OPENAI_API_KEY` - Sua chave da OpenAI
- ✅ `TELEGRAM_BOT_TOKEN` - Token do bot
- ✅ `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`

### 3. Inicie Docker

```bash
docker-compose up -d
```

### 4. Configure Supabase

1. Acesse: https://supabase.com
2. Abra seu projeto
3. Vá em **SQL Editor**
4. Cole e execute: `scripts/setup_supabase_tables.sql`

### 5. TESTE!

```bash
python tests/test_cardio_crew.py
```

Escolha opção **1** (IAM) e aguarde ~60 segundos.

Se ver análise SOAP formatada: **✅ FUNCIONOU!**

---

## 📖 Uso Diário

### Opção 1: Via Telegram Bot

```bash
# Terminal 1: API
uvicorn app.main:app --reload

# Terminal 2: Bot
python app/telegram_bot.py
```

Depois:
1. Abra Telegram
2. Busque: `@ClinicaPro_Bot`
3. Envie `/start`
4. Envie texto da consulta

### Opção 2: Via API Direta

```bash
# Inicie API
uvicorn app.main:app --reload

# Acesse documentação interativa
# http://localhost:8000/docs
```

Use a interface Swagger para testar!

### Opção 3: Via Python

```python
import asyncio
from app.crews.cardio_crew import analyze_cardio_case

async def main():
    result = await analyze_cardio_case(
        transcription="""
        Paciente masculino, 58 anos, dor torácica há 2h,
        PA 160x100, FC 95bpm
        """,
        doctor_name="Dr. João Silva"
    )
    print(result["analysis"])

asyncio.run(main())
```

---

## 🐛 Problemas Comuns

### "ModuleNotFoundError: crewai"
```bash
pip install crewai crewai-tools
```

### "OpenAI API key not found"
Edite `.env` e adicione sua chave:
```env
OPENAI_API_KEY=sk-proj-SUA-CHAVE-AQUI
```

### Docker não inicia
```bash
docker-compose down
docker-compose up -d
```

### Análise muito lenta (>2 min)
- OpenAI pode estar com rate limit
- Verifique sua conta OpenAI
- Tente usar `gpt-3.5-turbo` no `.env`

---

## 📊 Estrutura de Resposta

O sistema retorna análise SOAP:

```
📋 SUBJETIVO
- Resumo da queixa

🔍 OBJETIVO
- Dados vitais
- Exame físico

🧠 AVALIAÇÃO
- Diagnóstico principal
- Diferenciais
- Fundamentação (guidelines)

📝 PLANO
1. Exames complementares
2. Conduta terapêutica
3. Critérios internação
4. Red flags

📚 REFERÊNCIAS
- Guidelines citadas
```

---

## 💡 Dicas Pro

### 1. Melhore a Transcrição

Inclua sempre:
- ✅ Queixa principal
- ✅ Dados vitais (PA, FC, etc.)
- ✅ Comorbidades
- ✅ Medicações em uso
- ✅ Exame físico relevante

### 2. Customize os Agentes

Edite `app/agents/*.py` para ajustar:
- `temperature`: 0.1-0.3 (mais conservador)
- `backstory`: Adicione expertise específica
- `model`: Use `gpt-4o` para melhor qualidade

### 3. Use Cache Redis

TODO: Implementar cache de respostas similares

### 4. Ative RAG com Qdrant

TODO: Indexar PDFs de guidelines

---

## 🎯 Casos de Uso

### Emergência (IAM, dissecção aórtica)
✅ Sistema identifica urgência
✅ Sugere exames imediatos
✅ Cita guidelines de SCA

### Ambulatório (IC crônica, FA)
✅ Analisa farmacoterapia atual
✅ Sugere otimização (4 pilares)
✅ Indica seguimento

### Dúvidas (casos atípicos)
✅ Lista diferenciais
✅ Sugere propedêutica
✅ Referências baseadas em evidência

---

## 📞 Suporte

- Documentação completa: `README.md`
- Logs: `clinicapro_cardio.log`
- Issues: Crie no repositório

---

**Desenvolvido para cardiologistas 🏥**
