"""
QA Code Audit & Diff Aggregator CLI
-----------------------------------
Inspects git diffs, commits, and status across the 4 product subrepositories.
Supports querying directly by defect ID (--issue AF-XXX) by resolving
associated commit hashes from Google Sheets.
"""
import sys
import os
import subprocess
import argparse
import json
import re

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

REPOS = [
    "ai-factory-core",
    "ai-factory-agents",
    "ai-factory-frontend",
    "ai-factory-platform"
]

def run_cmd(cmd, cwd):
    try:
        res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, shell=(sys.platform == "win32"), encoding="utf-8", errors="replace")
        return res.stdout.strip()
    except Exception as e:
        return f"Error running {' '.join(cmd)}: {e}"

def extract_commit_hashes(text: str) -> list[str]:
    """Finds all potential 7-40 hex commit hashes in text."""
    if not text:
        return []
    return re.findall(r"\b[0-9a-fA-F]{7,40}\b", text)

def resolve_commits_from_issue(issue_id: str) -> tuple[dict, list[str]]:
    """Looks up the issue in Google Sheets and resolves its commit hashes."""
    defects = utils.list_defects_from_sheets(limit=None)
    for d in defects:
        if d["id"].upper() == issue_id.upper():
            combined_text = f"{d.get('id_commits', '')} {d.get('commits', '')} {d.get('comentario_dev', '')}"
            commits = extract_commit_hashes(combined_text)
            return d, list(dict.fromkeys(commits))  # deduplicate preserving order
    return None, []

def audit_repo(repo_name, commit_hashes=None, max_commits=3):
    repo_path = os.path.join(utils.WORKSPACE_ROOT, repo_name)
    if not os.path.exists(repo_path):
        return {"repo": repo_name, "status": "Not cloned locally"}

    result = {
        "repo": repo_name,
        "branch": run_cmd(["git", "branch", "--show-current"], repo_path),
        "status": run_cmd(["git", "status", "-s"], repo_path),
        "matched_commits": [],
        "recent_commits": [],
        "diff": ""
    }

    # If specific commit hashes provided, check which ones belong to this repo
    if commit_hashes:
        for c in commit_hashes:
            check_commit = run_cmd(["git", "rev-parse", "--verify", c], repo_path)
            if "Error" not in check_commit and len(check_commit) >= 7:
                c_details = run_cmd(["git", "show", "--stat", "--oneline", c], repo_path)
                c_diff = run_cmd(["git", "show", c], repo_path)
                result["matched_commits"].append({
                    "hash": c,
                    "summary": c_details,
                    "diff": c_diff[:3000]  # Cap diff to avoid giant outputs
                })

    # Also fetch recent HEAD commits for general context
    logs = run_cmd(["git", "log", f"-n{max_commits}", "--oneline"], repo_path)
    result["recent_commits"] = logs.split("\n") if logs else []
    if not result["matched_commits"]:
        result["diff_head"] = run_cmd(["git", "diff", "HEAD~1", "--stat"], repo_path)

    return result

def main():
    parser = argparse.ArgumentParser(description="Audit git changes and diffs across IAFactory subrepositories.")
    parser.add_argument("--issue", type=str, default=None, help="Target defect ID (e.g. AF-185) to resolve its commits from Sheets")
    parser.add_argument("--repo", type=str, default="all", help="Target repository (or 'all')")
    parser.add_argument("--commit", type=str, default=None, help="Target commit hash to inspect directly")
    parser.add_argument("--run-tests", action="store_true", help="Ejecutar pruebas unitarias dirigidas localmente con fast_test_runner.py (omitido por defecto, cubierto en Jenkins)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    targets = REPOS if args.repo == "all" else [args.repo]
    
    commit_hashes = []
    issue_data = None

    if args.commit:
        commit_hashes = [args.commit]
    elif args.issue:
        issue_data, commit_hashes = resolve_commits_from_issue(args.issue)

    audits = []
    for r in targets:
        audits.append(audit_repo(r, commit_hashes=commit_hashes))

    # Ejecución opcional de tests unitarios solo bajo flag --run-tests
    test_results = None
    if args.run_tests:
        runner_script = os.path.join(os.path.dirname(__file__), "fast_test_runner.py")
        if os.path.exists(runner_script):
            try:
                # Correr suite voseo como baseline representativo
                t_proc = subprocess.run([sys.executable, runner_script, "--agent", "all", "--test-voseo", "--json"], capture_output=True, text=True, timeout=45)
                if t_proc.stdout:
                    test_results = json.loads(t_proc.stdout)
                else:
                    test_results = {"executed": True, "raw": t_proc.stderr}
            except Exception as e:
                test_results = {"executed": True, "error": str(e)}

    output_payload = {
        "issue": args.issue,
        "issue_metadata": issue_data,
        "resolved_commits": commit_hashes,
        "audits": audits,
        "tests_executed": args.run_tests,
        "test_results": test_results
    }

    if args.json:
        print(json.dumps(output_payload, indent=2, ensure_ascii=False))
        return

    print("\n### 🔍 Resumen de Auditoría de Código y Commits")
    if args.issue:
        if issue_data:
            print(f"**Defecto:** `{issue_data['id']}` - {issue_data['nombre']}")
            print(f"**Estado:** `{issue_data['estado']}` | **Responsable:** {issue_data['responsable'] or 'Sin asignar'}")
            print(f"**Commits Asociados en Sheets:** {', '.join(commit_hashes) if commit_hashes else 'Ninguno registrado'}")
        else:
            print(f"⚠️ Defecto `{args.issue}` no encontrado en Google Sheets.")

    for a in audits:
        print(f"\n📁 **Repositorio:** `{a['repo']}`")
        if a.get("status") == "Not cloned locally":
            print("  ⚠️ *No clonado localmente.*")
            continue
        print(f"  - **Rama activa:** `{a.get('branch')}`")
        if a.get("status"):
            print(f"  - **Cambios locales pendientes:**\n```\n{a.get('status')}\n```")
        
        if a.get("matched_commits"):
            for mc in a["matched_commits"]:
                print(f"  - **Commit Encontrado ({mc['hash']}):**\n```\n{mc['summary']}\n```")
        elif not commit_hashes:
            print(f"  - **Últimos commits:** {', '.join(a.get('recent_commits')[:2])}")
            if a.get("diff_head"):
                print(f"  - **Diff HEAD~1:**\n```\n{a.get('diff_head')}\n```")

    print("\n🧪 **Validación de Tests:**")
    if args.run_tests:
        if test_results and test_results.get("success"):
            print("  ✅ Tests ejecutados localmente: PASÓ")
        else:
            print(f"  ⚠️ Tests ejecutados localmente: {test_results}")
    else:
        print("  ℹ️ Omitida por defecto (cubierta por Jenkins CI/CD). Usa `--run-tests` para forzar ejecución local.")

if __name__ == "__main__":
    main()
