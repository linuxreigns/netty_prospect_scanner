#!/usr/bin/env bash
# Configura branch protection en main via GitHub REST API.
# Requiere un Personal Access Token con permiso 'repo' (o 'administration').
#
# Uso:
#   export GITHUB_PAT=ghp_xxxxxxxxxxxxx
#   ./scripts/setup_branch_protection.sh

set -euo pipefail

REPO="linuxreigns/netty_prospect_scanner"
BRANCH="main"
PAT="${GITHUB_PAT:?Exporta GITHUB_PAT=ghp_xxx antes de ejecutar este script}"

echo "Aplicando branch protection en ${REPO}:${BRANCH}..."

response=$(curl -s -w "\n%{http_code}" -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${PAT}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${REPO}/branches/${BRANCH}/protection" \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["test (ubuntu-latest)"]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": null,
    "restrictions": null,
    "allow_force_pushes": false,
    "allow_deletions": false
  }')

http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

python3 - "$http_code" <<PY
import sys, json

code = int(sys.argv[1])
body = """$body"""

try:
    data = json.loads(body)
except Exception:
    data = {}

if code == 200:
    print("Branch protection configurada exitosamente.")
    fpe = data.get("allow_force_pushes", {})
    de  = data.get("allow_deletions", {})
    sc  = data.get("required_status_checks", {})
    print(f"  Force push bloqueado : {not fpe.get('enabled', True)}")
    print(f"  Eliminacion bloqueada: {not de.get('enabled', True)}")
    print(f"  Checks requeridos    : {sc.get('contexts', [])}")
    print(f"  Enforce admins       : {data.get('enforce_admins', {}).get('enabled', False)}")
else:
    print(f"Error HTTP {code}:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    sys.exit(1)
PY
