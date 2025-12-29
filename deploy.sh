#!/bin/bash
# ===== CLINICAPRO - DEPLOY AUTOMÁTICO PARA SWARM =====
# Executa: bash deploy.sh

set -e  # Para no primeiro erro

echo "🚀 ClinicaPro - Deploy Automático"
echo "=================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ===== PASSO 1: GIT PUSH (LOCAL) =====
echo -e "${YELLOW}📤 Passo 1: Git Push...${NC}"

# Verifica se está no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Erro: Execute no diretório D:\CLINIAPRO${NC}"
    exit 1
fi

# Git commands
git add .
git commit -m "feat: Docker + Emergency protocols + Security fixes

- Add Dockerfile with FFmpeg
- Add docker-compose.yml for local dev
- Add clinicapro.yaml for Swarm production
- Remove hardcoded API keys (security)
- Add emergency protocols (hypertensive crisis, ACS)
- Fix date display in reports
- Add comprehensive documentation
- Update .gitignore for security
" || echo "Nada novo para commitar"

git push -u origin main || git push origin main

echo -e "${GREEN}✅ Git push concluído!${NC}"
echo ""

# ===== PASSO 2: SOLICITA DADOS DA VPS =====
echo -e "${YELLOW}📋 Passo 2: Configuração da VPS${NC}"

read -p "IP ou hostname da VPS (ex: Fbzia): " VPS_HOST
read -p "Usuário SSH (padrão: root): " VPS_USER
VPS_USER=${VPS_USER:-root}

read -p "Porta SSH (padrão: 22): " VPS_PORT
VPS_PORT=${VPS_PORT:-22}

echo ""
echo -e "${YELLOW}🔐 Passo 3: Variáveis de Ambiente${NC}"
echo "Digite suas chaves de API:"

read -p "OPENAI_API_KEY: " OPENAI_KEY
read -p "TELEGRAM_BOT_TOKEN: " TELEGRAM_TOKEN
read -p "REDIS_PASSWORD (opcional, Enter para padrão): " REDIS_PASS
REDIS_PASS=${REDIS_PASS:-clinicapro_redis_2025}

echo ""
echo -e "${YELLOW}🚢 Passo 4: Deploy no Swarm...${NC}"

# Cria arquivo .env temporário
cat > /tmp/clinicapro.env << EOF
OPENAI_API_KEY=$OPENAI_KEY
TELEGRAM_BOT_TOKEN=$TELEGRAM_TOKEN
REDIS_PASSWORD=$REDIS_PASS
EOF

# ===== PASSO 5: DEPLOY VIA SSH =====
echo "Conectando ao servidor..."

ssh -p $VPS_PORT $VPS_USER@$VPS_HOST << 'ENDSSH'
set -e

echo ""
echo "📦 No servidor: Preparando deploy..."

# Remove instalação antiga se existir
if [ -d "/root/clinicapro2" ]; then
    echo "⚠️  Removendo instalação antiga..."
    rm -rf /root/clinicapro2
fi

# Clone o repositório
echo "📥 Clonando repositório..."
cd /root
git clone https://github.com/fabiobzissou72/clinicapro2.git
cd clinicapro2

echo "✅ Repositório clonado"
ENDSSH

# Copia .env para o servidor
echo "📤 Copiando variáveis de ambiente..."
scp -P $VPS_PORT /tmp/clinicapro.env $VPS_USER@$VPS_HOST:/root/clinicapro2/.env

# Limpa .env local
rm /tmp/clinicapro.env

# Continua deploy
ssh -p $VPS_PORT $VPS_USER@$VPS_HOST << 'ENDSSH'
set -e

cd /root/clinicapro2

echo ""
echo "🏗️  Buildando imagem Docker..."
docker build -t clinicapro:latest . || {
    echo "❌ Erro no build. Verifique Dockerfile"
    exit 1
}

echo ""
echo "🚀 Fazendo deploy da stack..."

# Remove stack antiga se existir
if docker stack ls | grep -q clinicapro; then
    echo "⚠️  Removendo stack antiga..."
    docker stack rm clinicapro
    echo "⏳ Aguardando remoção completa..."
    sleep 10
fi

# Deploy da nova stack
docker stack deploy -c clinicapro.yaml clinicapro

echo ""
echo "✅ Stack deployada!"
echo ""
echo "📊 Status dos serviços:"
docker stack ps clinicapro --format "table {{.Name}}\t{{.CurrentState}}\t{{.Error}}"

echo ""
echo "⏳ Aguardando serviços iniciarem (30s)..."
sleep 30

echo ""
echo "📋 Logs da API (últimas 20 linhas):"
docker service logs --tail 20 clinicapro_api || echo "API ainda não iniciou"

echo ""
echo "📋 Logs do Bot (últimas 20 linhas):"
docker service logs --tail 20 clinicapro_bot || echo "Bot ainda não iniciou"

ENDSSH

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ DEPLOY CONCLUÍDO COM SUCESSO!     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "🔍 Verificação:"
echo "  docker stack ps clinicapro"
echo "  docker service logs -f clinicapro_bot"
echo "  docker service logs -f clinicapro_api"
echo ""
echo "🌐 Endpoints (se Traefik configurado):"
echo "  https://api.clinicapro.seudominio.com/health"
echo ""
echo "📱 Telegram Bot:"
echo "  Envie /start para seu bot"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE: Salve suas API keys em local seguro!${NC}"
echo ""
