#!/bin/sh
# Prepara dist/ e divulga-web.zip só cos ficheiros públicos do sitio.
# Sube o contido de dist/ (ou descomprime o zip) na raíz do subdominio.
set -e
cd "$(dirname "$0")/.."
python3 build.py
rm -rf dist divulga-web.zip
rsync -a --exclude-from=- ./ dist/ <<'X'
.git/
.claude/
.gitignore
fontes/
templates/
scripts/
dist/
build.py
README.md
*.zip
.DS_Store
X
(cd dist && zip -qr ../divulga-web.zip .)
echo "dist/ e divulga-web.zip listos:"
find dist -type f | sed 's#^dist/#  #' | sort
