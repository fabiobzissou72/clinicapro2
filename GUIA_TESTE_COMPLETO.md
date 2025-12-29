# Guia Completo de Testes - ClinicaPro Cardio

## ✅ IMPLEMENTAÇÕES CONCLUÍDAS

### 1. **Otimização de Tempo de Resposta**
- ⚡ **56 segundos** (antes: 125s - melhoria de 55%)
- 2 chamadas LLM em vez de 8
- `allow_delegation=False` + `max_iter=3`
- Timeout ajustado para 180s

### 2. **Transcrição de Áudio Completa** 🎤
- Whisper modelo base
- Suporte: OGG, MP3, M4A, WAV
- Conversão automática com pydub
- Limpeza de arquivos temporários

### 3. **Análise de Imagens (ECG, Raio-X)** 📸 **NOVO!**
- GPT-4o-mini Vision
- Análise técnica de ECGs
- Suporte para raio-x e ecocardiogramas
- Integração automática com análise clínica

---

## 🚀 COMO TESTAR

### Pré-requisitos:
1. ✅ FFmpeg instalado (para áudio)
2. ✅ Pillow e OpenCV instalados (para imagens)
3. ✅ API rodando (`python run_api.py`)
4. ✅ Bot rodando (`python -m app.telegram_bot`)

---

## 📋 TESTE 1: Análise de Texto

**O que fazer:**
1. Abra chat com bot no Telegram
2. Envie `/start`
3. Envie mensagem de texto:
```
Paciente masculino, 58 anos, hipertenso, diabético.
Queixa: Dor torácica em aperto há 2 horas, irradiando para braço esquerdo.
Exame físico: PA 160/100, FC 95, SpO2 96%.
Ectoscopia: Regular estado geral.
Cardiovascular: BNF 2T sem sopros.
```

**Resultado esperado:**
- ✅ Resposta em 60-90 segundos
- ✅ Relatório SOAP completo
- ✅ Diagnósticos diferenciais (IAM, angina, etc.)
- ✅ Exames sugeridos
- ✅ Conduta baseada em guidelines

---

## 🎤 TESTE 2: Transcrição de Áudio

**O que fazer:**
1. No Telegram, pressione e segure botão de microfone
2. Grave voice note descrevendo caso:
```
"Paciente com cinquenta e cinco anos, hipertenso,
refere dor no peito há uma hora,
pressão arterial cento e sessenta por cem,
frequência cardíaca noventa e cinco"
```
3. Envie o áudio

**Resultado esperado:**
- ✅ "Etapa 1/3: Baixando áudio..."
- ✅ "Etapa 2/3: Convertendo formato..."
- ✅ "Etapa 3/3: Transcrevendo com IA..."
- ✅ Mostra transcrição (prévia de 200 chars)
- ✅ Análise completa após ~70-100 segundos

**Tempo total:** ~70-120 segundos (10-20s transcrição + 60s análise)

---

## 📸 TESTE 3: Análise de Imagem (ECG) **NOVO!**

**O que fazer:**
1. Tire foto de um ECG (ou baixe exemplo da internet)
2. Envie a foto no Telegram

**Resultado esperado:**
- ✅ "Etapa 1/3: Baixando imagem..."
- ✅ "Etapa 2/3: Analisando imagem com IA..."
- ✅ Análise técnica do ECG:
  - Frequência cardíaca
  - Ritmo (sinusal, FA, etc.)
  - Intervalos (PR, QRS, QT)
  - Alterações (isquemia, bloqueios, etc.)
  - Interpretação clínica
  - Urgência (EMERGÊNCIA/URGENTE/ROTINA)
- ✅ Pergunta se quer análise completa com dados clínicos

**Tempo:** ~15-30 segundos

---

## 🔗 TESTE 4: Imagem + Dados Clínicos (Integração)

**O que fazer:**
1. Envie foto de ECG
2. Aguarde análise da imagem
3. Quando bot perguntar, envie texto com dados clínicos:
```
Paciente 62 anos, hipertensão não controlada,
dor precordial súbita há 30 minutos,
sudorese fria, náusea.
PA 180/110, FC 105.
```

**Resultado esperado:**
- ✅ Bot confirma: "Integrando análise da imagem com dados clínicos..."
- ✅ Transcrição enviada ao crew já inclui análise do ECG
- ✅ Relatório SOAP correlaciona ECG com quadro clínico
- ✅ Conduta mais específica baseada em ECG + sintomas

**Tempo:** ~60-90 segundos para análise completa

---

## 🧪 TESTE 5: Raio-X / Ecocardiograma

**O que fazer:**
1. Envie foto de raio-x de tórax com legenda: `RX de tórax`
2. OU envie foto de eco com legenda: `Ecocardiograma`

**Resultado esperado:**
- ✅ Bot detecta tipo pela legenda
- ✅ Análise específica para o tipo de exame
- ✅ Descrição de achados radiológicos/ecocardiográficos
- ✅ Interpretação clínica

---

## ⚠️ TRATAMENTO DE ERROS CORRIGIDO

### Erro anterior:
```
❌ Erro inesperado ao processar análise.
```

### Agora mostra erro real:
```
❌ Erro inesperado: <descrição do erro>
```

**Possíveis erros:**
- `Timeout na análise` → Caso muito complexo (aumentar timeout?)
- `Erro ao processar áudio` → FFmpeg não instalado ou áudio corrompido
- `Erro ao processar imagem` → Imagem muito grande ou formato inválido
- `API key error` → Problema com OpenAI API

---

## 📊 ESTRUTURA COMPLETA DO SISTEMA

```
Telegram → Bot
  ├─ FOTO → GPT-4V → Análise ECG → [Salva contexto]
  ├─ ÁUDIO → Whisper → Texto → CrewAI → SOAP
  └─ TEXTO → [Integra ECG se existe] → CrewAI → SOAP

CrewAI:
  Task 1: Especialista analisa caso (coronary/HF/arritmia)
  Task 2: Coordinator sintetiza SOAP
```

---

## 🐛 TROUBLESHOOTING

### Bot não responde:
```bash
# Verificar se bot está rodando
tasklist | findstr python

# Reiniciar bot
python -m app.telegram_bot
```

### API dando erro 500:
```bash
# Ver logs
tail -f C:\Users\fbzis\AppData\Local\Temp\claude\D--CLINIAPRO\tasks\bdff2be.output

# Reiniciar API
python run_api.py
```

### Transcrição de áudio falha:
```bash
# Verificar FFmpeg
ffmpeg -version

# Se não instalado:
choco install ffmpeg
```

### Análise de imagem falha:
```bash
# Verificar dependências
pip list | findstr -i "pillow opencv openai"

# Se faltando:
pip install pillow opencv-python
```

### Timeout persistente:
- Aumentar timeout em `app/telegram_bot.py` linha 324 e 218
- Verificar créditos OpenAI
- Simplificar transcrição/dados

---

## 💰 CUSTOS APROXIMADOS

| Operação | Modelo | Custo Médio |
|----------|--------|-------------|
| Análise texto | gpt-4o-mini | ~$0.002/análise |
| Transcrição áudio (1min) | whisper | Local (grátis) |
| Análise ECG | gpt-4o-mini vision | ~$0.003/imagem |
| **Análise completa** | **Total** | **~$0.005** |

Com $1.73 de crédito: **~346 análises completas**

---

## ✅ CHECKLIST FINAL

- [x] API otimizada (56s vs 125s)
- [x] Áudio funcionando (Whisper + conversão)
- [x] Imagens funcionando (GPT-4V)
- [x] Integração imagem + texto
- [x] Error handling melhorado
- [x] Timeout ajustado (180s)
- [x] Dependencies instaladas
- [x] Documentação completa

---

## 🎯 TESTE AGORA!

1. **Terminal 1:**
```bash
cd D:\CLINIAPRO
python run_api.py
```

2. **Terminal 2:**
```bash
cd D:\CLINIAPRO
python -m app.telegram_bot
```

3. **Telegram:**
   - Envie `/start`
   - Teste com foto de ECG
   - Teste com áudio
   - Teste com texto
   - Teste integração foto + texto

**Boa sorte! 🚀**
