# Como Instalar FFmpeg no Windows

## Opção 1: Download Direto (Mais Rápido)

### Passo 1: Baixar FFmpeg
1. Acesse: https://github.com/BtbN/FFmpeg-Builds/releases
2. Baixe: **ffmpeg-master-latest-win64-gpl.zip**
   - Arquivo ~150MB

### Passo 2: Extrair
1. Extraia o ZIP para `C:\ffmpeg`
2. A estrutura deve ficar:
   ```
   C:\ffmpeg\
   ├── bin\
   │   ├── ffmpeg.exe  ← O arquivo principal
   │   ├── ffplay.exe
   │   └── ffprobe.exe
   ├── doc\
   └── presets\
   ```

### Passo 3: Adicionar ao PATH

**Via Interface Gráfica:**
1. Pressione `Win + R`
2. Digite: `sysdm.cpl` e Enter
3. Aba **Avançado** → **Variáveis de Ambiente**
4. Em **Variáveis do sistema**, encontre `Path`
5. Clique em **Editar**
6. Clique em **Novo**
7. Adicione: `C:\ffmpeg\bin`
8. Clique **OK** em tudo

**OU via PowerShell (Como Administrador):**
```powershell
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "Machine") + ";C:\ffmpeg\bin",
    "Machine"
)
```

### Passo 4: Testar
1. **Feche e abra** um novo terminal
2. Digite:
```bash
ffmpeg -version
```

**Saída esperada:**
```
ffmpeg version N-... Copyright (c) 2000-2024 the FFmpeg developers
  built with gcc ...
```

### Passo 5: Reiniciar o Bot
Após instalar FFmpeg, reinicie o bot do Telegram para ele detectar o FFmpeg.

---

## Opção 2: Chocolatey (Requer Admin)

### Se você tem permissões de administrador:

1. **Abra PowerShell como Administrador**
   - Clique com botão direito no menu Iniciar
   - Selecione "Windows PowerShell (Admin)"

2. **Instale Chocolatey** (se ainda não tiver):
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
```

3. **Instale FFmpeg:**
```powershell
choco install ffmpeg -y
```

4. **Feche** o PowerShell e abra um novo terminal

5. **Teste:**
```bash
ffmpeg -version
```

---

## Opção 3: Winget (Windows 10/11)

```bash
winget install Gyan.FFmpeg
```

Depois, adicione ao PATH:
```
C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin
```

---

## Verificar Instalação no Python

Abra Python e teste:

```python
import subprocess

# Testar FFmpeg
result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
print(result.returncode)  # Deve ser 0

# Se der 0, está funcionando!
```

---

## Troubleshooting

### "ffmpeg não é reconhecido como comando"

**Solução:**
1. Verifique se `C:\ffmpeg\bin` está no PATH
2. Feche **TODOS** os terminais abertos
3. Abra um **NOVO** terminal
4. Teste novamente: `ffmpeg -version`

### "Acesso negado" ao adicionar ao PATH

**Solução:**
1. Execute PowerShell como **Administrador**
2. Ou adicione ao PATH do **Usuário** ao invés de Sistema:
   - Variáveis de Ambiente
   - **Variáveis do usuário** (seção de cima)
   - Edite `Path` do usuário

### Bot ainda não reconhece FFmpeg

**Solução:**
1. Verifique se FFmpeg funciona no terminal: `ffmpeg -version`
2. **Reinicie o bot:**
   - Feche o processo atual do bot
   - Inicie novamente: `python -m app.telegram_bot`
3. O bot carrega as variáveis de ambiente na inicialização

---

## Testar no Bot

Após instalar FFmpeg:

1. **Envie um áudio** no bot do Telegram
2. O bot deve:
   - Baixar o áudio (.ogg)
   - Converter para WAV (usando FFmpeg)
   - Transcrever com Whisper
   - Enviar transcrição

**Mensagem esperada:**
```
🎙️ Processando áudio...
🎙️ Convertendo áudio...
🎙️ Transcrevendo com Whisper...
✅ Transcrição concluída!

📝 Texto: [sua transcrição]
```

**Se der erro:**
```
❌ Erro ao converter áudio.
```
↑ Significa que FFmpeg não foi encontrado. Verifique os passos acima.

---

## Desinstalar (se necessário)

1. Remova `C:\ffmpeg`
2. Remova `C:\ffmpeg\bin` do PATH
3. Feche e abra novo terminal

---

**Resumo:**
1. Baixe FFmpeg
2. Extraia para C:\ffmpeg
3. Adicione C:\ffmpeg\bin ao PATH
4. Feche e abra novo terminal
5. Teste: `ffmpeg -version`
6. Reinicie o bot

**Pronto!** Agora o bot pode processar áudios! 🎙️
