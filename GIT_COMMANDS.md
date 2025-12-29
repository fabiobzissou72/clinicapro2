# 📤 COMANDOS GIT PARA PUSH

Siga estes passos para fazer o push para o GitHub.

---

## ✅ CHECKLIST PRÉ-PUSH

Verifique se você fez:
- [x] API keys removidas do código (whisper_service.py, image_analysis_service.py)
- [x] .env no .gitignore
- [x] Docker configurado (Dockerfile, docker-compose.yml, clinicapro.yaml)
- [x] README.md atualizado
- [x] Documentação criada (DOCKER_SETUP.md, DEPLOY_SWARM.md)

---

## 🚀 COMANDOS

### Passo 1: Verifique o Status

```bash
cd D:\CLINIAPRO

# Veja o que mudou
git status

# Veja diferenças
git diff
```

### Passo 2: Adicione os Arquivos

```bash
# Adiciona tudo
git add .

# OU adicione apenas arquivos específicos:
git add Dockerfile docker-compose.yml clinicapro.yaml
git add app/whisper_service.py app/image_analysis_service.py
git add app/crews/cardio_crew.py
git add .dockerignore .env.example .gitignore
git add README.md DOCKER_SETUP.md DEPLOY_SWARM.md
```

### Passo 3: Commit

```bash
# Commit com mensagem clara
git commit -m "feat: Add Docker support with FFmpeg + Remove hardcoded API keys + Emergency protocols

- Add Dockerfile with FFmpeg for audio processing
- Add docker-compose.yml for local development
- Add clinicapro.yaml for Docker Swarm production
- Remove hardcoded OpenAI API keys (security fix)
- Add emergency protocols (hypertensive crisis, ACS)
- Fix date display in reports (now uses datetime.now())
- Add comprehensive documentation (Docker, Swarm, etc)
- Update .gitignore for security
- Add .env.example template
"
```

### Passo 4: Conecte ao Repositório (se necessário)

```bash
# Se ainda não adicionou o remote:
git remote add origin https://github.com/fabiobzissou72/clinicapro2.git

# Verifique
git remote -v
```

### Passo 5: Push

```bash
# Push para a branch main
git push -u origin main

# Se der erro de histórico divergente, force (cuidado!):
# git push -f origin main
```

---

## 🔧 ALTERNATIVA: NOVO REPOSITÓRIO LIMPO

Se quiser começar do zero:

```bash
# Remove .git existente
rm -rf .git

# Inicializa novo repo
git init

# Cria branch main
git branch -M main

# Adiciona tudo
git add .

# Primeiro commit
git commit -m "Initial commit: ClinicaPro Cardio v0.2 with Docker"

# Conecta ao GitHub
git remote add origin https://github.com/fabiobzissou72/clinicapro2.git

# Push
git push -u origin main -f
```

---

## 📝 APÓS O PUSH

### 1. Verifique no GitHub
- Acesse: https://github.com/fabiobzissou72/clinicapro2
- Veja se todos os arquivos estão lá
- **IMPORTANTE**: Confirme que `.env` NÃO está lá!

### 2. Configure Secrets no GitHub (para CI/CD)

Se for usar GitHub Actions:

1. Vá em: **Settings** → **Secrets and variables** → **Actions**
2. Adicione:
   - `OPENAI_API_KEY`: sua chave OpenAI
   - `TELEGRAM_BOT_TOKEN`: token do bot
   - `DOCKER_USERNAME`: seu usuário Docker Hub
   - `DOCKER_PASSWORD`: sua senha Docker Hub

### 3. Teste o Clone

```bash
# Em outro lugar
git clone https://github.com/fabiobzissou72/clinicapro2.git
cd clinicapro2

# Copie .env
cp .env.example .env
# Edite e adicione suas chaves

# Teste Docker
docker-compose up -d
```

---

## 🚨 TROUBLESHOOTING

### Erro: "Updates were rejected"

```bash
# Puxa as mudanças do remoto primeiro
git pull origin main --rebase

# Resolve conflitos se houver
git add .
git rebase --continue

# Depois push
git push origin main
```

### Erro: "Permission denied"

```bash
# Configure suas credenciais
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"

# Use token pessoal em vez de senha
# GitHub → Settings → Developer Settings → Personal Access Tokens
```

### Erro: ".env foi commitado por engano"

```bash
# URGENTE - Remova do histórico!
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# Force push (cuidado!)
git push -f origin main

# DEPOIS: Revogue e regenere TODAS as API keys!
```

---

## 📊 TAGS E RELEASES

### Criar uma Tag

```bash
# Tag para versão 0.2
git tag -a v0.2 -m "Version 0.2: Docker support + Emergency protocols"

# Push da tag
git push origin v0.2
```

### Criar Release no GitHub

1. Acesse: https://github.com/fabiobzissou72/clinicapro2/releases
2. Clique: **Draft a new release**
3. Tag: `v0.2`
4. Título: `ClinicaPro Cardio v0.2 - Docker Ready`
5. Descrição:
```markdown
## 🎉 Novidades

- 🐳 **Docker Suporte Completo**: docker-compose e Swarm
- 🎤 **FFmpeg Integrado**: Áudio funcionando no Docker
- 🚨 **Protocolos de Emergência**: Timing crítico minuto a minuto
- 📅 **Data Corrigida**: Relatórios com data atual
- 🔐 **Segurança**: API keys removidas do código

## 📦 Como Usar

```bash
git clone https://github.com/fabiobzissou72/clinicapro2.git
cd clinicapro2
cp .env.example .env
# Configure suas API keys
docker-compose up -d
```

Veja documentação completa no [README](README.md)
```

---

## ✅ PRONTO!

Seu código agora está no GitHub:
- 🌐 https://github.com/fabiobzissou72/clinicapro2
- 📖 Documentação acessível
- 🐳 Pronto para deploy
- 🔐 Seguro (sem API keys)

---

**Next Steps:**
1. Deploy no seu servidor Swarm
2. Configure CI/CD (opcional)
3. Compartilhe com a comunidade!
