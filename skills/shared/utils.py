import os
import re
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import ssl
import tempfile

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# TLS & Corporate Proxy Configuration
# ---------------------------------------------------------------------------
# Defaults to strict verified TLS.
# - QA_KIT_TLS_RELAX_STRICT=1: keeps certificate verification but clears
#   VERIFY_X509_STRICT (Python 3.13+ default). Fixes "Basic Constraints of CA
#   cert not marked critical" behind proxies/antivirus that re-sign certs.
# - QA_KIT_INSECURE_TLS=1: disables verification entirely (last resort).
def get_ssl_context() -> ssl.SSLContext:
    if os.environ.get("QA_KIT_INSECURE_TLS", "0") == "1":
        return ssl._create_unverified_context()
    ctx = ssl.create_default_context()
    bundle = os.environ.get("QA_KIT_CA_BUNDLE")
    if bundle and os.path.exists(bundle):
        ctx.load_verify_locations(cafile=bundle)
    if os.environ.get("QA_KIT_TLS_RELAX_STRICT", "0") == "1" and hasattr(ssl, "VERIFY_X509_STRICT"):
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx

if os.environ.get("QA_KIT_INSECURE_TLS", "0") == "1":
    ssl._create_default_https_context = ssl._create_unverified_context
elif os.environ.get("QA_KIT_TLS_RELAX_STRICT", "0") == "1":
    ssl._create_default_https_context = get_ssl_context

# ---------------------------------------------------------------------------
# Dynamic Workspace and Plugin Path Resolution (Cross-Platform & Portable)
# ---------------------------------------------------------------------------
UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(os.path.dirname(UTILS_DIR))

def get_token_cache_dir() -> str:
    """Returns user-level local cache directory to prevent token leaks in repo."""
    cache_dir = os.environ.get("QA_KIT_CACHE_DIR")
    if not cache_dir:
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
        else:
            base = os.path.expanduser("~/.cache")
        cache_dir = os.path.join(base, "iafactory-qa-kit")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def get_token_cache_path() -> str:
    return os.path.join(get_token_cache_dir(), "gcloud_token.json")

DEFAULT_PRODUCT_REPOS = ["ai-factory-core", "ai-factory-agents", "ai-factory-frontend", "ai-factory-platform"]

def _read_env_key(key: str) -> str:
    """Reads a single key: real environment first, then .env files. Files are
    <plugin>/.env, <cwd>/.env and <WORKSPACE_ROOT>/.env; later ones win, like
    load_env_variables(). When the kit is installed as a Claude Code plugin the
    plugin folder is a cache replaced on every update, so the workspace .env is
    the durable place for these settings."""
    if os.environ.get(key):
        return os.environ[key]
    files = [os.path.join(PLUGIN_ROOT, ".env"), os.path.join(os.getcwd(), ".env")]
    ws = globals().get("WORKSPACE_ROOT")
    if ws:
        files.append(os.path.join(ws, ".env"))
    value = ""
    for fpath in dict.fromkeys(files):
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
    return value

def _apply_ca_bundle():
    """QA_KIT_CA_BUNDLE: PEM with the public CAs plus a local interception CA
    (antivirus/corporate proxy). Python requests trust it via get_ssl_context();
    gcloud subprocesses (API calls, SSH and IAP tunnels) via
    CLOUDSDK_CORE_CUSTOM_CA_CERTS_FILE, set only for this process tree.
    Build it with skills/qa-preflight/scripts/build_ca_bundle.py."""
    for key in ("QA_KIT_CA_BUNDLE", "QA_KIT_TLS_RELAX_STRICT"):
        val = _read_env_key(key)
        if val:
            os.environ.setdefault(key, val)
    bundle = os.environ.get("QA_KIT_CA_BUNDLE")
    if bundle and os.path.exists(bundle):
        os.environ.setdefault("CLOUDSDK_CORE_CUSTOM_CA_CERTS_FILE", bundle)
    if os.environ.get("QA_KIT_INSECURE_TLS") != "1" and (bundle or os.environ.get("QA_KIT_TLS_RELAX_STRICT") == "1"):
        ssl._create_default_https_context = get_ssl_context

_apply_ca_bundle()

def get_product_repos() -> list[str]:
    """Product repo folders, relative to WORKSPACE_ROOT (QA_KIT_REPOS=a,b,c; subfolders allowed: ia-factory/a)."""
    raw = _read_env_key("QA_KIT_REPOS")
    repos = [r.strip() for r in raw.split(",") if r.strip()] if raw else []
    return repos or DEFAULT_PRODUCT_REPOS

# ---------------------------------------------------------------------------
# Remote VM environments (dev / qa / team-devs ...)
# ---------------------------------------------------------------------------
# Team-shared definitions live in <KIT>/environments.json; personal overrides in
# <KIT>/environments.local.json (gitignored). Each environment gets its own
# local port offset so several IAP tunnels can run in parallel.
DEFAULT_ENVIRONMENTS = {
    "dev": {
        "instance": "iafactory-dev",
        "zone": "us-central1-a",
        "project": "apiux-iafactory-nonprod",
        "port_offset": 0,
        "api_url": "https://aifactory-dev.api-ux.dev",
        "remote_repo_root": "/opt/ai-factory",
    }
}

def get_environments() -> dict:
    envs = {k: dict(v) for k, v in DEFAULT_ENVIRONMENTS.items()}
    for fname in ("environments.json", "environments.local.json"):
        fpath = os.path.join(PLUGIN_ROOT, fname)
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Warning: no se pudo leer {fname} ({e})", file=sys.stderr)
            continue
        for name, cfg in (data.get("environments") or {}).items():
            envs.setdefault(name, {}).update({k: v for k, v in cfg.items() if not k.startswith("_")})
    return envs

def get_default_environment_name() -> str:
    return _read_env_key("QA_KIT_ENV") or "dev"

def resolve_environment(name: str = None) -> dict:
    """Returns the environment config (with 'name'). Legacy GCP_INSTANCE /
    GCP_ZONE / GCP_PROJECT env vars only override the default environment, so
    an explicit --env never silently points at another VM.
    Raises ValueError for unknown or incomplete environments."""
    envs = get_environments()
    default_name = get_default_environment_name()
    name = name or default_name
    if name not in envs:
        raise ValueError(f"Entorno '{name}' no definido. Disponibles: {', '.join(sorted(envs))}. "
                         f"Agrégalo en environments.json o environments.local.json del kit.")
    cfg = dict(envs[name])
    cfg["name"] = name
    if name == default_name:
        for key, var in (("instance", "GCP_INSTANCE"), ("zone", "GCP_ZONE"), ("project", "GCP_PROJECT")):
            if os.environ.get(var):
                cfg[key] = os.environ[var]
    missing = [k for k in ("instance", "zone", "project") if not cfg.get(k)]
    if missing:
        raise ValueError(f"Entorno '{name}' incompleto: falta {', '.join(missing)} en environments.json.")
    cfg.setdefault("port_offset", 0)
    cfg.setdefault("remote_repo_root", "/opt/ai-factory")
    return cfg

def iap_extra_args() -> list[str]:
    """Opt-in workaround for antivirus/proxies that intercept the IAP websocket
    (QA_KIT_IAP_INSECURE_WS=1). Disables cert checks on that websocket only."""
    if _read_env_key("QA_KIT_IAP_INSECURE_WS") == "1":
        return ["--iap-tunnel-insecure-disable-websocket-cert-check"]
    return []

def _is_workspace_root(path: str) -> bool:
    # The kit itself is never the workspace, even if an earlier run left a Reportes/ inside it.
    if os.path.realpath(path) == os.path.realpath(PLUGIN_ROOT):
        return False
    if os.path.exists(os.path.join(path, ".qa-kit-root")) or \
       os.path.exists(os.path.join(path, "MANIFIESTO_WORKSPACE.md")) or \
       os.path.exists(os.path.join(path, "Reportes")):
        return True
    return any(os.path.isdir(os.path.join(path, r)) for r in get_product_repos())

def detect_workspace_root() -> str:
    """Locates the workspace root. Priority: WORKSPACE_ROOT env/.env, then upward
    search (from CWD, then from the plugin) for a '.qa-kit-root' marker,
    'Reportes/', MANIFIESTO_WORKSPACE.md or any configured product repo folder."""
    env_root = _read_env_key("WORKSPACE_ROOT")
    if env_root and os.path.exists(env_root):
        return os.path.abspath(env_root)

    for start in (os.getcwd(), os.path.dirname(PLUGIN_ROOT)):
        current = os.path.abspath(start)
        for _ in range(7):
            if _is_workspace_root(current):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

    return os.path.abspath(os.getcwd())

WORKSPACE_ROOT = detect_workspace_root()

# Constants
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "1Ddc43mRVFNtSCVNWwSxOi_IZZXHof_LJxel6qVqJlxM")
SHEET_NAME = os.environ.get("SHEET_NAME", "Ai-Factory")
REPORTS_DIR = os.path.join(WORKSPACE_ROOT, "Reportes")
CONFIG_FILE = os.path.join(UTILS_DIR, "config.json")
ENV_FILE = os.path.join(WORKSPACE_ROOT, ".env")
OBSIDIAN_VAULT_DIR = os.path.join(WORKSPACE_ROOT, "docs", "vault")
# Google Sheets accepts 50,000 characters per cell. Full reports go in COMENTARIO QA.
COMMENT_MAX_CHARS = 45000
SEVERITIES = {"critica": "Critica", "crítica": "Critica", "alta": "Alta", "media": "Media", "baja": "Baja"}


def normalize_severity(value: str) -> str:
    """'Crítica' -> 'Critica' (the sheet's spelling). Raises ValueError for anything else."""
    key = (value or "").strip().lower()
    if key not in SEVERITIES:
        raise ValueError(f"Gravedad '{value}' no válida. Usa Critica, Alta, Media o Baja.")
    return SEVERITIES[key]


def truncate_comment(text: str) -> str:
    if len(text) <= COMMENT_MAX_CHARS:
        return text
    mark = "\n\n[... recortado: el reporte completo está en el archivo local de Reportes/]"
    return text[:COMMENT_MAX_CHARS - len(mark)] + mark

# ---------------------------------------------------------------------------
# Publish gate: a real write needs the code printed by the matching --dry-run.
# The code is a hash of exactly what will be written, so a dry-run of other
# content (or content edited after the dry-run) does not unlock the write.
# ---------------------------------------------------------------------------
CONFIRM_EXIT_CODE = 4


def confirm_code(kind: str, parts: list) -> str:
    import hashlib
    h = hashlib.sha256(kind.encode("utf-8"))
    for p in parts:
        h.update(b"\x1f")
        h.update(str(p if p is not None else "").encode("utf-8"))
    return h.hexdigest()[:8]


def file_digest(path: str) -> str:
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def pop_option(argv: list, name: str) -> tuple:
    """Removes `name <value>` from argv. Returns (value or None, remaining argv)."""
    rest, value, i = [], None, 0
    while i < len(argv):
        if argv[i] == name and i + 1 < len(argv):
            value = argv[i + 1]
            i += 2
            continue
        rest.append(argv[i])
        i += 1
    return value, rest


def require_confirm(kind: str, parts: list, given: str) -> None:
    """Exits with CONFIRM_EXIT_CODE unless `given` matches the dry-run code for this content."""
    expected = confirm_code(kind, parts)
    if given == expected:
        return
    reason = "falta --confirm" if not given else "el código no coincide con este contenido"
    print(f"[BLOQUEADO] Publicación sin dry-run válido ({reason}). Ejecuta primero el mismo comando con "
          f"--dry-run, muéstrale el resultado al usuario y, con su confirmación, repítelo con "
          f"--confirm <código que imprime el dry-run>.", file=sys.stderr)
    sys.exit(CONFIRM_EXIT_CODE)


# ---------------------------------------------------------------------------
# Human gate: new tickets, closures and rejections are confirmed by a person in
# an interactive terminal, one ticket at a time. Assistants run commands without
# a terminal (stdin is not a TTY), so they cannot answer; the script refuses
# immediately instead of hanging. It stops mistakes and hurried automation, not
# someone who deliberately works around it.
# ---------------------------------------------------------------------------
HUMAN_GATE_EXIT_CODE = 5
PUBLISH_LOG = os.path.join(REPORTS_DIR, ".publicaciones.log")


HUMAN_GATE_TIMEOUT_S = 180
# Variables that AI coding assistants set in the processes they launch. An assistant's
# process can still own a console, so "stdin is a TTY" alone is not enough to know that a
# person is typing (tested: under the Claude desktop app the check passed and the script
# waited on a console nobody could see).
AGENT_ENV_MARKERS = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "AI_AGENT")


def running_under_agent() -> str:
    return next((k for k in AGENT_ENV_MARKERS if os.environ.get(k)), "")


def _read_console_line(prompt: str, timeout: int = HUMAN_GATE_TIMEOUT_S) -> str:
    """Reads one line with input() (works in every console, including Windows Terminal,
    PowerShell, CMD and Git Bash). The timeout runs in a thread so an unattended console
    does not hang forever. Returns '' on timeout or EOF."""
    import threading
    got = []

    def ask():
        try:
            got.append(input(prompt))
        except (EOFError, KeyboardInterrupt, OSError):
            got.append("")

    t = threading.Thread(target=ask, daemon=True)
    t.start()
    t.join(timeout)
    return got[0].strip() if got else ""


def log_publication(action: str, defect_id: str, detail: str = "") -> None:
    try:
        os.makedirs(os.path.dirname(PUBLISH_LOG), exist_ok=True)
        import datetime
        with open(PUBLISH_LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\t{get_user_name()}\t{action}\t"
                    f"{defect_id}\t{detail}\n")
    except OSError:
        pass


def require_human_confirmation(action: str, defect_id: str, summary: list) -> None:
    """Shows what will be written and asks the person to type the defect ID.

    Exits with HUMAN_GATE_EXIT_CODE when there is no interactive terminal or the
    typed ID does not match. On success, appends the decision to Reportes/.publicaciones.log.
    """
    try:
        interactive = sys.stdin is not None and sys.stdin.isatty()
    except (AttributeError, ValueError):
        interactive = False
    if not interactive or running_under_agent():
        print(f"[REQUIERE A UNA PERSONA] '{action}' de {defect_id} se confirma en una terminal interactiva. "
              f"Copia este mismo comando y ejecútalo tú en una terminal propia (PowerShell, CMD o bash abierta por ti, "
              f"fuera del asistente), desde la raíz del workspace: "
              f"verás qué se publica y tendrás que escribir {defect_id} para confirmar. El asistente no puede hacer este paso.",
              file=sys.stderr)
        sys.exit(HUMAN_GATE_EXIT_CODE)
    lines = [f"\n=== Confirmación humana: {action} ==="] + [f"  {s}" for s in summary] + [""]
    print("\n".join(lines))
    typed = _read_console_line(f"Escribe {defect_id} para confirmar (Enter vacío cancela): ")
    if typed.strip().upper() != defect_id.strip().upper():
        print(f"Cancelado: no se escribió el ID correcto (o pasaron {HUMAN_GATE_TIMEOUT_S} s). No se publicó nada.",
              file=sys.stderr)
        sys.exit(HUMAN_GATE_EXIT_CODE)
    log_publication(action, defect_id, " | ".join(s for s in summary if s)[:300])


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def get_git_user_name() -> str:
    """Attempts to extract user.name from git configuration."""
    try:
        cmd = ["git", "config", "user.name"]
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=3).strip()
    except Exception:
        return ""

def set_configured_user_name(name: str):
    """Saves configured QA user name in config and environment."""
    cfg = load_config()
    cfg["user_name"] = name.strip()
    save_config(cfg)
    os.environ["USER_NAME"] = name.strip()

def get_user_name() -> str:
    load_env_variables()
    env_name = os.environ.get("USER_NAME", "").strip()
    if env_name and env_name not in ("Tu Nombre y Apellido", "your_name"):
        return env_name

    config = load_config()
    cfg_name = config.get("user_name", "").strip()
    if cfg_name and cfg_name not in ("Alonso Salas (IA)", "Tu Nombre y Apellido"):
        return cfg_name

    git_name = get_git_user_name()

    # First-time interactive prompt
    if sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
        print("\n" + "=" * 55)
        print("  👤 Configuración Inicial: Identidad de Reporte QA")
        print("=" * 55)
        prompt = f"Ingresa tu nombre y apellido [{git_name}]: " if git_name else "Ingresa tu nombre y apellido (ej. Juan Pérez): "
        try:
            entered = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            entered = ""
        resolved = entered or git_name
        if resolved:
            set_configured_user_name(resolved)
            print(f"✅ Identidad de reporte guardada: {resolved}\n")
            return resolved

    # Non-interactive fallback to git user.name
    if git_name:
        set_configured_user_name(git_name)
        return git_name

    return "QA Automation"

def load_env_variables():
    for fpath in (os.path.join(PLUGIN_ROOT, ".env"), ENV_FILE):
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        val_clean = val.strip().strip('"').strip("'")
                        if val_clean and not val_clean.startswith("your_") and not val_clean.startswith("ya29.pega"):
                            os.environ[key.strip()] = val_clean

def append_to_env(key: str, value: str):
    target = ENV_FILE if os.path.exists(ENV_FILE) else os.path.join(PLUGIN_ROOT, ".env")
    with open(target, "a", encoding="utf-8") as f:
        f.write(f"\n{key}={value}\n")
    os.environ[key] = value

# ---------------------------------------------------------------------------
# Google Sheets access token. Sources, in order:
#   1. SHEETS_ACCESS_TOKEN in the environment or .env: a token pasted from the
#      Google OAuth Playground (scope spreadsheets). Lasts 60 minutes; when it
#      expires the person pastes a new one. Nothing renews it automatically.
#   2. SHEETS_CLIENT_ID + SHEETS_CLIENT_SECRET + SHEETS_REFRESH_TOKEN: an OAuth
#      client of your own; the kit renews the access token by itself.
#   3. gcloud auth print-access-token (needs `gcloud auth login --enable-gdrive-access`).
# GCLOUD_ACCESS_TOKEN is accepted as an alias of SHEETS_ACCESS_TOKEN.
# ---------------------------------------------------------------------------
SHEETS_AUTH_EXIT_CODE = 6
SHEETS_TOKEN_HELP = (
    "Pega un token nuevo en el .env del workspace como SHEETS_ACCESS_TOKEN=ya29... "
    "(Google OAuth Playground, scope https://www.googleapis.com/auth/spreadsheets; dura 60 minutos). "
    "Alternativas: SHEETS_CLIENT_ID/SHEETS_CLIENT_SECRET/SHEETS_REFRESH_TOKEN para renovación automática, "
    "o una sesión de gcloud (gcloud auth login --enable-gdrive-access)."
)


class SheetsAuthError(RuntimeError):
    """No usable token for Google Sheets (missing or expired)."""


_TOKEN = {"value": None, "source": None, "ts": 0}


def _mem(token: str, source: str) -> str:
    _TOKEN.update(value=token, source=source, ts=time.time())
    return token


def invalidate_gcloud_token():
    """Drops the in-memory and file token caches (e.g. after a 401)."""
    _TOKEN.update(value=None, source=None, ts=0)
    try:
        os.remove(get_token_cache_path())
    except OSError:
        pass


def _refresh_with_oauth_client() -> str:
    cid, secret, rtok = (_read_env_key(k) for k in ("SHEETS_CLIENT_ID", "SHEETS_CLIENT_SECRET", "SHEETS_REFRESH_TOKEN"))
    if not (cid and secret and rtok):
        return ""
    body = urllib.parse.urlencode({"client_id": cid, "client_secret": secret, "refresh_token": rtok,
                                   "grant_type": "refresh_token"}).encode("ascii")
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, context=get_ssl_context(), timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8")).get("access_token", "")
    except Exception as e:
        print(f"Warning: no se pudo renovar el token con SHEETS_REFRESH_TOKEN ({e})", file=sys.stderr)
        return ""


def _gcloud_access_token() -> str:
    token_json_path = get_token_cache_path()
    now = time.time()
    if os.path.exists(token_json_path):
        try:
            if now - os.path.getmtime(token_json_path) < 2700:  # 45 minutes
                with open(token_json_path, "r", encoding="utf-8") as f:
                    tok = json.load(f).get("access_token")
                if tok:
                    return tok
        except Exception:
            pass
    try:
        out = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True, stderr=subprocess.PIPE,
                                      shell=(sys.platform == "win32"), timeout=15).strip()
    except Exception:
        return ""
    if not out or out.startswith("ERROR"):
        return ""
    try:
        with open(token_json_path, "w", encoding="utf-8") as f:
            json.dump({"access_token": out, "timestamp": now}, f)
    except Exception:
        pass
    return out


def get_sheets_token() -> str:
    """Access token for the Sheets API. Raises SheetsAuthError when no source works."""
    if _TOKEN["value"] and time.time() - _TOKEN["ts"] < 1800:
        return _TOKEN["value"]
    pasted = _read_env_key("SHEETS_ACCESS_TOKEN") or _read_env_key("GCLOUD_ACCESS_TOKEN")
    if pasted:
        return _mem(pasted, "pegado")
    refreshed = _refresh_with_oauth_client()
    if refreshed:
        return _mem(refreshed, "refresh")
    tok = _gcloud_access_token()
    if tok:
        return _mem(tok, "gcloud")
    raise SheetsAuthError("Sin token para Google Sheets. " + SHEETS_TOKEN_HELP)


get_gcloud_token = get_sheets_token  # legacy name


def sheets_token_source() -> str:
    """'pegado', 'refresh', 'gcloud' or '' when nothing works. Never raises."""
    try:
        get_sheets_token()
        return _TOKEN["source"] or ""
    except SheetsAuthError:
        return ""


def google_urlopen(req: urllib.request.Request, timeout: int = 20):
    """urlopen for the Sheets API. On 401: a pasted token is simply expired (the person
    must paste a new one); the other sources are refreshed once and the call retried."""
    try:
        return urllib.request.urlopen(req, context=get_ssl_context(), timeout=timeout)
    except urllib.error.HTTPError as e:
        if e.code != 401:
            raise
        if _TOKEN["source"] == "pegado":
            raise SheetsAuthError("Google respondió 401: el SHEETS_ACCESS_TOKEN pegado venció o no vale para esta "
                                  "planilla. " + SHEETS_TOKEN_HELP) from None
        invalidate_gcloud_token()
        req.add_header("Authorization", f"Bearer {get_sheets_token()}")
        return urllib.request.urlopen(req, context=get_ssl_context(), timeout=timeout)


def exit_on_auth_error(fn):
    """Decorator for CLI mains: prints the Sheets auth problem and exits with code 6."""
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except SheetsAuthError as e:
            print(f"[SIN TOKEN DE SHEETS] {e}", file=sys.stderr)
            sys.exit(SHEETS_AUTH_EXIT_CODE)
    return wrapper


_COLUMN_MAPPING_CACHE = None

def get_column_mapping() -> dict[str, str]:
    global _COLUMN_MAPPING_CACHE
    if _COLUMN_MAPPING_CACHE:
        return _COLUMN_MAPPING_CACHE

    token = get_sheets_token()
    mapping = {
        "id": "A", "nombre": "B", "agrupacion": "C", "responsable": "D", "gravedad": "E",
        "descripcion": "F", "reportada_por": "G", "fecha_inicio": "H",
        "estado": "I", "fecha_termino": "J", "cerrada_por": "K",
        "commits": "L", "id_commits": "M", "comentario_dev": "N", "comentario_qa": "O"
    }

    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{SHEET_NAME}!A1:Z1"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with google_urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            headers = data.get("values", [[]])[0]
            for idx, h in enumerate(headers):
                col_letter = chr(65 + idx) if idx < 26 else f"A{chr(65 + idx - 26)}"
                h_norm = h.strip().upper()
                if h_norm == "ID": mapping["id"] = col_letter
                elif "NOMBRE" in h_norm or "TITULO" in h_norm: mapping["nombre"] = col_letter
                elif "AGRUPACION" in h_norm or "GRUPO" in h_norm or "CLUSTER" in h_norm: mapping["agrupacion"] = col_letter
                elif "RESPONSABLE" in h_norm: mapping["responsable"] = col_letter
                elif "GRAVEDAD" in h_norm or "SEVERIDAD" in h_norm: mapping["gravedad"] = col_letter
                elif "DESCRIPCION" in h_norm: mapping["descripcion"] = col_letter
                elif "REPORTADA POR" in h_norm or "CREADA POR" in h_norm: mapping["reportada_por"] = col_letter
                elif "FECHA INICIO" in h_norm: mapping["fecha_inicio"] = col_letter
                elif h_norm == "ESTADO" or h_norm == "STATUS": mapping["estado"] = col_letter
                elif "FECHA TERMINO" in h_norm: mapping["fecha_termino"] = col_letter
                elif "RECHAZADA" in h_norm or "CERRADA POR" in h_norm: mapping["cerrada_por"] = col_letter
                elif "COMMITS REALIZADOS" in h_norm or "CANTIDAD COMMITS" in h_norm: mapping["commits"] = col_letter
                elif "ID COMMITS" in h_norm: mapping["id_commits"] = col_letter
                elif "COMENTARIO DEV" in h_norm: mapping["comentario_dev"] = col_letter
                elif "COMENTARIO QA" in h_norm or "NOTION" in h_norm: mapping["comentario_qa"] = col_letter
    except SheetsAuthError:
        raise
    except Exception as e:
        print(f"Warning: Fallback a mapeo por defecto de columnas ({e})", file=sys.stderr)

    _COLUMN_MAPPING_CACHE = mapping
    return mapping

def list_defects_from_sheets(status_filter: list[str] = None, limit: int = None) -> list[dict]:
    """
    Queries Google Sheets directly and returns structured defect objects.
    status_filter: list of strings (e.g. ['Reportada', 'En Revisión'])
    """
    token = get_sheets_token()
    mapping = get_column_mapping()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{SHEET_NAME}!A2:Z"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    results = []
    try:
        with google_urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rows = data.get("values", [])

            # Map column letters to 0-indexed column offsets
            def col_idx(col_name):
                letter = mapping.get(col_name, "A")
                return ord(letter.upper()) - ord("A") if len(letter) == 1 else 0

            for r_idx, row in enumerate(rows):
                def get_val(col_name):
                    idx = col_idx(col_name)
                    return row[idx].strip() if idx < len(row) else ""

                d_id = get_val("id")
                if not d_id or not d_id.startswith("AF-"):
                    continue

                estado = get_val("estado")
                if status_filter:
                    matched = any(f.strip().lower() in estado.lower() for f in status_filter if f.strip())
                    if not matched:
                        continue

                item = {
                    "row": r_idx + 2,
                    "id": d_id,
                    "nombre": get_val("nombre"),
                    "agrupacion": get_val("agrupacion"),
                    "responsable": get_val("responsable"),
                    "gravedad": get_val("gravedad"),
                    "descripcion": get_val("descripcion"),
                    "reportada_por": get_val("reportada_por"),
                    "fecha_inicio": get_val("fecha_inicio"),
                    "estado": estado if estado else "Reportada",
                    "fecha_termino": get_val("fecha_termino"),
                    "cerrada_por": get_val("cerrada_por"),
                    "commits": get_val("commits"),
                    "id_commits": get_val("id_commits"),
                    "comentario_dev": get_val("comentario_dev"),
                    "comentario_qa": get_val("comentario_qa")
                }
                results.append(item)
                if limit and len(results) >= limit:
                    break
    except SheetsAuthError:
        raise
    except Exception as e:
        print(f"Error consultando defectos en Google Sheets: {e}", file=sys.stderr)

    return results

def obsidian_enabled() -> bool:
    """The local Obsidian mirror is opt-in (QA_KIT_OBSIDIAN=1) so the kit never
    creates docs/vault/ in a teammate's repo unasked."""
    return _read_env_key("QA_KIT_OBSIDIAN") == "1"

def ensure_obsidian_vault():
    os.makedirs(os.path.join(OBSIDIAN_VAULT_DIR, "defectos"), exist_ok=True)

def sync_obsidian_note(defect_id: str, title: str, status: str, severity: str, evidence: str = "", tech_details: str = ""):
    """One-way local mirror of a defect (docs/vault/defectos/AF-XXX.md). Nothing
    reads it back. Each call rewrites the whole note. No-op unless opted in."""
    if not obsidian_enabled():
        return
    ensure_obsidian_vault()
    note_path = os.path.join(OBSIDIAN_VAULT_DIR, "defectos", f"{defect_id}.md")
    frontmatter = f"""---
id: {defect_id}
title: "{title}"
status: "{status}"
severity: "{severity}"
last_tested: "{os.environ.get('QA_TEST_DATE') or time.strftime('%Y-%m-%d')}"
tags:
  - qa/defect
  - status/{status.lower().replace(' ', '_')}
  - severity/{severity.lower()}
---

# {defect_id}: {title}

**Estado QA:** `{status}` | **Severidad:** `{severity}`

---

## 🧪 Evidencia Empírica y Pruebas Realizadas
{evidence if evidence else "Validación técnica y funcional completada según protocolo QA."}

---

## 🛠️ Diagnóstico y Resolución Técnica
{tech_details if tech_details else "Documentado en Comentario QA de la planilla."}
"""
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(frontmatter)

def find_sheet_row_for_defect(defect_id: str) -> int:
    token = get_sheets_token()
    mapping = get_column_mapping()
    id_col = mapping.get("id", "A")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{SHEET_NAME}!{id_col}:{id_col}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with google_urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            values = data.get("values", [])
            for r_idx, row in enumerate(values):
                if row and row[0].strip() == defect_id:
                    return r_idx + 1
    except SheetsAuthError:
        raise
    except Exception as e:
        print(f"Error buscando fila de {defect_id}: {e}", file=sys.stderr)
    return None

def get_sheet_cell(row_idx: int, key: str) -> str:
    """Reads one mapped column (e.g. 'gravedad') of a sheet row. Returns '' on failure."""
    token = get_sheets_token()
    if not row_idx:
        return ""
    col = get_column_mapping().get(key)
    if not col:
        return ""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{SHEET_NAME}!{col}{row_idx}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with google_urlopen(req, timeout=20) as resp:
            values = json.loads(resp.read().decode("utf-8")).get("values", [])
        return values[0][0].strip() if values and values[0] else ""
    except SheetsAuthError:
        raise
    except Exception as e:
        print(f"Warning: no se pudo leer {key} de la fila {row_idx} ({e})", file=sys.stderr)
        return ""

def batch_update_sheet_row(row_idx: int, updates: dict):
    token = get_sheets_token()
    mapping = get_column_mapping()
    data_payload = []
    for key, val in updates.items():
        col_letter = mapping.get(key.lower(), key.upper())
        data_payload.append({
            "range": f"{SHEET_NAME}!{col_letter}{row_idx}",
            "majorDimension": "ROWS",
            "values": [[val]]
        })
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values:batchUpdate"
    payload = {"valueInputOption": "USER_ENTERED", "data": data_payload}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST"
    )
    with google_urlopen(req, timeout=20) as resp:
        json.loads(resp.read().decode("utf-8"))

def publish_qa_outcome(
    defect_id: str,
    status: str,
    summary: str,
    report_text: str,
    evidence: str = "",
    tech_details: str = "",
    dry_run: bool = False,
) -> dict:
    """Closes or rejects a defect in the sheet: ESTADO, FECHA TERMINO, CERRADA POR and the
    full report in COMENTARIO QA. Returns None if the defect is not in the sheet.
    With dry_run it only resolves the row and returns what would be written."""
    import datetime
    user_name = get_user_name()
    row_idx = find_sheet_row_for_defect(defect_id)
    if not row_idx:
        print(f"Error: {defect_id} no está en Google Sheets; no se escribe nada.", file=sys.stderr)
        return None
    severity = get_sheet_cell(row_idx, "gravedad") or "Sin gravedad"
    current_status = get_sheet_cell(row_idx, "estado")
    today = datetime.date.today().strftime("%Y-%m-%d")
    comment = truncate_comment(report_text) if report_text else f"{summary}\n<reporte completo>"
    updates = {"estado": status, "fecha_termino": today, "cerrada_por": user_name, "comentario_qa": comment}
    if dry_run:
        return {
            "dry_run": True,
            "defect_id": defect_id,
            "sheet_row": row_idx,
            "estado_actual": current_status,
            "gravedad": severity,
            "obsidian_note": os.path.join(OBSIDIAN_VAULT_DIR, "defectos", f"{defect_id}.md") if obsidian_enabled() else None,
            "sheet_updates": updates,
        }

    batch_update_sheet_row(row_idx, updates)
    sync_obsidian_note(defect_id=defect_id, title=summary, status=status, severity=severity,
                       evidence=evidence, tech_details=tech_details)
    return {"defect_id": defect_id, "status": status, "sheet_row": row_idx, "estado_anterior": current_status,
            "user_name": user_name, "sheet_updated": True}
