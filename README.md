# YT-MP3 Playlist Downloader

Interface gráfica para baixar playlists e vídeos do YouTube em MP3 com alta qualidade, organização automática por pastas e suporte a autenticação via cookies.

---

## ✨ Funcionalidades

- Download de playlists completas e vídeos individuais
- Conversão automática para MP3 (128 / 192 / 256 / 320 kbps)
- **Uma pasta por playlist** — organização automática pelo título da playlist
- Fila de downloads com múltiplas URLs
- Busca automática do título e contagem de faixas ao adicionar URLs
- Metadados ID3 embutidos automaticamente (título, artista, álbum)
- Capa do álbum embutida no MP3
- Autenticação via `cookies.txt` — acessa conteúdo da sua conta logada
- Log de atividade em tempo real com velocidade e ETA
- Indicadores visuais de status do FFmpeg e Deno
- Configurações salvas entre sessões
- Interface dark mode — sem dependências externas de UI

---

## 📋 Pré-requisitos

### 1. Python 3.8+
Baixe em https://python.org

### 2. FFmpeg
Necessário para converter o áudio para MP3.

```bash
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt install ffmpeg
```

### 3. Deno
Necessário para resolver os desafios JavaScript do YouTube (obrigatório desde 2025).

```bash
# Windows
winget install DenoLand.Deno

# macOS / Linux
curl -fsSL https://deno.land/install.sh | sh
```

> Após instalar FFmpeg e Deno, **feche e abra o terminal novamente** antes de rodar o script.

---

## 🚀 Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/yt-mp3-downloader.git
cd yt-mp3-downloader

# Instale a dependência Python
pip install yt-dlp
```

O script instala o `yt-dlp` automaticamente caso não esteja presente.

---

## ▶️ Como usar

```bash
python yt_playlist_downloader.py
```

### Passo a passo

1. **Exporte o `cookies.txt`** do Chrome (veja seção abaixo)
2. Clique em **`📄`** e selecione o arquivo `cookies.txt`
3. Cole a URL de uma playlist ou vídeo no campo de URL
4. Clique em **`＋ Adicionar`** — o título e número de faixas aparecem automaticamente
5. Repita para quantas playlists quiser
6. Escolha a **pasta de saída** e a **qualidade** desejada
7. Clique em **`⬇ BAIXAR TUDO`**

---

## 🍪 Exportando o cookies.txt

O YouTube exige autenticação para acessar certos conteúdos e para evitar bloqueios. O `cookies.txt` é a forma mais segura — nenhuma senha é digitada no script.

1. Instale a extensão **"Get cookies.txt LOCALLY"** no Chrome
   - [Chrome Web Store](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Acesse **youtube.com** e faça login na sua conta Google
3. Clique no ícone da extensão → **Export** → salve como `cookies.txt`
4. Selecione o arquivo no script pelo botão `📄`

> ⚠️ O `cookies.txt` contém tokens de sessão sensíveis. **Não compartilhe e não comite no Git.**

---

## 📁 Estrutura de saída

Cada playlist adicionada cria sua própria pasta nomeada pelo título da playlist:

```
Downloads/YouTube MP3/
├── AM - Arctic Monkeys/
│   ├── 01. Do I Wanna Know.mp3
│   ├── 02. R U Mine.mp3
│   └── 03. Why'd You Only Call Me When You're High.mp3
├── Currents - Tame Impala/
│   ├── 01. Let It Happen.mp3
│   └── 02. Nangs.mp3
└── Lo-Fi Hip Hop Mix 2025/
    ├── 01. Track Name.mp3
    └── ...
```

---

## ⚙️ Template de nome de arquivo

No campo **"Nome do arquivo"** use variáveis do yt-dlp:

| Variável | Resultado |
|---|---|
| `%(playlist_index)s. %(title)s` | `01. Nome da Música` (padrão) |
| `%(title)s` | `Nome da Música` |
| `%(uploader)s - %(title)s` | `Artista - Nome da Música` |
| `%(upload_date)s %(title)s` | `20240315 Nome da Música` |

---

## 🛠️ Dependências

| Pacote | Uso |
|---|---|
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | Engine de download e extração |
| `tkinter` + `ttk` | Interface gráfica (incluso no Python) |
| [FFmpeg](https://ffmpeg.org) | Conversão para MP3, metadados e capa |
| [Deno](https://deno.land) | Runtime JS para resolver desafios do YouTube |

---

## 🔒 Segurança e privacidade

- O `cookies.txt` é lido localmente — nunca enviado a nenhum servidor
- Nenhuma senha ou credencial é armazenada pelo script
- As configurações ficam em `~/.ytmp3_config.json` (apenas caminhos e preferências)

### `.gitignore` recomendado

```gitignore
cookies.txt
__pycache__/
*.pyc
.ytmp3_config.json
```

---

## 🐛 Problemas comuns

| Erro | Solução |
|---|---|
| `Signature solving failed` | Instale o Deno: `winget install DenoLand.Deno` e reinicie o terminal |
| `Only images are available` | cookies.txt inválido ou expirado — exporte novamente do Chrome |
| `FFmpeg not found` | Instale o FFmpeg: `winget install ffmpeg` e reinicie o terminal |
| `failed to load cookies` | Feche o Chrome completamente ou use o arquivo `cookies.txt` |
| Downloads bloqueados | YouTube aplica rate limit por IP — aguarde alguns minutos |

---

## 📄 Licença

MIT License — use, modifique e distribua livremente.
