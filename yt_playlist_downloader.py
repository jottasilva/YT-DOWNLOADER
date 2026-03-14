#!/usr/bin/env python3
"""
YT-MP3 Playlist Downloader
Dependências: pip install yt-dlp
Requer: Deno instalado (winget install DenoLand.Deno)
        FFmpeg instalado (winget install ffmpeg)
        cookies.txt exportado do Chrome (extensão "Get cookies.txt LOCALLY")
"""

import os
import sys
import json
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

try:
    import yt_dlp
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "-q"])
    import yt_dlp

# ─── Cores ────────────────────────────────────────────────────────────────────
C = {
    "bg":       "#0f0f0f",
    "surface":  "#1a1a1a",
    "card":     "#1e1e1e",
    "border":   "#2e2e2e",
    "accent":   "#e63946",
    "accent2":  "#ff6b35",
    "text":     "#f0f0f0",
    "muted":    "#777777",
    "success":  "#06d6a0",
    "warning":  "#ffd166",
    "error":    "#ef476f",
    "entry_bg": "#282828",
    "sel":      "#3a3a3a",
}

FONT       = ("Consolas", 10)
FONT_BOLD  = ("Consolas", 10, "bold")
FONT_SM    = ("Consolas", 9)
FONT_TITLE = ("Consolas", 20, "bold")

CONFIG_FILE = Path.home() / ".ytmp3_config.json"

# ─── Config ───────────────────────────────────────────────────────────────────
def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "output_dir":        str(Path.home() / "Downloads" / "YouTube MP3"),
        "quality":           "320",
        "cookies_file":      "",
        "filename_template": "%(playlist_index)s. %(title)s",
    }

def save_config(cfg):
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        pass

# ─── Helpers UI ───────────────────────────────────────────────────────────────
def bg_of(w):
    try:
        return w.cget("bg")
    except Exception:
        return C["bg"]

def mk_frame(parent, **kw):
    kw.setdefault("bg", bg_of(parent))
    return tk.Frame(parent, **kw)

def mk_label(parent, text="", color=None, font=FONT, anchor="w", **kw):
    kw.setdefault("bg", bg_of(parent))
    return tk.Label(parent, text=text, fg=color or C["text"],
                    font=font, anchor=anchor, bd=0, **kw)

def mk_entry(parent, textvariable=None, width=30, **kw):
    return tk.Entry(parent, textvariable=textvariable, width=width,
                    bg=C["entry_bg"], fg=C["text"],
                    insertbackground=C["text"],
                    relief="flat", font=FONT, bd=4,
                    disabledbackground=C["entry_bg"],
                    disabledforeground=C["muted"], **kw)

def mk_btn(parent, text, cmd, bg=None, fg=C["text"], font=FONT_BOLD,
           hover=None, **kw):
    _bg    = bg    or C["accent"]
    _hover = hover or C["accent2"]
    kw.setdefault("padx", 12)
    kw.setdefault("pady", 6)
    b = tk.Button(parent, text=text, command=cmd,
                  bg=_bg, fg=fg, font=font,
                  activebackground=_hover, activeforeground=fg,
                  relief="flat", bd=0, cursor="hand2", **kw)
    b.bind("<Enter>", lambda e: b.configure(bg=_hover))
    b.bind("<Leave>", lambda e: b.configure(bg=_bg))
    return b

def section(parent, title):
    f = mk_frame(parent)
    f.pack(fill="x", pady=(14, 3))
    tk.Frame(f, bg=C["accent"], width=3, height=13).pack(side="left")
    mk_label(f, "  " + title.upper(),
             color=C["accent"], font=("Consolas", 8, "bold")).pack(side="left")

def card(parent, **kw):
    kw.setdefault("bg", C["card"])
    kw.setdefault("highlightbackground", C["border"])
    kw.setdefault("highlightthickness", 1)
    return tk.Frame(parent, **kw)

# ─── App ──────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg            = load_config()
        self.queue          = []          # lista de dicts {url, label, status}
        self.is_downloading = False
        self._stop_flag     = False

        self.title("YT-MP3  //  Playlist Downloader")
        self.geometry("1020x760")
        self.minsize(860, 640)
        self.configure(bg=C["bg"])

        self._ttk_style()
        self._build()
        self._check_deps()

    # ── TTK ───────────────────────────────────────────────────────────────────
    def _ttk_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        for w in ("TCombobox",):
            s.configure(w, fieldbackground=C["entry_bg"],
                        background=C["entry_bg"], foreground=C["text"],
                        selectbackground=C["accent"], selectforeground=C["text"],
                        arrowcolor=C["text"], bordercolor=C["border"],
                        relief="flat", padding=4)
            s.map(w, fieldbackground=[("readonly", C["entry_bg"])],
                  foreground=[("readonly", C["text"])])
        s.configure("TProgressbar", troughcolor=C["border"],
                    background=C["accent"], bordercolor=C["border"],
                    lightcolor=C["accent"], darkcolor=C["accent"])
        s.configure("Vertical.TScrollbar", background=C["border"],
                    troughcolor=C["surface"], arrowcolor=C["muted"],
                    bordercolor=C["surface"])

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=C["surface"], height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        mk_label(hdr, "▶  YT-MP3", color=C["accent"],
                 font=FONT_TITLE, bg=C["surface"]).pack(side="left", padx=20, pady=10)
        mk_label(hdr, "Playlist & Vídeo Downloader  —  yt-dlp + Deno + FFmpeg",
                 color=C["muted"], font=FONT_SM,
                 bg=C["surface"]).pack(side="left", pady=10)

        # Indicadores de dependências (direita do header)
        self._dep_frame = tk.Frame(hdr, bg=C["surface"])
        self._dep_frame.pack(side="right", padx=16)

        tk.Frame(self, bg=C["accent"], height=2).pack(fill="x")

        # Corpo
        body = mk_frame(self)
        body.pack(fill="both", expand=True)

        left = mk_frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(16, 8), pady=10)

        right = mk_frame(body)
        right.pack(side="right", fill="both", expand=False,
                   padx=(8, 16), pady=10)
        right.configure(width=360)
        right.pack_propagate(False)

        self._build_left(left)
        self._build_right(right)

        # Status bar
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")
        sb = tk.Frame(self, bg=C["surface"], height=26)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self.status_var = tk.StringVar(value="Pronto.")
        tk.Label(sb, textvariable=self.status_var,
                 font=("Consolas", 8), fg=C["muted"],
                 bg=C["surface"], anchor="w").pack(side="left", padx=12)

    def _build_left(self, p):
        # ── URL
        section(p, "URL  /  Playlist ou Vídeo")
        url_card = card(p)
        url_card.pack(fill="x", pady=(3, 10))

        self.url_var = tk.StringVar()
        url_e = mk_entry(url_card, textvariable=self.url_var, width=50)
        url_e.pack(side="left", fill="x", expand=True, padx=(10, 6), pady=8)
        url_e.bind("<Return>", lambda e: self._add_url())

        mk_btn(url_card, "＋ Adicionar", self._add_url).pack(
            side="right", padx=6, pady=6)

        # ── Configurações
        section(p, "Configurações")
        cfg_card = card(p)
        cfg_card.pack(fill="x", pady=(3, 10))

        def row(lbl, width=14):
            r = mk_frame(cfg_card, bg=C["card"])
            r.pack(fill="x", padx=12, pady=5)
            mk_label(r, lbl, color=C["muted"], font=FONT_SM,
                     bg=C["card"], width=width).pack(side="left")
            return r

        # Pasta de saída
        r1 = row("Pasta de saída")
        self.dir_var = tk.StringVar(value=self.cfg["output_dir"])
        mk_entry(r1, textvariable=self.dir_var, width=34).pack(
            side="left", fill="x", expand=True, padx=(4, 4))
        mk_btn(r1, "📁", self._choose_dir,
               bg=C["border"], hover=C["sel"],
               fg=C["text"], font=FONT, padx=8, pady=3).pack(side="right")

        # Qualidade
        r2 = row("Qualidade MP3")
        self.quality_var = tk.StringVar(value=self.cfg.get("quality", "320"))
        ttk.Combobox(r2, textvariable=self.quality_var,
                     values=["128", "192", "256", "320"],
                     state="readonly", width=8, font=FONT).pack(side="left", padx=4)
        mk_label(r2, "kbps", color=C["muted"], font=FONT_SM,
                 bg=C["card"]).pack(side="left", padx=(2, 16))

        # Template nome
        mk_label(r2, "Nome do arquivo", color=C["muted"],
                 font=FONT_SM, bg=C["card"]).pack(side="left")
        self.tpl_var = tk.StringVar(
            value=self.cfg.get("filename_template", "%(playlist_index)s. %(title)s"))
        mk_entry(r2, textvariable=self.tpl_var, width=24).pack(
            side="left", padx=4)

        # Cookies.txt
        r3 = row("cookies.txt")
        self.cookies_var = tk.StringVar(value=self.cfg.get("cookies_file", ""))
        self.cookies_entry = mk_entry(r3, textvariable=self.cookies_var, width=34)
        self.cookies_entry.pack(side="left", fill="x", expand=True, padx=(4, 4))
        mk_btn(r3, "📄", self._choose_cookies,
               bg=C["border"], hover=C["sel"],
               fg=C["text"], font=FONT, padx=8, pady=3).pack(side="right")

        mk_label(cfg_card,
                 "  ℹ  Exporte o cookies.txt com a extensão \"Get cookies.txt LOCALLY\" no Chrome (logado no YouTube).",
                 color=C["muted"], font=("Consolas", 8),
                 bg=C["card"]).pack(fill="x", padx=12, pady=(0, 8))

        # ── Fila
        section(p, "Fila de Downloads")
        q_card = card(p)
        q_card.pack(fill="x", pady=(3, 8))

        sb = ttk.Scrollbar(q_card, orient="vertical")
        sb.pack(side="right", fill="y")
        self.queue_lb = tk.Listbox(
            q_card, bg=C["card"], fg=C["text"],
            selectbackground=C["accent"], selectforeground=C["text"],
            font=FONT_SM, bd=0, relief="flat", height=8,
            activestyle="none", yscrollcommand=sb.set)
        self.queue_lb.pack(fill="both", expand=True, padx=4, pady=4)
        sb.configure(command=self.queue_lb.yview)
        self._queue_empty()

        # Botões
        btn_row = mk_frame(p)
        btn_row.pack(fill="x", pady=(0, 8))

        self.dl_btn = mk_btn(btn_row, "⬇  BAIXAR TUDO", self._start,
                             bg=C["accent"])
        self.dl_btn.pack(side="left", fill="x", expand=True,
                         padx=(0, 6), ipady=7)

        mk_btn(btn_row, "✕ Limpar", self._clear_queue,
               bg=C["border"], hover=C["sel"],
               fg=C["muted"], font=FONT, padx=12).pack(side="right", ipady=7)

        # Progresso
        self.prog_var = tk.DoubleVar(value=0)
        ttk.Progressbar(p, variable=self.prog_var,
                        maximum=100).pack(fill="x", pady=(0, 2))
        self.prog_lbl = tk.StringVar(value="")
        mk_label(p, color=C["muted"], font=FONT_SM).configure(
            textvariable=self.prog_lbl)
        tk.Label(p, textvariable=self.prog_lbl,
                 font=FONT_SM, fg=C["muted"],
                 bg=C["bg"], anchor="w").pack(fill="x")

    def _build_right(self, p):
        section(p, "Log de Atividade")
        log_card = card(p)
        log_card.pack(fill="both", expand=True, pady=(3, 6))

        sb = ttk.Scrollbar(log_card, orient="vertical")
        sb.pack(side="right", fill="y")
        self.log_box = tk.Text(
            log_card, bg=C["card"], fg=C["text"],
            font=("Consolas", 9), bd=0, relief="flat",
            state="disabled", wrap="word",
            yscrollcommand=sb.set, insertbackground=C["text"])
        self.log_box.pack(fill="both", expand=True, padx=4, pady=4)
        sb.configure(command=self.log_box.yview)

        self.log_box.tag_config("ok",  foreground=C["success"])
        self.log_box.tag_config("err", foreground=C["error"])
        self.log_box.tag_config("inf", foreground=C["warning"])
        self.log_box.tag_config("dim", foreground=C["muted"])
        self.log_box.tag_config("ts",  foreground="#444444")

        mk_btn(p, "Limpar Log", self._clear_log,
               bg=C["border"], hover=C["sel"],
               fg=C["muted"], font=FONT_SM, padx=12).pack(fill="x", ipady=4)

    # ── Verificação de dependências ───────────────────────────────────────────
    def _check_deps(self):
        def dot(name, ok):
            color = C["success"] if ok else C["error"]
            sym   = "●" if ok else "●"
            f = mk_frame(self._dep_frame, bg=C["surface"])
            f.pack(side="left", padx=6)
            tk.Label(f, text=sym, fg=color,
                     bg=C["surface"], font=("Consolas", 9)).pack(side="left")
            tk.Label(f, text=name, fg=C["muted"],
                     bg=C["surface"], font=("Consolas", 8)).pack(side="left")

        has_ffmpeg = shutil.which("ffmpeg") is not None
        has_deno   = shutil.which("deno")   is not None

        dot("FFmpeg", has_ffmpeg)
        dot("Deno",   has_deno)

        if not has_ffmpeg:
            self.after(500, lambda: messagebox.showwarning(
                "FFmpeg não encontrado",
                "Instale o FFmpeg para converter para MP3:\n\n"
                "  winget install ffmpeg\n\n"
                "Depois reinicie o script."))
        if not has_deno:
            self.after(800, lambda: messagebox.showwarning(
                "Deno não encontrado",
                "O Deno é necessário para resolver os desafios do YouTube:\n\n"
                "  winget install DenoLand.Deno\n\n"
                "Depois reinicie o script."))

    # ── Ações ─────────────────────────────────────────────────────────────────
    def _choose_dir(self):
        d = filedialog.askdirectory(title="Pasta de saída")
        if d:
            self.dir_var.set(d)

    def _choose_cookies(self):
        f = filedialog.askopenfilename(
            title="Selecionar cookies.txt",
            filetypes=[("Text", "*.txt"), ("Todos", "*.*")])
        if f:
            self.cookies_var.set(f)

    def _queue_empty(self):
        self.queue_lb.delete(0, "end")
        self.queue_lb.insert("end", "  — Fila vazia. Cole uma URL acima e clique em Adicionar. —")
        self.queue_lb.itemconfig(0, fg=C["muted"])

    def _refresh_queue(self):
        self.queue_lb.delete(0, "end")
        if not self.queue:
            self._queue_empty()
            return
        icons = {"pendente": "○", "baixando": "◉", "concluído": "✓", "erro": "✗"}
        colors = {"pendente": C["muted"], "baixando": C["warning"],
                  "concluído": C["success"], "erro": C["error"]}
        for item in self.queue:
            st    = item["status"]
            label = item.get("label") or item["url"]
            short = label[:62] + ("…" if len(label) > 62 else "")
            self.queue_lb.insert("end", f"  {icons.get(st,'○')}  {short}")
            self.queue_lb.itemconfig("end", fg=colors.get(st, C["text"]))

    def _add_url(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL vazia", "Cole uma URL do YouTube.")
            return
        if "youtube.com" not in url and "youtu.be" not in url:
            messagebox.showwarning("URL inválida", "Use uma URL do YouTube.")
            return
        # Evita duplicatas
        if any(q["url"] == url for q in self.queue):
            messagebox.showinfo("Já na fila", "Essa URL já está na fila.")
            return
        self.queue.append({"url": url, "label": url, "status": "pendente"})
        self.url_var.set("")
        self._refresh_queue()
        self._log(f"+ {url[:72]}", "inf")
        # Tenta buscar o título em background
        threading.Thread(target=self._fetch_title,
                         args=(url, len(self.queue)-1), daemon=True).start()

    def _fetch_title(self, url, idx):
        """Busca título da playlist/vídeo — cada URL vira uma pasta própria."""
        try:
            opts = {"quiet": True, "no_warnings": True,
                    "skip_download": True, "extract_flat": "in_playlist"}
            cookies = self.cookies_var.get().strip()
            if cookies and Path(cookies).exists():
                opts["cookiefile"] = cookies
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    # Título da playlist ou do vídeo único
                    title    = info.get("title") or info.get("playlist_title") or ""
                    uploader = (info.get("uploader")
                                or info.get("channel")
                                or info.get("playlist_uploader")
                                or "")
                    count = info.get("playlist_count") or len(info.get("entries", [])) or ""
                    # Nome da pasta = título da playlist (cada link = uma pasta)
                    folder_name = title or uploader or "Playlist"
                    label = title
                    if uploader:
                        label = f"{uploader}  —  {title}" if title else uploader
                    if count:
                        label += f"  [{count} faixas]"
                    if idx < len(self.queue):
                        self.queue[idx]["label"]       = label or url
                        self.queue[idx]["folder_name"] = folder_name
                        self.after(0, self._refresh_queue)
        except Exception:
            pass

    def _clear_queue(self):
        if self.is_downloading:
            messagebox.showwarning("Em andamento", "Aguarde o download terminar.")
            return
        self.queue.clear()
        self._refresh_queue()
        self.prog_var.set(0)
        self.prog_lbl.set("")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _log(self, msg: str, tag: str = ""):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{ts}] ", "ts")
        self.log_box.insert("end", msg + "\n", tag or "")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_status(self, txt: str):
        self.status_var.set(txt)

    # ── Download ──────────────────────────────────────────────────────────────
    def _start(self):
        if self.is_downloading:
            return
        pending = [q for q in self.queue if q["status"] == "pendente"]
        if not pending:
            messagebox.showwarning("Fila vazia", "Adicione URLs antes de baixar.")
            return

        # Valida cookies
        cookies = self.cookies_var.get().strip()
        if not cookies or not Path(cookies).exists():
            if not messagebox.askyesno(
                "cookies.txt não configurado",
                "Nenhum arquivo cookies.txt válido foi selecionado.\n\n"
                "Sem cookies, o YouTube pode bloquear os downloads.\n\n"
                "Deseja continuar mesmo assim?"):
                return

        # Salva config
        self.cfg.update({
            "output_dir":        self.dir_var.get(),
            "quality":           self.quality_var.get(),
            "cookies_file":      cookies,
            "filename_template": self.tpl_var.get(),
        })
        save_config(self.cfg)

        out = self.dir_var.get().strip()
        Path(out).mkdir(parents=True, exist_ok=True)

        self.is_downloading = True
        self._stop_flag     = False
        self.dl_btn.configure(text="⏹  Parar", command=self._stop,
                              bg="#555555")

        threading.Thread(target=self._worker, args=(out,), daemon=True).start()

    def _stop(self):
        self._stop_flag = True
        self._log("⚠ Parando após o item atual…", "inf")
        self._set_status("Parando…")

    def _worker(self, out: str):
        pending = [i for i, q in enumerate(self.queue)
                   if q["status"] == "pendente"]
        total = len(pending)

        for step, idx in enumerate(pending):
            if self._stop_flag:
                break

            item = self.queue[idx]
            item["status"] = "baixando"
            self.after(0, self._refresh_queue)

            label = item.get("label") or item["url"]
            self._log(f"↓ [{step+1}/{total}] {label[:65]}", "inf")
            self._set_status(f"Baixando {step+1} de {total}…")
            self.after(0, lambda v=(step/total)*100: self.prog_var.set(v))

            try:
                folder_name = item.get("folder_name", "")
                self._yt_download(item["url"], out, folder_name)
                item["status"] = "concluído"
                self._log("✓ Concluído!", "ok")
            except Exception as exc:
                item["status"] = "erro"
                self._log(f"✗ Erro: {exc}", "err")

            self.after(0, self._refresh_queue)
            pct = ((step+1)/total)*100
            self.after(0, lambda v=pct: self.prog_var.set(v))
            self.after(0, lambda s=step+1, t=total:
                       self.prog_lbl.set(f"{s} / {t} itens concluídos"))

        self.is_downloading = False
        self._stop_flag     = False
        self.after(0, lambda: self.dl_btn.configure(
            text="⬇  BAIXAR TUDO", command=self._start, bg=C["accent"]))
        self._log("═══ Sessão finalizada ═══", "ok")
        self._set_status("Pronto.")
        self.after(0, lambda: self.prog_var.set(100))

    @staticmethod
    def _safe_folder(name: str) -> str:
        """Remove caracteres inválidos para nome de pasta no Windows."""
        import re
        name = re.sub(r'[\/:*?"<>|]', '', name).strip('. ')
        return name[:80] or "YouTube MP3"

    def _yt_download(self, url: str, out: str, folder_name: str = ""):
        quality  = self.quality_var.get()
        template = self.tpl_var.get() or "%(title)s"
        cookies  = self.cookies_var.get().strip()
        has_ffmpeg = shutil.which("ffmpeg") is not None

        # Cada playlist/URL tem sua própria pasta
        # folder_name vem do _fetch_title; se ainda não buscou, usa %(playlist_title)s
        if folder_name:
            safe = self._safe_folder(folder_name)
        else:
            # Descobre em tempo real via yt-dlp (primeiro item da playlist)
            try:
                probe_opts = {"quiet": True, "no_warnings": True,
                              "skip_download": True, "extract_flat": "in_playlist",
                              "playlist_items": "1"}
                if cookies and Path(cookies).exists():
                    probe_opts["cookiefile"] = cookies
                with yt_dlp.YoutubeDL(probe_opts) as ydl2:
                    info2 = ydl2.extract_info(url, download=False)
                    raw = (info2.get("title") or info2.get("playlist_title")
                           or info2.get("uploader") or "Playlist") if info2 else "Playlist"
                    safe = self._safe_folder(raw)
            except Exception:
                safe = "Playlist"

        out = os.path.join(out, safe)
        Path(out).mkdir(parents=True, exist_ok=True)
        self._log(f"  📁 Pasta: {safe}", "dim")

        postprocessors = []
        if has_ffmpeg:
            postprocessors = [
                {"key": "FFmpegExtractAudio",
                 "preferredcodec": "mp3",
                 "preferredquality": quality},
                {"key": "FFmpegMetadata", "add_metadata": True},
                {"key": "EmbedThumbnail"},
            ]
        else:
            self._log("⚠ FFmpeg não encontrado — baixando sem converter.", "err")

        ydl_opts = {
            "format":           "bestaudio/best",
            "outtmpl":          os.path.join(out, f"{template}.%(ext)s"),
            "postprocessors":   postprocessors,
            "writethumbnail":   has_ffmpeg,
            "ignoreerrors":     True,
            "retries":          10,
            "fragment_retries": 10,
            "quiet":            False,
            "no_warnings":      False,
            "progress_hooks":   [self._prog_hook],
            "postprocessor_hooks": [self._pp_hook],
            "noprogress":       True,
            "logger":           self._Logger(self),
            # ── Chave: usa Deno para resolver desafios JS do YouTube ──
            "extractor_args": {
                "youtube": {
                    "player_client": ["web"],
                }
            },
        }

        # Adiciona --remote-components e --js-runtimes via yt-dlp params
        # (equivalente a passar na linha de comando)
        if shutil.which("deno"):
            ydl_opts["jsinterp_runtime"] = "deno"

        if cookies and Path(cookies).exists():
            ydl_opts["cookiefile"] = cookies
            self._log(f"  🍪 cookies: {Path(cookies).name}", "dim")
        else:
            self._log("  ⚠ Sem cookies.txt — pode falhar.", "inf")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    # ── Hooks / Logger ────────────────────────────────────────────────────────
    class _Logger:
        def __init__(self, app): self.app = app
        def debug(self, msg):
            if "[debug]" in msg: return
            self.app._log(f"  {msg[:110]}", "dim")
        def info(self, msg):
            self.app._log(f"  {msg[:110]}", "dim")
        def warning(self, msg):
            self.app._log(f"  ⚠ {msg[:110]}", "inf")
        def error(self, msg):
            self.app._log(f"  ✗ {msg[:110]}", "err")

    def _prog_hook(self, d):
        if d["status"] == "downloading":
            fn    = Path(d.get("filename", "")).stem[:35]
            pct   = d.get("_percent_str", "").strip()
            speed = d.get("_speed_str",   "").strip()
            eta   = d.get("_eta_str",     "").strip()
            self.after(0, lambda: self._set_status(
                f"{fn:<35}  {pct:>6}  {speed:>12}  ETA {eta}"))
        elif d["status"] == "finished":
            fn = Path(d.get("filename", "arquivo")).name
            self._log(f"  ♪ Convertendo: {fn[:60]}", "inf")

    def _pp_hook(self, d):
        if d["status"] == "finished":
            info = d.get("info_dict", {})
            fp   = info.get("filepath") or info.get("filename", "")
            if fp:
                self._log(f"  ✓ Salvo: {Path(fp).name[:65]}", "ok")

# ─── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
