import os
import re
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error
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
    """Product repo folder names, relative to WORKSPACE_ROOT (QA_KIT_REPOS=a,b,c)."""
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
DEFAULT_PARENT_PAGE_ID = os.environ.get("NOTION_PARENT_PAGE_ID", "3b8f79fc-5514-80e3-bbe0-cb9cd1ee14cc")
NOTION_PUBLIC_DOMAIN = "https://tungsten-holly-b01.notion.site/"
CONFIG_FILE = os.path.join(UTILS_DIR, "config.json")
ENV_FILE = os.path.join(WORKSPACE_ROOT, ".env")
OBSIDIAN_VAULT_DIR = os.path.join(WORKSPACE_ROOT, "docs", "vault")

_NOTION_ID_RE = re.compile(r"([0-9a-fA-F]{32})(?:[?#/]|$)")
_DASHED_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_LEVEL2_SUFFIXES = (
    "_tecnico",
    "_rechazo_qa",
    "_exito_qa",
    "_reporte_exito_qa",
    "_reporte_rechazo_qa",
)

def to_dashed_uuid(raw: str) -> str:
    h = (raw or "").replace("-", "").strip().lower()
    if len(h) != 32:
        return raw or ""
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

def notion_public_url(app_url: str) -> str:
    return (
        (app_url or "")
        .replace("https://app.notion.com/p/", NOTION_PUBLIC_DOMAIN)
        .replace("https://www.notion.so/", NOTION_PUBLIC_DOMAIN)
    )

def extract_notion_page_id(text: str) -> str:
    if not text:
        return None
    tail_ids = _NOTION_ID_RE.findall(text)
    if tail_ids:
        return to_dashed_uuid(tail_ids[-1])
    dashed = _DASHED_UUID_RE.search(text)
    return to_dashed_uuid(dashed.group(0)) if dashed else None

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
                        if not val_clean.startswith("ntn_your_") and not val_clean.startswith("your_"):
                            os.environ[key.strip()] = val_clean

def append_to_env(key: str, value: str):
    target = ENV_FILE if os.path.exists(ENV_FILE) else os.path.join(PLUGIN_ROOT, ".env")
    with open(target, "a", encoding="utf-8") as f:
        f.write(f"\n{key}={value}\n")
    os.environ[key] = value

def get_notion_token():
    load_env_variables()
    token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
    if not token:
        if not sys.stdin.isatty():
            return None
        print("\n--- Configuración de API de Notion ---")
        token = input("Ingresa el token de integración de Notion (ntn_...): ").strip()
        if token:
            append_to_env("NOTION_TOKEN", token)
    return token

_GCLOUD_TOKEN_MEM_CACHE = {"token": None, "ts": 0}
_COLUMN_MAPPING_CACHE = None

def invalidate_gcloud_token():
    """Drops the in-memory and file token caches (e.g. after a 401)."""
    _GCLOUD_TOKEN_MEM_CACHE["token"] = None
    try:
        os.remove(get_token_cache_path())
    except OSError:
        pass

def google_urlopen(req: urllib.request.Request, timeout: int = 20):
    """urlopen for Google APIs: on 401 the cached token is stale/revoked, so it
    invalidates the cache, fetches a fresh gcloud token and retries once."""
    try:
        return urllib.request.urlopen(req, context=get_ssl_context(), timeout=timeout)
    except urllib.error.HTTPError as e:
        if e.code != 401 or os.environ.get("GCLOUD_ACCESS_TOKEN"):
            raise
        invalidate_gcloud_token()
        fresh = get_gcloud_token()
        if not fresh:
            raise
        req.add_header("Authorization", f"Bearer {fresh}")
        return urllib.request.urlopen(req, context=get_ssl_context(), timeout=timeout)

def get_gcloud_token() -> str:
    # 0. In-memory cache (30 min TTL)
    now = time.time()
    if _GCLOUD_TOKEN_MEM_CACHE["token"] and (now - _GCLOUD_TOKEN_MEM_CACHE["ts"] < 1800):
        return _GCLOUD_TOKEN_MEM_CACHE["token"]

    # 1. Direct env variable
    if os.environ.get("GCLOUD_ACCESS_TOKEN"):
        _GCLOUD_TOKEN_MEM_CACHE["token"] = os.environ.get("GCLOUD_ACCESS_TOKEN")
        _GCLOUD_TOKEN_MEM_CACHE["ts"] = now
        return _GCLOUD_TOKEN_MEM_CACHE["token"]

    # 2. User cache gcloud_token.json (outside repository, TTL < 45 min)
    token_json_path = get_token_cache_path()
    if os.path.exists(token_json_path):
        try:
            mtime = os.path.getmtime(token_json_path)
            if now - mtime < 2700:  # 45 minutes
                with open(token_json_path, "r", encoding="utf-8") as f:
                    tdata = json.load(f)
                    if "access_token" in tdata and tdata["access_token"]:
                        tok = tdata["access_token"]
                        _GCLOUD_TOKEN_MEM_CACHE["token"] = tok
                        _GCLOUD_TOKEN_MEM_CACHE["ts"] = now
                        return tok
        except Exception:
            pass

    # 3. gcloud CLI (cross-platform)
    try:
        cmd = ["gcloud", "auth", "print-access-token"]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE, shell=(sys.platform == "win32"), timeout=15).strip()
        if out and not out.startswith("ERROR"):
            _GCLOUD_TOKEN_MEM_CACHE["token"] = out
            _GCLOUD_TOKEN_MEM_CACHE["ts"] = now
            # Save to secure cache outside repository
            try:
                with open(token_json_path, "w", encoding="utf-8") as f:
                    json.dump({"access_token": out, "timestamp": now}, f)
            except Exception:
                pass
            return out
    except Exception:
        pass
        
    if not sys.stdin.isatty():
        raise RuntimeError("gcloud token no disponible en modo no interactivo. Ejecuta 'gcloud auth login'.")
    
    print("\n[!] No se detectó sesión activa de gcloud. Ejecuta: gcloud auth login --enable-gdrive-access")
    return None

def get_column_mapping() -> dict[str, str]:
    global _COLUMN_MAPPING_CACHE
    if _COLUMN_MAPPING_CACHE:
        return _COLUMN_MAPPING_CACHE

    token = get_gcloud_token()
    mapping = {
        "id": "A", "nombre": "B", "agrupacion": "C", "responsable": "D", "gravedad": "E",
        "descripcion": "F", "reportada_por": "G", "fecha_inicio": "H",
        "estado": "I", "fecha_termino": "J", "cerrada_por": "K",
        "commits": "L", "id_commits": "M", "comentario_dev": "N", "comentario_qa": "O"
    }
    if not token:
        _COLUMN_MAPPING_CACHE = mapping
        return mapping

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
    except Exception as e:
        print(f"Warning: Fallback a mapeo por defecto de columnas ({e})", file=sys.stderr)
        
    _COLUMN_MAPPING_CACHE = mapping
    return mapping

def list_defects_from_sheets(status_filter: list[str] = None, limit: int = None) -> list[dict]:
    """
    Queries Google Sheets directly and returns structured defect objects.
    status_filter: list of strings (e.g. ['Pendiente', 'En Revisión', 'Reportada'])
    """
    token = get_gcloud_token()
    if not token:
        return []

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
                    "commits": get_val("commits"),
                    "id_commits": get_val("id_commits"),
                    "comentario_dev": get_val("comentario_dev"),
                    "comentario_qa": get_val("comentario_qa")
                }
                results.append(item)
                if limit and len(results) >= limit:
                    break
    except Exception as e:
        print(f"Error consultando defectos en Google Sheets: {e}", file=sys.stderr)

    return results

def call_notion_mcp(operation: str, payload: dict) -> dict:
    notion_token = get_notion_token()
    if not notion_token:
        return None

    env = os.environ.copy()
    env["NOTION_TOKEN"] = notion_token
    env["NOTION_API_KEY"] = notion_token
    if os.environ.get("QA_KIT_INSECURE_TLS", "0") == "1":
        env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
    
    # 1. Try MCP via npx notion-mcp-server
    try:
        proc = subprocess.Popen(
            ["npx", "-y", "notion-mcp-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=(sys.platform == "win32")
        )
        init_req = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "qa-kit", "version": "1.0.0"}}
        }
        tool_name = "notion_write" if operation in ("create_page", "append_blocks", "update_page", "archive_page") else "notion_read"
        call_req = {
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": tool_name, "arguments": {"operation": operation, "payload": payload}}
        }
        input_str = json.dumps(init_req) + "\n" + json.dumps(call_req) + "\n"
        stdout, _ = proc.communicate(input=input_str, timeout=12)
        for line in stdout.strip().split("\n"):
            try:
                data = json.loads(line)
                if data.get("id") == 2 and "result" in data:
                    content_text = data["result"]["content"][0]["text"]
                    res_obj = json.loads(content_text)
                    if res_obj.get("ok"):
                        return res_obj["data"]
            except Exception:
                pass
    except Exception:
        pass

    # 2. Robust REST API Fallback
    if operation == "create_page":
        try:
            parent_info = payload.get("parent", {})
            p_id = parent_info.get("page_id")
            title_text = payload.get("title", "Reporte QA")
            md_content = payload.get("markdown", "")
            
            def parse_rich_text(raw_text: str) -> list[dict]:
                parts = []
                token_re = re.compile(r'(\*\*[^*]+\*\*|`[^`]+`)')
                tokens = token_re.split(raw_text)
                for t in tokens:
                    if not t: continue
                    is_bold = t.startswith("**") and t.endswith("**") and len(t) >= 4
                    is_code = t.startswith("`") and t.endswith("`") and len(t) >= 2
                    core_text = t[2:-2] if is_bold else (t[1:-1] if is_code else t)
                    
                    # Notion max 2000 chars per rich_text item: chunk without data loss
                    for chunk in [core_text[i:i+2000] for i in range(0, len(core_text), 2000)]:
                        item = {"type": "text", "text": {"content": chunk}}
                        if is_bold:
                            item["annotations"] = {"bold": True}
                        elif is_code:
                            item["annotations"] = {"code": True}
                        parts.append(item)
                return parts if parts else [{"type": "text", "text": {"content": raw_text[:2000]}}]

            blocks = []
            lines = md_content.strip().split("\n")
            in_code_block = False
            code_lines = []
            code_lang = "plain text"

            for l in lines:
                l_str = l.strip()
                # Handle Code Blocks
                if l_str.startswith("```"):
                    if not in_code_block:
                        in_code_block = True
                        code_lang = l_str[3:].strip() or "python"
                        code_lines = []
                    else:
                        in_code_block = False
                        code_content = "\n".join(code_lines)
                        # Chunk code blocks if exceeding 2000 chars to avoid loss
                        for c_chunk in [code_content[i:i+2000] for i in range(0, len(code_content), 2000)]:
                            blocks.append({
                                "object": "block",
                                "type": "code",
                                "code": {
                                    "rich_text": [{"type": "text", "text": {"content": c_chunk}}],
                                    "language": code_lang.lower() if code_lang.lower() in ("python", "bash", "javascript", "typescript", "json", "sql", "markdown") else "plain text"
                                }
                            })
                    continue

                if in_code_block:
                    code_lines.append(l)
                    continue

                if not l_str:
                    continue

                # Headings
                if l_str.startswith("# "):
                    blocks.append({"object": "block", "type": "heading_1", "heading_1": {"rich_text": parse_rich_text(l_str[2:])}})
                elif l_str.startswith("## "):
                    blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": parse_rich_text(l_str[3:])}})
                elif l_str.startswith("### "):
                    blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": parse_rich_text(l_str[4:])}})
                # Divider
                elif l_str == "---":
                    blocks.append({"object": "block", "type": "divider", "divider": {}})
                # Bulleted List
                elif l_str.startswith("- ") or l_str.startswith("* "):
                    blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": parse_rich_text(l_str[2:])}})
                # Numbered List
                elif re.match(r"^\d+\.\s+", l_str):
                    item_text = re.sub(r"^\d+\.\s+", "", l_str)
                    blocks.append({"object": "block", "type": "numbered_list_item", "numbered_list_item": {"rich_text": parse_rich_text(item_text)}})
                # Callout / Quote / Warning
                elif l_str.startswith("> "):
                    callout_text = l_str[2:]
                    is_warning = "ADVERTENCIA" in callout_text or "⚠️" in callout_text
                    icon_emoji = "⚠️" if is_warning else "💡"
                    blocks.append({
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": parse_rich_text(callout_text),
                            "icon": {"type": "emoji", "emoji": icon_emoji}
                        }
                    })
                # Paragraph
                else:
                    blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": parse_rich_text(l_str)}})

            body = {
                "parent": {"page_id": p_id},
                "properties": {"title": {"title": [{"type": "text", "text": {"content": title_text}}]}},
                "children": blocks[:100]
            }
            req = urllib.request.Request(
                "https://api.notion.com/v1/pages",
                data=json.dumps(body).encode("utf-8"),
                headers={"Authorization": f"Bearer {notion_token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
            )
            ctx = get_ssl_context()
            created_page = None
            try:
                with urllib.request.urlopen(req, context=ctx) as resp:
                    created_page = json.loads(resp.read().decode("utf-8"))
            except Exception as create_err:
                print(f"Error creando página inicial en Notion REST API: {create_err}", file=sys.stderr)
                return None

            # Lossless Pagination: Append remaining blocks in chunks of 100 with retry/backoff
            if len(blocks) > 100 and created_page and "id" in created_page:
                page_id_created = created_page["id"]
                for start_idx in range(100, len(blocks), 100):
                    batch = blocks[start_idx:start_idx+100]
                    patch_body = {"children": batch}
                    patch_req = urllib.request.Request(
                        f"https://api.notion.com/v1/blocks/{page_id_created}/children",
                        data=json.dumps(patch_body).encode("utf-8"),
                        headers={"Authorization": f"Bearer {notion_token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"},
                        method="PATCH"
                    )
                    for attempt in range(3):
                        try:
                            with urllib.request.urlopen(patch_req, context=ctx) as p_resp:
                                p_resp.read()
                            break
                        except Exception as patch_err:
                            if attempt < 2:
                                time.sleep(1.5 * (attempt + 1))
                            else:
                                print(f"Warning: Fallo al añadir lote {start_idx}..{start_idx+100} a la página {page_id_created}: {patch_err}", file=sys.stderr)

            return created_page
        except Exception as rest_err:
            print(f"Error en fallback REST de Notion: {rest_err}", file=sys.stderr)

    return None

def obsidian_enabled() -> bool:
    """The local Obsidian mirror is opt-in (QA_KIT_OBSIDIAN=1) so the kit never
    creates docs/vault/ in a teammate's repo unasked."""
    return _read_env_key("QA_KIT_OBSIDIAN") == "1"

def ensure_obsidian_vault():
    os.makedirs(os.path.join(OBSIDIAN_VAULT_DIR, "defectos"), exist_ok=True)
    os.makedirs(os.path.join(OBSIDIAN_VAULT_DIR, "reportes"), exist_ok=True)

def sync_obsidian_note(defect_id: str, title: str, status: str, severity: str, level1_url: str, subpage_url: str, evidence: str = "", tech_details: str = ""):
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
level1_url: "{level1_url}"
subpage_url: "{subpage_url}"
last_tested: "{os.environ.get('QA_TEST_DATE') or time.strftime('%Y-%m-%d')}"
tags:
  - qa/defect
  - status/{status.lower().replace(' ', '_')}
  - severity/{severity.lower()}
---

# {defect_id}: {title}

**Estado QA:** `{status}` | **Severidad:** `{severity}`  
**Enlace Notion Principal:** [{defect_id} en Notion]({level1_url})  
**Subpágina de Reporte:** [Subpágina QA]({subpage_url})  

---

## 🧪 Evidencia Empírica y Pruebas Realizadas
{evidence if evidence else "Validación técnica y funcional completada según protocolo QA."}

---

## 🛠️ Diagnóstico y Resolución Técnica
{tech_details if tech_details else "Documentado en la subpágina correspondiente de Notion."}
"""
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(frontmatter)

def _title_matches_defect(title: str, defect_id: str) -> bool:
    title = title or ""
    if not (title == defect_id or title.startswith(defect_id + "_")):
        return False
    if title.startswith(defect_id + "_ampliacion_"):  # qa-amplify subpages: AF-XXX_ampliacion_<origen>
        return False
    return not any(title.endswith(sfx) for sfx in _LEVEL2_SUFFIXES)

def resolve_level1_via_parent_chain(page_id: str, max_depth: int = 6) -> tuple[str, str]:
    seen = set()
    current = to_dashed_uuid(page_id)
    for _ in range(max_depth):
        if not current or current in seen: break
        seen.add(current)
        page = call_notion_mcp("get_page", {"page_id": current})
        if not page or not isinstance(page, dict): break
        parent_id = to_dashed_uuid((page.get("parent") or {}).get("page_id", ""))
        if parent_id == DEFAULT_PARENT_PAGE_ID:
            return page["id"], notion_public_url(page.get("url", ""))
        current = parent_id
    return None, None

def resolve_level1_from_sheet(defect_id: str) -> tuple[str, str]:
    try:
        row_idx = find_sheet_row_for_defect(defect_id)
        if not row_idx: return None, None
        col = get_column_mapping().get("comentario_qa", "O")
        token = get_gcloud_token()
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{SHEET_NAME}!{col}{row_idx}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with google_urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        values = data.get("values", [])
        cell = values[0][0] if values and values[0] else ""
        page_id = extract_notion_page_id(cell)
        if not page_id: return None, None
        l1_id, l1_url = resolve_level1_via_parent_chain(page_id)
        if not l1_id: return None, None
        page = call_notion_mcp("get_page", {"page_id": l1_id})
        title = (page or {}).get("title", "") if isinstance(page, dict) else ""
        if not _title_matches_defect(title, defect_id):
            return None, None
        return l1_id, l1_url
    except Exception:
        return None, None

def find_notion_level1_page_id(defect_id: str) -> tuple[str, str]:
    res = call_notion_mcp(
        "search_pages",
        {"query": defect_id, "paginate": True, "page_limit": 8, "page_size": 100},
    )
    results = res.get("results", []) if isinstance(res, dict) else []

    matches = []
    for p in results:
        if not _title_matches_defect(p.get("title", ""), defect_id):
            continue
        parent_id = to_dashed_uuid((p.get("parent") or {}).get("page_id", ""))
        if parent_id != DEFAULT_PARENT_PAGE_ID:
            continue
        matches.append(p)

    if not matches:
        return None, None
    if len(matches) > 1:
        print(
            f"Warning: {len(matches)} candidate Level-1 Notion pages for {defect_id} "
            f"({[m.get('title') for m in matches]}). Using the first; pass "
            f"level1_page_id explicitly to disambiguate.",
            file=sys.stderr,
        )
    p = matches[0]
    return p["id"], notion_public_url(p.get("url", ""))

def find_sheet_row_for_defect(defect_id: str) -> int:
    token = get_gcloud_token()
    if not token: return None
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
    except Exception as e:
        print(f"Error buscando fila de {defect_id}: {e}", file=sys.stderr)
    return None

def get_sheet_cell(row_idx: int, key: str) -> str:
    """Reads one mapped column (e.g. 'gravedad') of a sheet row. Returns '' on failure."""
    token = get_gcloud_token()
    if not token or not row_idx:
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
    except Exception as e:
        print(f"Warning: no se pudo leer {key} de la fila {row_idx} ({e})", file=sys.stderr)
        return ""

def batch_update_sheet_row(row_idx: int, updates: dict):
    token = get_gcloud_token()
    if not token: return
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
    page_suffix: str,
    content: str,
    status: str,
    severity: str | None,
    summary_or_reason: str,
    comment_label: str,
    evidence: str,
    tech_details: str,
    level1_page_id: str = None,
    dry_run: bool = False,
) -> dict:
    """Publishes a QA outcome subpage and updates Sheets + Obsidian.
    Never creates a new Level-1 page: closing/rejecting a defect that has no
    Level-1 page would create a duplicate, so it aborts instead.
    Returns None on failure; the result carries 'sheet_updated'."""
    user_name = get_user_name()
    p1_id, p1_url = level1_page_id, None
    if not p1_id:
        p1_id, p1_url = resolve_level1_from_sheet(defect_id)
    if not p1_id:
        p1_id, p1_url = find_notion_level1_page_id(defect_id)

    if not p1_id:
        print(
            f"Error: No se encontró la página Nivel 1 de Notion para {defect_id}. "
            f"No se crea una nueva para evitar duplicados; pásala explícitamente como level1_page_id.",
            file=sys.stderr,
        )
        return None

    row_idx = find_sheet_row_for_defect(defect_id)
    # Severity always comes from the sheet (the defect's real GRAVEDAD), never a fixed value
    if not severity:
        severity = get_sheet_cell(row_idx, "gravedad") or "Sin gravedad"
    if dry_run:
        return {
            "dry_run": True,
            "defect_id": defect_id,
            "level1_page_id": p1_id,
            "notion_subpage_title": f"{defect_id}_{page_suffix}",
            "sheet_row": row_idx,
            "gravedad": severity,
            "obsidian_note": os.path.join(OBSIDIAN_VAULT_DIR, "defectos", f"{defect_id}.md") if obsidian_enabled() else None,
            "sheet_updates": {
                "estado": status,
                "cerrada_por": user_name,
                "comentario_qa": f"{summary_or_reason}. {comment_label}:\n<url de la subpágina>",
            },
        }

    clean_md = re.sub(r'\[([^\]]+)\]\(file:///[^\)]+\)', r'`\1`', content)
    page = call_notion_mcp("create_page", {
        "parent": {"type": "page_id", "page_id": p1_id},
        "title": f"{defect_id}_{page_suffix}",
        "markdown": clean_md
    })
    if not page:
        print(f"Error al subir subpágina {page_suffix} a Notion", file=sys.stderr)
        return None

    pub_url = page.get("url", "").replace("https://app.notion.com/p/", NOTION_PUBLIC_DOMAIN)
    print(f"Subpágina publicada en Notion: {pub_url}")

    sheet_updated = False
    try:
        if row_idx:
            batch_update_sheet_row(row_idx, {
                "estado": status,
                "cerrada_por": user_name,
                "comentario_qa": f"{summary_or_reason}. {comment_label}:\n{pub_url}"
            })
            sheet_updated = True
        else:
            print(f"Error: {defect_id} no está en Google Sheets; la hoja NO se actualizó.", file=sys.stderr)
    except Exception as e:
        print(f"Error al actualizar Google Sheets ({e}); la hoja NO se actualizó.", file=sys.stderr)

    sync_obsidian_note(
        defect_id=defect_id,
        title=summary_or_reason,
        status=status,
        severity=severity,
        level1_url=p1_url or pub_url,
        subpage_url=pub_url,
        evidence=evidence,
        tech_details=tech_details
    )

    return {"defect_id": defect_id, "status": status, "notion_url": pub_url, "user_name": user_name, "sheet_updated": sheet_updated}
