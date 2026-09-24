#!/usr/bin/env python3
"""
CA Bundle Builder (fix for TLS interception by antivirus / corporate proxies)
----------------------------------------------------------------------------
Some antivirus products (e.g. Avast "HTTPS scanning") and corporate proxies
re-sign TLS traffic with their own root CA. Windows trusts it, but gcloud and
Python use their own CA list, so they fail with CERTIFICATE_VERIFY_FAILED.

This script writes a bundle = gcloud's public CA list + the interception CA,
into the user cache (outside any repo). It does NOT change gcloud's global
config: the kit points gcloud at the bundle only for its own processes.

Usage:
    python build_ca_bundle.py                 # auto-detect known interception CAs
    python build_ca_bundle.py --extra C:/ruta/ca.pem
    python build_ca_bundle.py --json
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

KNOWN_INTERCEPTION_CAS = [
    r"C:\ProgramData\Avast Software\Avast\wscert.pem",
    r"C:\ProgramData\AVG\Antivirus\wscert.pem",
]

def find_gcloud_public_cas() -> str:
    gcloud = shutil.which("gcloud")
    if not gcloud:
        return ""
    try:
        sdk_root = subprocess.check_output(
            [gcloud, "info", "--format=value(installation.sdk_root)"],
            text=True, stderr=subprocess.DEVNULL, timeout=30, shell=(sys.platform == "win32")
        ).strip()
    except Exception:
        return ""
    for pattern in ("lib/third_party/certifi/cacert.pem", "lib/third_party/**/cacert.pem"):
        hits = glob.glob(os.path.join(sdk_root, pattern), recursive=True)
        if hits:
            return hits[0]
    return ""

def main():
    parser = argparse.ArgumentParser(description="Construye un bundle de CA para TLS interceptado (antivirus/proxy).")
    parser.add_argument("--extra", action="append", default=[], help="PEM adicional a incluir (repetible)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    public = find_gcloud_public_cas()
    if not public:
        try:
            import certifi  # optional
            public = certifi.where()
        except ImportError:
            print("❌ No encontré la lista pública de CA (ni la de gcloud ni certifi).", file=sys.stderr)
            sys.exit(1)

    extras = [p for p in args.extra if os.path.exists(p)] or [p for p in KNOWN_INTERCEPTION_CAS if os.path.exists(p)]
    missing = [p for p in args.extra if not os.path.exists(p)]
    if missing:
        print(f"❌ No existen: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)
    if not extras:
        print("ℹ️ No se detectó ningún CA de interceptación conocido. Si tu antivirus o proxy re-firma TLS, "
              "pasa su certificado con --extra.", file=sys.stderr)
        sys.exit(1)

    out_path = os.path.join(utils.get_token_cache_dir(), "ca_bundle.pem")
    with open(out_path, "w", encoding="ascii", errors="ignore") as out:
        for src in [public] + extras:
            with open(src, "r", encoding="ascii", errors="ignore") as f:
                out.write(f.read().strip() + "\n")

    result = {"bundle": out_path, "public_cas": public, "extra_cas": extras,
              "env_line": f"QA_KIT_CA_BUNDLE={out_path}"}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"✅ Bundle generado: {out_path}")
        print(f"   CA públicas: {public}")
        print(f"   CA de interceptación: {', '.join(extras)}")
        print("\nAgrega estas líneas al .env del kit:")
        print(f"   QA_KIT_CA_BUNDLE={out_path}")
        print("   QA_KIT_TLS_RELAX_STRICT=1   # solo si usas Python 3.13 o superior")

if __name__ == "__main__":
    main()
