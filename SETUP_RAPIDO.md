# 🚀 Setup Rápido - ClinicaPro Cardio

## 📋 Checklist de Instalação

### 1. ✅ Instalar Dependências

```bash
pip install -r requirements.txt
```

Pacotes principais adicionados:
- `streamlit` - Dashboard
- `plotly` - Gráficos
- `python-jose` - JWT
- `passlib[bcrypt]` - Hash de senhas

---

### 2. 🗄️ Configurar Banco de Dados (Supabase)

**IMPORTANTE:** Use o arquivo `database/schema_doctors_v2.sql` (versão 2 - mais robusta)

#### Passo a passo:

1. Acesse o Supabase: https://supabase.com
2. Vá em seu projeto
3. Clique em "SQL Editor" no menu lateral
4. Clique em "+ New query"
5. Cole TODO o conteúdo de `database/schema_doctors_v2.sql`
6. Clique em "Run" (ou pressione Ctrl+Enter)

#### O que o SQL faz:

- ✅ Cria tabela `doctors` (se não existir)
- ✅ Adiciona colunas `is_active` e `updated_at` (se não existirem)
- ✅ Cria índices para performance
- ✅ Adiciona coluna `doctor_id` em `case_analyses` (se não existir)
- ✅ Cria trigger para atualizar `updated_at` automaticamente
- ⚠️ RLS está DESABILITADO por padrão (mais fácil para testes)

#### Se der erro "column already exists":

É normal! O script verifica antes de criar. Se der esse erro, significa que a coluna já existe e está OK.

---

### 3. 🔑 Verificar .env

Certifique-se que seu `.env` tem:

```env
# Autenticação (ADICIONAR se não tiver)
SECRET_KEY=mude-isso-para-producao-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Outros (já deve ter)
OPENAI_API_KEY=sk-proj-...
TELEGRAM_BOT_TOKEN=...
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...
QDRANT_URL=https://...
QDRANT_API_KEY=...
```

**Gerar SECRET_KEY segura:**

```bash
# No terminal Python
python -c "import secrets; print(secrets.token_hex(32))"
```

Copie o resultado e cole no SECRET_KEY do .env

---

### 4. ▶️ Iniciar Serviços

Abra **3 terminais**:

#### Terminal 1: API Principal
```bash
python -m app.main
# ou
uvicorn app.main:app --reload --port 8000
```

Acesse: http://localhost:8000/docs

#### Terminal 2: Bot Telegram
```bash
python -m app.telegram_bot
```

Teste no Telegram: @ClinicaPro_Bot

#### Terminal 3: Dashboard Streamlit
```bash
streamlit run streamlit_crewai_dashboard.py
```

Acesse: http://localhost:8501

---

## 🧪 Testar Instalação

### 1. Testar API (no navegador ou Postman)

**Registrar médico:**
```
POST http://localhost:8000/api/v1/auth/register
Content-Type: application/json

{
  "name": "Dr. Teste Silva",
  "crm": "99999-SP",
  "email": "teste@teste.com",
  "password": "senha12345",
  "specialty": "Cardiologia",
  "phone": "(11) 99999-9999"
}
```

**Fazer login:**
```
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "teste@teste.com",
  "password": "senha12345"
}
```

Copie o `access_token` da resposta.

**Testar rota protegida:**
```
GET http://localhost:8000/api/v1/auth/me
Authorization: Bearer SEU_TOKEN_AQUI
```

Se retornar seus dados, está funcionando! ✅

---

### 2. Testar Bot Telegram

1. Abra o Telegram
2. Busque: @ClinicaPro_Bot (ou use o nome do seu bot)
3. Teste comandos:

```
/start
/help
/paciente João Silva
/prontuario
/sugestao
```

---

### 3. Testar Dashboard Streamlit

1. Acesse: http://localhost:8501
2. Vá em "📤 Upload de Documentos"
3. Faça upload de um PDF de teste
4. Verifique em "🔍 Busca no Qdrant"

---

## 🐛 Troubleshooting

### Erro: "column is_active does not exist"

**Solução:** Use `database/schema_doctors_v2.sql` em vez da versão 1.

---

### Erro: "OPENAI_API_KEY not configured"

**Solução:** Verifique se a chave está no `.env` e reinicie o serviço.

---

### Erro: "Failed to connect to Qdrant"

**Solução:**
1. Verifique `QDRANT_URL` e `QDRANT_API_KEY` no `.env`
2. Teste a conexão: https://qdrant.fbzia.com.br/dashboard

---

### Erro: "Unauthorized" ao testar API

**Solução:**
1. Verifique se fez login e copiou o token
2. Use o header: `Authorization: Bearer SEU_TOKEN`
3. Verifique se o token não expirou (padrão: 30 min)

---

### Bot Telegram não responde

**Solução:**
1. Verifique se `TELEGRAM_BOT_TOKEN` está correto
2. Verifique se o bot está rodando (terminal 2)
3. Envie `/start` para iniciar conversa

---

## 📊 Verificar se Tudo Funciona

### Checklist Final:

- [ ] API rodando em http://localhost:8000
- [ ] Swagger docs acessível em http://localhost:8000/docs
- [ ] Consegui registrar médico via API
- [ ] Consegui fazer login e obter token
- [ ] Rotas protegidas funcionam com token
- [ ] Bot Telegram responde comandos
- [ ] Dashboard Streamlit carrega em http://localhost:8501
- [ ] Consigo fazer upload de PDF no Streamlit
- [ ] Busca no Qdrant funciona

---

## 🎉 Próximos Passos

Tudo funcionando? Agora você pode:

1. **Explorar a API:** http://localhost:8000/docs
2. **Testar novos comandos do bot:**
   - `/paciente [nome ou CPF]`
   - `/prontuario` (e enviar áudio/texto)
   - `/sugestao` (e enviar sintomas)
3. **Fazer upload de guidelines** no Streamlit
4. **Criar pacientes** via API `/api/v1/patients`
5. **Consultar dashboard** em `/api/v1/dashboard/stats`

---

## 📚 Documentação Completa

Para detalhes de cada funcionalidade, veja:
- `README_NOVOS_RECURSOS.md` - Documentação completa
- `http://localhost:8000/docs` - API Swagger

---

## 💡 Dicas

- Use o Swagger UI para testar endpoints facilmente
- Mantenha os 3 terminais abertos durante desenvolvimento
- Logs da API ficam em `clinicapro_cardio.log`
- Para produção, use `gunicorn` ou `uvicorn` com workers

---

Desenvolvido com ❤️ para ClinicaPro
