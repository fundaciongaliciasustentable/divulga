#!/bin/sh
# Empaqueta e sobe dist/ ao servidor de Dinahosting por FTP/FTPS/SFTP (lftp).
#
# Precisa as credenciais en .dinahosting.env (copia .dinahosting.env.example,
# cubrea e NUNCA a subas a git — xa está en .gitignore) e o paquete `lftp`
# (`brew install lftp`).
#
# Uso:
#   ./scripts/subir.sh           # sobe e actualiza; NON borra nada no servidor
#   ./scripts/subir.sh --probar  # só amosa o que faría, non toca o servidor
#   ./scripts/subir.sh --borrar  # ademais borra no servidor o que xa non
#                                 # existe en dist/ — SEMPRE respectando
#                                 # api/datos/ (os votos de habelos-hainos)
set -e
cd "$(dirname "$0")/.."

ENV_FILE=.dinahosting.env
if [ ! -f "$ENV_FILE" ]; then
  echo "Falta $ENV_FILE. Copia .dinahosting.env.example a $ENV_FILE e cubrea coas credenciais." >&2
  exit 1
fi
if ! command -v lftp >/dev/null 2>&1; then
  echo "Falta lftp. Instálao con: brew install lftp" >&2
  exit 1
fi

set -a
. "./$ENV_FILE"
set +a

: "${DINA_PROTOCOLO:?Falta DINA_PROTOCOLO en $ENV_FILE}"
: "${DINA_HOST:?Falta DINA_HOST en $ENV_FILE}"
: "${DINA_USUARIO:?Falta DINA_USUARIO en $ENV_FILE}"
: "${DINA_CONTRASINAL:?Falta DINA_CONTRASINAL en $ENV_FILE}"
DINA_RUTA_REMOTA="${DINA_RUTA_REMOTA:-/}"
if [ -z "$DINA_PORT" ]; then
  case "$DINA_PROTOCOLO" in
    sftp) DINA_PORT=22 ;;
    *) DINA_PORT=21 ;;
  esac
fi

echo "Empaquetando..."
./scripts/empaquetar.sh >/dev/null

MIRROR_OPTS="--reverse --verbose --parallel=3"
for arg in "$@"; do
  case "$arg" in
    --borrar) MIRROR_OPTS="$MIRROR_OPTS --delete --exclude-glob api/datos/**" ;;
    --probar) MIRROR_OPTS="$MIRROR_OPTS --dry-run" ;;
  esac
done

case " $* " in
  *" --borrar "*) BORRADO=" (con borrado remoto, agás api/datos/)" ;;
  *) BORRADO=" (sen borrar nada no servidor)" ;;
esac
case " $* " in
  *" --probar "*) echo "[probar] non se toca o servidor — só se amosa o que faría." ;;
esac
echo "Subindo dist/ a $DINA_HOST$DINA_RUTA_REMOTA$BORRADO..."

VERIFY_SSL=yes
[ "${DINA_SSL_NO_VERIFY:-0}" = "1" ] && VERIFY_SSL=no

# lftp (nalgunhas versións) escribe URLs con user:contrasinal embebido nas
# liñas de progreso/chmod do mirror; redacímolas sempre, por se acaso, para
# que o contrasinal nunca quede visible nin na terminal nin en ningún log.
lftp <<EOF 2>&1 | sed -E "s#(//)[^/@[:space:]]+:[^/@[:space:]]+@#\\1[credenciais-ocultas]@#g"
set ftp:ssl-allow true
set ssl:verify-certificate $VERIFY_SSL
open -u "$DINA_USUARIO","$DINA_CONTRASINAL" -p "$DINA_PORT" "$DINA_PROTOCOLO://$DINA_HOST"
mirror $MIRROR_OPTS dist "$DINA_RUTA_REMOTA"
bye
EOF

echo "Feito."
