# 🐳 CLINICAPRO - SETUP DOCKER

Guia completo para rodar o ClinicaPro usando Docker.

---

## 📋 PRÉ-REQUISITOS

1. **Docker Desktop** instalado
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - Verifique: `docker --version`

2. **Chaves de API**:
   - OpenAI API Key: https://platform.openai.com/api-keys
   - Telegram Bot Token: Fale com @BotFather no Telegram

---

## 🚀 INSTALAÇÃO RÁPIDA

### Passo 1: Configure as Variáveis de Ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o .env e adicione suas chaves:
# - OPENAI_API_KEY=sk-proj-...
# - TELEGRAM_BOT_TOKEN=1234567890:ABCDEF...
```

### Passo 2: Inicie os Containers

```bash
# Builda e inicia todos os serviços
docker-compose up -d

# Primeira vez pode demorar 2-3 minutos (download de imagens)
```

### Passo 3: Verifique se Está Funcionando

```bash
# Veja os logs em tempo real
docker-compose logs -f

# Você deve ver:
# ✅ clinicapro_api    | Application startup complete
# ✅ clinicapro_bot    | Bot rodando!
# ✅ clinicapro_qdrant | Qdrant started
# ✅ clinicapro_redis  | Ready to accept connections
```

### Passo 4: Teste o Sistema

**Teste a API:**
```bash
# No navegador ou curl:
curl http://localhost:8000/health
# Deve retornar: {"status":"ok"}
```

**Teste o Bot:**
- Abra o Telegram
- Procure seu bot
- Envie `/start`
- Deve receber a mensagem de boas-vindas

---

## 📦 SERVIÇOS INCLUÍDOS

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| **API** | 8000 | FastAPI backend + análise IA |
| **Bot** | - | Telegram bot (polling) |
| **Qdrant** | 6333 | Vector database (RAG) |
| **Redis** | 6379 | Cache & sessions |

---

## 🛠️ COMANDOS ÚTEIS

### Ver Status dos Containers
```bash
docker-compose ps
```

### Ver Logs
```bash
# Todos os serviços
docker-compose logs -f

# Apenas API
docker-compose logs -f api

# Apenas Bot
docker-compose logs -f bot

# Últimas 100 linhas
docker-compose logs --tail=100
```

### Reiniciar Serviços
```bash
# Reinicia tudo
docker-compose restart

# Reinicia apenas o bot
docker-compose restart bot

# Reinicia apenas a API
docker-compose restart api
```

### Parar e Remover Tudo
```bash
# Para os containers (mantém dados)
docker-compose down

# Para e remove TUDO (incluindo volumes/dados)
docker-compose down -v
```

### Rebuildar Após Mudanças no Código
```bash
# Rebuild da imagem
docker-compose build

# Rebuild e reinicia
docker-compose up -d --build
```

### Acessar Shell do Container
```bash
# Entrar no container da API
docker exec -it clinicapro_api bash

# Entrar no container do Bot
docker exec -it clinicapro_bot bash
```

---

## 🐛 TROUBLESHOOTING

### Problema: Bot não responde

**Solução:**
```bash
# Verifique os logs
docker-compose logs bot

# Verifique se o token está correto no .env
cat .env | grep TELEGRAM_BOT_TOKEN

# Reinicie o bot
docker-compose restart bot
```

### Problema: API não sobe

**Solução:**
```bash
# Verifique porta 8000 está livre
netstat -ano | findstr :8000

# Se estiver ocupada, mate o processo:
# Localize o PID e execute:
taskkill /PID <numero_pid> /F

# Reinicie
docker-compose up -d api
```

### Problema: Erro "No space left on device"

**Solução:**
```bash
# Limpa imagens e containers não usados
docker system prune -a

# Remove volumes órfãos
docker volume prune
```

### Problema: Áudio não funciona

**Solução:**
- ✅ FFmpeg já está instalado no container Docker!
- Se persistir, veja logs: `docker-compose logs bot`

### Problema: Data errada nos relatórios

**Solução:**
```bash
# Verifica se código foi atualizado
docker-compose exec api cat app/crews/cardio_crew.py | grep "datetime.now"

# Se não aparecer, rebuild:
docker-compose up -d --build
```

---

## 🔧 DESENVOLVIMENTO

### Hot Reload (Código Atualiza Automaticamente)

Os volumes montados permitem que você edite o código localmente e ele seja atualizado automaticamente no container:

```yaml
volumes:
  - ./app:/app/app  # ← Mudanças em ./app refletem automaticamente
```

**Não precisa rebuildar** para mudanças no código Python!

### Quando Rebuildar?

Rebuild apenas quando mudar:
- `requirements.txt` (novas dependências)
- `Dockerfile`
- Dependências do sistema (FFmpeg, etc)

```bash
docker-compose up -d --build
```

---

## 📊 MONITORAMENTO

### Saúde dos Serviços
```bash
# Verifica health checks
docker-compose ps

# STATUS deve estar "healthy" ou "running"
```

### Uso de Recursos
```bash
# CPU e RAM de cada container
docker stats
```

### Logs Estruturados
```bash
# Salva logs em arquivo
docker-compose logs > logs_$(date +%Y%m%d).txt
```

---

## 🔐 SEGURANÇA

### Remover Chaves Hard-Coded

**IMPORTANTE:** Remova as API keys fixas do código:

```python
# ❌ NÃO FAÇA ISSO:
api_key = "sk-proj-ABC123..."

# ✅ FAÇA ISSO:
import os
api_key = os.getenv("OPENAI_API_KEY")
```

**Arquivos a corrigir:**
- `app/whisper_service.py:26`
- `app/image_analysis_service.py:25`

### Proteja o .env
```bash
# NUNCA commite o .env pro Git!
echo ".env" >> .gitignore
```

---

## 📈 PRODUÇÃO

### Docker Compose para Produção

Crie `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always  # ← Sempre reinicia se cair
    environment:
      - PORT=8000
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  bot:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

**Iniciar produção:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 🆘 SUPORTE

### Logs Completos para Debug
```bash
# Exporta TUDO
docker-compose logs --no-color > debug_full.log
zip debug.zip debug_full.log .env
# Envie debug.zip (REMOVA chaves sensíveis antes!)
```

### Reset Completo
```bash
# Mata tudo e recomeça do zero
docker-compose down -v
docker system prune -a -f
docker-compose up -d --build
```

---

## ✅ CHECKLIST PÓS-INSTALAÇÃO

- [ ] `docker-compose ps` mostra todos "Up" ou "healthy"
- [ ] `curl http://localhost:8000/health` retorna OK
- [ ] Bot responde no Telegram com `/start`
- [ ] Enviar áudio no Telegram funciona (FFmpeg)
- [ ] Data aparece correta nos relatórios (29/12/2025)
- [ ] Protocolos de emergência aparecem nos casos urgentes

---

**Pronto! Seu ClinicaPro está rodando no Docker com FFmpeg incluído! 🎉**
