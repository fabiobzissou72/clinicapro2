# 🐝 CLINICAPRO - DEPLOY NO DOCKER SWARM

Guia para deploy em produção usando Docker Swarm com Traefik.

---

## 📋 PRÉ-REQUISITOS

1. **Docker Swarm** inicializado
   ```bash
   docker swarm init
   ```

2. **Traefik** rodando (você já tem)
   - Rede: `traefik_public`

3. **Variáveis de Ambiente** configuradas no servidor

---

## 🚀 DEPLOY RÁPIDO

### Passo 1: Envie os Arquivos para o Servidor

```bash
# No seu PC Windows (PowerShell):
scp -r D:\CLINIAPRO root@Fbzia:/root/clinicapro
```

### Passo 2: Configure as Variáveis no Servidor

```bash
# SSH no servidor
ssh root@Fbzia

# Entre na pasta
cd /root/clinicapro

# Crie o .env
nano .env
```

**Conteúdo do .env:**
```bash
OPENAI_API_KEY=sk-proj-SUA_CHAVE_AQUI
TELEGRAM_BOT_TOKEN=SEU_TOKEN_AQUI
REDIS_PASSWORD=clinicapro_redis_2025
```

### Passo 3: Build da Imagem

```bash
# Build da imagem
docker build -t clinicapro/api:latest .
docker build -t clinicapro/bot:latest .

# OU use a mesma imagem para ambos:
docker build -t clinicapro:latest .
```

### Passo 4: Edite o YAML para Seu Domínio

```bash
# Edite o arquivo
nano clinicapro.yaml

# Substitua:
# api.clinicapro.seudominio.com → api.clinicapro.fbzia.com
# qdrant.clinicapro.seudominio.com → qdrant.clinicapro.fbzia.com
```

### Passo 5: Deploy da Stack

```bash
# Deploy
docker stack deploy -c clinicapro.yaml clinicapro

# Verifique
docker stack ps clinicapro
```

### Passo 6: Verifique os Logs

```bash
# Logs da API
docker service logs -f clinicapro_api

# Logs do Bot
docker service logs -f clinicapro_bot

# Status dos serviços
docker stack services clinicapro
```

---

## 🔧 COMANDOS ÚTEIS

### Ver Serviços Rodando
```bash
docker stack services clinicapro
```

### Ver Réplicas e Status
```bash
docker stack ps clinicapro
```

### Escalar Serviços
```bash
# Aumentar réplicas da API (mais tráfego)
docker service scale clinicapro_api=4

# Bot sempre deve ter 1 réplica apenas!
```

### Atualizar Serviço (Zero Downtime)
```bash
# Rebuild da imagem
docker build -t clinicapro:latest .

# Update da API
docker service update --image clinicapro:latest clinicapro_api

# Update do Bot
docker service update --image clinicapro:latest clinicapro_bot
```

### Reiniciar Serviço
```bash
# Força restart
docker service update --force clinicapro_bot
docker service update --force clinicapro_api
```

### Remover Stack Completa
```bash
docker stack rm clinicapro
```

---

## 🌐 INTEGRAÇÃO COM TRAEFIK

O arquivo YAML já vem configurado para Traefik. Certifique-se:

### 1. Rede Traefik Existe
```bash
docker network ls | grep traefik_public
```

Se não existir:
```bash
docker network create --driver=overlay traefik_public
```

### 2. Labels do Traefik Configuradas

No `clinicapro.yaml`:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.clinicapro-api.rule=Host(`api.clinicapro.fbzia.com`)"
  - "traefik.http.routers.clinicapro-api.entrypoints=websecure"
  - "traefik.http.routers.clinicapro-api.tls.certresolver=letsencrypt"
  - "traefik.http.services.clinicapro-api.loadbalancer.server.port=8000"
```

### 3. DNS Configurado
```bash
# Adicione no seu DNS:
api.clinicapro.fbzia.com → IP_DO_SERVIDOR
qdrant.clinicapro.fbzia.com → IP_DO_SERVIDOR
```

### 4. Teste o Acesso
```bash
curl https://api.clinicapro.fbzia.com/health
```

---

## 📊 MONITORAMENTO

### Portainer (Você já tem)
- Acesse: `https://portainer.fbzia.com`
- Vá em: **Stacks** → `clinicapro`
- Veja: Logs, status, recursos

### Logs em Tempo Real
```bash
# Últimas 100 linhas
docker service logs --tail=100 clinicapro_api

# Follow
docker service logs -f clinicapro_bot

# Todos os serviços
docker stack services clinicapro --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}"
```

### Uso de Recursos
```bash
# CPU e Memória de cada serviço
docker stats $(docker ps -q -f label=com.docker.swarm.service.name=clinicapro_api)
```

---

## 🔐 SEGURANÇA

### 1. Remova API Keys Hard-Coded

**CRÍTICO:** O código tem chaves fixas. Remova antes do deploy!

**Arquivo:** `app/whisper_service.py`
```python
# ❌ LINHA 26 - REMOVER:
api_key = "sk-proj-o9GW5F..."

# ✅ SUBSTITUIR POR:
api_key = os.getenv("OPENAI_API_KEY")
```

**Arquivo:** `app/image_analysis_service.py`
```python
# ❌ LINHA 25 - REMOVER:
api_key = "sk-proj-o9GW5F..."

# ✅ SUBSTITUIR POR:
api_key = os.getenv("OPENAI_API_KEY")
```

### 2. Proteja Qdrant
```yaml
# Adicione autenticação básica no Traefik
labels:
  - "traefik.http.middlewares.qdrant-auth.basicauth.users=admin:$$apr1$$..."
  - "traefik.http.routers.clinicapro-qdrant.middlewares=qdrant-auth"
```

### 3. Redis com Senha
```yaml
environment:
  - REDIS_PASSWORD=SUA_SENHA_FORTE_AQUI
```

---

## 🔄 CI/CD (Opcional)

### GitHub Actions

**Arquivo:** `.github/workflows/deploy.yml`
```yaml
name: Deploy to Swarm

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker Image
        run: docker build -t clinicapro:${{ github.sha }} .

      - name: Push to Registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker push clinicapro:${{ github.sha }}

      - name: Deploy to Swarm
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SSH_HOST }}
          username: root
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /root/clinicapro
            docker service update --image clinicapro:${{ github.sha }} clinicapro_api
            docker service update --image clinicapro:${{ github.sha }} clinicapro_bot
```

---

## 🐛 TROUBLESHOOTING

### Problema: Serviço não sobe

```bash
# Verifique logs detalhados
docker service ps clinicapro_api --no-trunc

# Inspecione o serviço
docker service inspect clinicapro_api
```

### Problema: Erro de rede

```bash
# Verifique redes
docker network ls

# Verifique se traefik_public existe
docker network inspect traefik_public
```

### Problema: Imagem não encontrada

```bash
# Verifique imagens disponíveis
docker images | grep clinicapro

# Rebuild se necessário
docker build -t clinicapro:latest .
```

### Problema: Variáveis de ambiente não carregam

```bash
# Use secrets do Docker (mais seguro)
echo "sk-proj-..." | docker secret create openai_api_key -
echo "1234567:ABC..." | docker secret create telegram_token -
```

Depois no YAML:
```yaml
secrets:
  - openai_api_key
  - telegram_token

secrets:
  openai_api_key:
    external: true
  telegram_token:
    external: true
```

---

## 📈 BACKUP E RESTORE

### Backup de Volumes
```bash
# Qdrant
docker run --rm -v clinicapro_qdrant_storage:/data -v $(pwd):/backup alpine tar czf /backup/qdrant_backup_$(date +%Y%m%d).tar.gz -C /data .

# Redis
docker run --rm -v clinicapro_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup_$(date +%Y%m%d).tar.gz -C /data .
```

### Restore
```bash
# Qdrant
docker run --rm -v clinicapro_qdrant_storage:/data -v $(pwd):/backup alpine tar xzf /backup/qdrant_backup_20251229.tar.gz -C /data

# Redis
docker run --rm -v clinicapro_redis_data:/data -v $(pwd):/backup alpine tar xzf /backup/redis_backup_20251229.tar.gz -C /data
```

---

## ✅ CHECKLIST PÓS-DEPLOY

- [ ] `docker stack ps clinicapro` mostra todos "Running"
- [ ] `curl https://api.clinicapro.fbzia.com/health` retorna OK
- [ ] Bot responde no Telegram
- [ ] Traefik roteia corretamente (HTTPS)
- [ ] Certificados SSL funcionando
- [ ] Logs não mostram erros
- [ ] API keys removidas do código fonte
- [ ] Backup automático configurado

---

**Pronto para produção! 🚀**
