# Guia de Deployment - ClinicaPro Cardio VPS

## Visão Geral

Sistema completo de apoio à decisão cardiológica com IA multi-agente (CrewAI).

**Componentes:**
- API FastAPI (porta 8000)
- Bot Telegram
- Dashboard Médico (Streamlit - porta 8501)
- Dashboard CrewAI (Streamlit - porta 8502)

---

## 1. Preparação do Servidor VPS

### Requisitos Mínimos
- Ubuntu 20.04+ / Debian 11+
- 4GB RAM (recomendado 8GB)
- 2 vCPUs
- 20GB disco
- Python 3.10+
- FFmpeg (para processamento de áudio)

### 1.1. Atualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2. Instalar Dependências do Sistema
```bash
# Python e ferramentas
sudo apt install -y python3.11 python3.11-venv python3-pip

# FFmpeg (para Whisper)
sudo apt install -y ffmpeg

# Git
sudo apt install -y git

# Supervisor (para gerenciar processos)
sudo apt install -y supervisor

# Nginx (proxy reverso)
sudo apt install -y nginx

# Certbot (SSL/HTTPS)
sudo apt install -y certbot python3-certbot-nginx
```

---

## 2. Configuração do Projeto

### 2.1. Clonar Repositório (ou upload via FTP)
```bash
cd /var/www
sudo mkdir clinicapro
sudo chown $USER:$USER clinicapro
cd clinicapro

# Se usar git
git clone <seu-repositorio> .

# OU upload manual via FTP/SCP para /var/www/clinicapro
```

### 2.2. Criar Ambiente Virtual
```bash
cd /var/www/clinicapro
python3.11 -m venv venv
source venv/bin/activate
```

### 2.3. Instalar Dependências Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Pacotes principais instalados:**
- fastapi>=0.115.6
- uvicorn[standard]>=0.34.0
- python-dotenv>=1.0.1
- crewai>=1.7.2
- crewai-tools>=0.18.0
- openai>=1.59.5
- langchain>=0.3.14
- langchain-openai>=0.2.14
- python-telegram-bot>=21.10
- openai-whisper>=20240930
- supabase>=2.10.0
- qdrant-client>=1.12.1
- redis>=5.2.1
- streamlit>=1.40.0
- plotly>=5.24.0
- python-jose[cryptography]>=3.3.0
- passlib[bcrypt]>=1.7.4
- httpx>=0.28.1
- bcrypt<5.0.0  # IMPORTANTE: versão específica para compatibilidade

### 2.4. Configurar Variáveis de Ambiente
```bash
# Copiar exemplo
cp .env.example .env

# Editar com suas credenciais
nano .env
```

**Variáveis críticas no .env:**
```bash
# OpenAI API
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# Telegram Bot
TELEGRAM_BOT_TOKEN=123456789:AAG...
TELEGRAM_WEBAPP_URL=https://seu-dominio.com
TELEGRAM_BOT_USERNAME=SeuBot

# Supabase Database
SUPABASE_URL=https://...supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Qdrant Vector Database
QDRANT_URL=https://qdrant.seu-dominio.com
QDRANT_API_KEY=...

# Redis Cache (opcional)
REDIS_URL=redis://localhost:6379

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT=8000
API_VERSION=v1
DOMAIN=seu-dominio.com

# Security
SECRET_KEY=gere-uma-chave-segura-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CrewAI
CREWAI_TELEMETRY_ENABLED=false
CREWAI_MAX_RPM=10
CREWAI_VERBOSE=false
```

---

## 3. Configurar Serviços com Supervisor

Supervisor gerencia processos Python, mantendo-os rodando 24/7 e reiniciando automaticamente em caso de falha.

### 3.1. API FastAPI
```bash
sudo nano /etc/supervisor/conf.d/clinicapro-api.conf
```

```ini
[program:clinicapro-api]
command=/var/www/clinicapro/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/var/www/clinicapro
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/clinicapro/api.err.log
stdout_logfile=/var/log/clinicapro/api.out.log
environment=PATH="/var/www/clinicapro/venv/bin"
```

### 3.2. Bot Telegram
```bash
sudo nano /etc/supervisor/conf.d/clinicapro-bot.conf
```

```ini
[program:clinicapro-bot]
command=/var/www/clinicapro/venv/bin/python -m app.telegram_bot
directory=/var/www/clinicapro
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/clinicapro/bot.err.log
stdout_logfile=/var/log/clinicapro/bot.out.log
environment=PATH="/var/www/clinicapro/venv/bin"
```

### 3.3. Dashboard Médico (Streamlit)
```bash
sudo nano /etc/supervisor/conf.d/clinicapro-dashboard-medico.conf
```

```ini
[program:clinicapro-dashboard-medico]
command=/var/www/clinicapro/venv/bin/streamlit run streamlit_dashboard_medico.py --server.port 8501 --server.headless true
directory=/var/www/clinicapro
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/clinicapro/dashboard-medico.err.log
stdout_logfile=/var/log/clinicapro/dashboard-medico.out.log
environment=PATH="/var/www/clinicapro/venv/bin"
```

### 3.4. Dashboard CrewAI (Streamlit)
```bash
sudo nano /etc/supervisor/conf.d/clinicapro-dashboard-crewai.conf
```

```ini
[program:clinicapro-dashboard-crewai]
command=/var/www/clinicapro/venv/bin/streamlit run streamlit_crewai_dashboard.py --server.port 8502 --server.headless true
directory=/var/www/clinicapro
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/clinicapro/dashboard-crewai.err.log
stdout_logfile=/var/log/clinicapro/dashboard-crewai.out.log
environment=PATH="/var/www/clinicapro/venv/bin"
```

### 3.5. Criar diretório de logs
```bash
sudo mkdir -p /var/log/clinicapro
sudo chown www-data:www-data /var/log/clinicapro
```

### 3.6. Recarregar Supervisor
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### 3.7. Verificar Status
```bash
sudo supervisorctl status
```

**Saída esperada:**
```
clinicapro-api               RUNNING   pid 1234, uptime 0:00:10
clinicapro-bot               RUNNING   pid 1235, uptime 0:00:10
clinicapro-dashboard-crewai  RUNNING   pid 1236, uptime 0:00:10
clinicapro-dashboard-medico  RUNNING   pid 1237, uptime 0:00:10
```

---

## 4. Configurar Nginx (Proxy Reverso)

### 4.1. Configuração Principal
```bash
sudo nano /etc/nginx/sites-available/clinicapro
```

```nginx
# API FastAPI
server {
    listen 80;
    server_name api.seu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Dashboard Médico
server {
    listen 80;
    server_name medico.seu-dominio.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Streamlit websocket
        proxy_read_timeout 86400;
    }
}

# Dashboard CrewAI
server {
    listen 80;
    server_name crew.seu-dominio.com;

    location / {
        proxy_pass http://localhost:8502;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Streamlit websocket
        proxy_read_timeout 86400;
    }
}
```

### 4.2. Ativar Configuração
```bash
sudo ln -s /etc/nginx/sites-available/clinicapro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 5. Configurar SSL/HTTPS (Certbot)

```bash
# API
sudo certbot --nginx -d api.seu-dominio.com

# Dashboard Médico
sudo certbot --nginx -d medico.seu-dominio.com

# Dashboard CrewAI
sudo certbot --nginx -d crew.seu-dominio.com
```

**Renovação automática:**
```bash
sudo certbot renew --dry-run
```

---

## 6. Firewall (UFW)

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

---

## 7. Monitoramento e Logs

### Ver logs em tempo real
```bash
# API
sudo tail -f /var/log/clinicapro/api.out.log

# Bot
sudo tail -f /var/log/clinicapro/bot.out.log

# Dashboard Médico
sudo tail -f /var/log/clinicapro/dashboard-medico.out.log

# Dashboard CrewAI
sudo tail -f /var/log/clinicapro/dashboard-crewai.out.log

# Erros
sudo tail -f /var/log/clinicapro/*.err.log
```

### Gerenciar processos
```bash
# Reiniciar API
sudo supervisorctl restart clinicapro-api

# Parar Bot
sudo supervisorctl stop clinicapro-bot

# Ver status
sudo supervisorctl status

# Reiniciar tudo
sudo supervisorctl restart all
```

---

## 8. Backup e Manutenção

### 8.1. Backup do .env
```bash
sudo cp /var/www/clinicapro/.env /var/backups/clinicapro-env-$(date +%Y%m%d).bak
```

### 8.2. Backup do código
```bash
sudo tar -czf /var/backups/clinicapro-$(date +%Y%m%d).tar.gz /var/www/clinicapro
```

### 8.3. Atualizar aplicação
```bash
cd /var/www/clinicapro
source venv/bin/activate

# Pull changes (se usando git)
git pull

# Atualizar dependências
pip install -r requirements.txt --upgrade

# Reiniciar serviços
sudo supervisorctl restart all
```

---

## 9. Troubleshooting

### Serviço não inicia
```bash
# Ver logs de erro
sudo supervisorctl tail -f clinicapro-api stderr

# Verificar permissões
sudo chown -R www-data:www-data /var/www/clinicapro

# Verificar .env
cat /var/www/clinicapro/.env
```

### API não responde
```bash
# Verificar se porta está aberta
sudo netstat -tulpn | grep 8000

# Testar localmente
curl http://localhost:8000/docs

# Verificar logs do Nginx
sudo tail -f /var/log/nginx/error.log
```

### Bot não recebe mensagens
```bash
# Verificar logs
sudo tail -f /var/log/clinicapro/bot.out.log

# Testar conexão Telegram API
curl https://api.telegram.org/bot<SEU_TOKEN>/getMe
```

---

## 10. URLs Finais

Após deployment completo:

- **API Docs**: https://api.seu-dominio.com/docs
- **Dashboard Médico**: https://medico.seu-dominio.com
- **Dashboard CrewAI**: https://crew.seu-dominio.com
- **Telegram Bot**: @SeuBot (procurar no Telegram)

---

## 11. Checklist de Deployment

- [ ] Servidor VPS configurado (Ubuntu/Debian)
- [ ] Python 3.11+ instalado
- [ ] FFmpeg instalado
- [ ] Código enviado para `/var/www/clinicapro`
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas (`requirements.txt`)
- [ ] Arquivo `.env` configurado com credenciais corretas
- [ ] Supervisor configurado (4 serviços)
- [ ] Logs criados em `/var/log/clinicapro`
- [ ] Nginx configurado (proxy reverso)
- [ ] DNS apontando para VPS:
  - [ ] api.seu-dominio.com
  - [ ] medico.seu-dominio.com
  - [ ] crew.seu-dominio.com
- [ ] SSL/HTTPS configurado (Certbot)
- [ ] Firewall ativado (UFW)
- [ ] Todos os serviços rodando:
  - [ ] `clinicapro-api` (RUNNING)
  - [ ] `clinicapro-bot` (RUNNING)
  - [ ] `clinicapro-dashboard-medico` (RUNNING)
  - [ ] `clinicapro-dashboard-crewai` (RUNNING)
- [ ] URLs funcionando:
  - [ ] https://api.seu-dominio.com/docs
  - [ ] https://medico.seu-dominio.com
  - [ ] https://crew.seu-dominio.com
- [ ] Bot respondendo no Telegram

---

## 12. Comandos Rápidos

```bash
# Ver status de tudo
sudo supervisorctl status

# Reiniciar tudo
sudo supervisorctl restart all

# Ver logs da API
sudo tail -f /var/log/clinicapro/api.out.log

# Ver logs do Bot
sudo tail -f /var/log/clinicapro/bot.out.log

# Testar API localmente
curl http://localhost:8000/docs

# Recarregar Nginx
sudo systemctl reload nginx

# Ver processos Python
ps aux | grep python
```

---

**Autor:** ClinicaPro Development Team
**Data:** 2025-12-30
**Versão:** 1.0
