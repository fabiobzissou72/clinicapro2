# 📝 DEPLOY MANUAL - PASSO A PASSO

Se preferir fazer manualmente com controle total.

---

## PARTE 1: NO SEU PC (Windows)

### Passo 1: Git Push

```bash
cd D:\CLINIAPRO

# Adiciona tudo
git add .

# Commit
git commit -m "feat: Docker + Emergency protocols + Security fixes"

# Push
git push -u origin main
```

**✅ Confirme:** Acesse https://github.com/fabiobzissou72/clinicapro2 e veja se os arquivos estão lá

---

## PARTE 2: NA VPS (Servidor)

### Passo 2: Conecte na VPS

```bash
# Do seu PC, conecte via SSH
ssh root@Fbzia

# OU se tiver porta diferente:
ssh -p 22 root@Fbzia
```

### Passo 3: Clone o Repositório

```bash
# Remove instalação antiga (se existir)
cd /root
rm -rf clinicapro2

# Clone novo
git clone https://github.com/fabiobzissou72/clinicapro2.git
cd clinicapro2

# Confirme que está lá
ls -la
```

### Passo 4: Configure as Variáveis

```bash
# Crie o .env
nano .env
```

**Cole isso (substitua com suas chaves reais):**
```bash
OPENAI_API_KEY=sk-proj-SUA_CHAVE_AQUI
TELEGRAM_BOT_TOKEN=SEU_TOKEN_AQUI
REDIS_PASSWORD=clinicapro_redis_2025
```

**Salve:** Ctrl+O, Enter, Ctrl+X

### Passo 5: Build da Imagem

```bash
# Build
docker build -t clinicapro:latest .

# Isso vai levar 2-3 minutos na primeira vez
# Vai instalar FFmpeg e todas as dependências
```

**✅ Confirme:** Deve aparecer "Successfully tagged clinicapro:latest"

### Passo 6: Edite o YAML (Opcional)

Se quiser customizar domínios:

```bash
nano clinicapro.yaml

# Substitua:
# api.clinicapro.seudominio.com → api.clinicapro.fbzia.com
# qdrant.clinicapro.seudominio.com → qdrant.clinicapro.fbzia.com
```

### Passo 7: Deploy no Swarm

```bash
# Se já tem uma stack rodando, remova primeiro:
docker stack rm clinicapro

# Aguarde 10 segundos
sleep 10

# Deploy da nova stack
docker stack deploy -c clinicapro.yaml clinicapro
```

**✅ Confirme:** Deve aparecer "Creating service clinicapro_api" etc

### Passo 8: Verifique o Status

```bash
# Lista os serviços
docker stack ps clinicapro

# Deve mostrar:
# clinicapro_api.1     Running
# clinicapro_bot.1     Running
# clinicapro_qdrant.1  Running
# clinicapro_redis.1   Running
```

### Passo 9: Veja os Logs

```bash
# Logs da API
docker service logs -f clinicapro_api

# Em outro terminal (novo SSH), logs do Bot
docker service logs -f clinicapro_bot
```

**✅ Procure por:**
- API: "Application startup complete"
- Bot: "Bot rodando!"

### Passo 10: Teste

```bash
# Teste a API
curl http://localhost:8000/health

# Deve retornar: {"status":"ok"}
```

**Telegram:**
- Abra o Telegram
- Procure seu bot
- Envie `/start`
- Deve responder com a mensagem de boas-vindas

---

## 🔍 COMANDOS ÚTEIS

### Ver Status
```bash
docker stack services clinicapro
docker stack ps clinicapro
```

### Ver Logs
```bash
# API
docker service logs --tail 50 clinicapro_api

# Bot
docker service logs --tail 50 clinicapro_bot

# Tempo real
docker service logs -f clinicapro_bot
```

### Reiniciar Serviço
```bash
docker service update --force clinicapro_bot
docker service update --force clinicapro_api
```

### Escalar API (mais réplicas)
```bash
# 3 réplicas da API
docker service scale clinicapro_api=3

# Bot sempre deve ter apenas 1!
```

### Remover Tudo
```bash
docker stack rm clinicapro
```

---

## 🐛 TROUBLESHOOTING

### Serviço não sobe

```bash
# Veja erro detalhado
docker service ps clinicapro_api --no-trunc

# Inspecione
docker service inspect clinicapro_api
```

### Erro de rede

```bash
# Verifique se a rede Fbzianet existe
docker network ls | grep Fbzianet

# Se não existir, crie:
docker network create --driver=overlay Fbzianet
```

### Rebuild após mudanças

```bash
# Rebuild
docker build -t clinicapro:latest .

# Update (zero downtime)
docker service update --image clinicapro:latest clinicapro_api
docker service update --image clinicapro:latest clinicapro_bot
```

---

## ✅ CHECKLIST FINAL

- [ ] Git push funcionou
- [ ] Código no GitHub: https://github.com/fabiobzissou72/clinicapro2
- [ ] Conectou na VPS via SSH
- [ ] Repositório clonado em /root/clinicapro2
- [ ] .env configurado com API keys
- [ ] Build da imagem concluído
- [ ] Stack deployada: `docker stack deploy`
- [ ] Serviços rodando: `docker stack ps clinicapro`
- [ ] API responde: `curl localhost:8000/health`
- [ ] Bot responde no Telegram: `/start`
- [ ] Logs sem erros críticos

---

**Pronto! Sistema em produção! 🚀**
