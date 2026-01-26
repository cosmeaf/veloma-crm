#!/usr/bin/env bash
# Manager para Django + Celery (DEV/Stage) no host
# Agora respeita CELERY_ENABLED do .env
# Melhorias: tolerância a falhas (ex: Redis ausente), error handling robusto, retries em checks, logs aprimorados

set -euo pipefail

# ===== Config Dinâmica =====
SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
APP_DIR="${APP_DIR:-$SCRIPT_DIR}"
VENV_DIR="${VENV_DIR:-$APP_DIR/venv}"
LOG_DIR="${LOG_DIR:-$APP_DIR/logs}"
LOG_FILE="${LOG_FILE:-$LOG_DIR/manager.log}"

DJANGO_PORT="${DJANGO_PORT:-7000}"
DJANGO_BIND="0.0.0.0:${DJANGO_PORT}"

STATIC_DIR="${STATIC_DIR:-/var/www/api.alvelos.com/static}"
MEDIA_DIR="${MEDIA_DIR:-/var/www/api.alvelos.com/media}"

REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_CLI="${REDIS_CLI:-redis-cli}"

# Comandos Celery (queues dedicadas, ex: -Q emails,celery)
CELERY_WORKER_CMD="${CELERY_WORKER_CMD:-celery -A core.celery worker -Q emails,celery --loglevel=INFO --logfile=$LOG_DIR/celery_worker.log --detach --concurrency=2 --prefetch-multiplier=4}"
CELERY_BEAT_CMD="${CELERY_BEAT_CMD:-celery -A core.celery beat --loglevel=INFO --logfile=$LOG_DIR/celery_beat.log --detach}"

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-core.settings}"
export PATH="$VENV_DIR/bin:$PATH"

DJANGO_PATTERN="python manage.py runserver 0.0.0.0:$DJANGO_PORT"
CELERY_WORKER_PATTERN="celery -A core.celery worker"
CELERY_BEAT_PATTERN="celery -A core.celery beat"

# ANSI colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# ===== Helpers Melhorados (com tolerância) =====
log() { echo -e "[$(date '+%F %T')] $*" | tee -a "$LOG_FILE"; }
ok()  { echo -e "${GREEN}$*${NC}" | tee -a "$LOG_FILE"; }
warn(){ echo -e "${YELLOW}$*${NC}" | tee -a "$LOG_FILE"; }
err() { echo -e "${RED}$*${NC}" >&2 | tee -a "$LOG_FILE"; }

need_cmd() {
  for c in "$@"; do
    if ! command -v "$c" >/dev/null 2>&1; then
      err "Comando não encontrado: $c. Instale-o para continuar."
      return 1
    fi
  done
  return 0
}

ensure_dirs() {
  mkdir -p "$LOG_DIR" || { err "Falha ao criar $LOG_DIR"; return 1; }
  chmod 775 "$LOG_DIR" || warn "Falha ao setar permissões em $LOG_DIR (continuando)."
  touch "$LOG_FILE" || warn "Falha ao criar $LOG_FILE (logs serão no stdout)."
  chmod 664 "$LOG_FILE" || warn "Falha ao setar permissões em $LOG_FILE."

  local changed=false
  if [[ -n "${STATIC_DIR:-}" && ! -d "$STATIC_DIR" ]]; then
    mkdir -p "$STATIC_DIR" || warn "Falha ao criar $STATIC_DIR (continuando)."
    changed=true
  fi
  if [[ -n "${MEDIA_DIR:-}" && ! -d "$MEDIA_DIR" ]]; then
    mkdir -p "$MEDIA_DIR" || warn "Falha ao criar $MEDIA_DIR (continuando)."
    changed=true
  fi
  if [[ "$changed" = true ]]; then
    chown -R www-data:www-data "$STATIC_DIR" "$MEDIA_DIR" 2>/dev/null || warn "Falha ao chown static/media (ok em dev)."
    chmod -R 755 "$STATIC_DIR" "$MEDIA_DIR" 2>/dev/null || warn "Falha ao chmod static/media."
    if command -v nginx >/dev/null 2>&1; then
      nginx -t >>"$LOG_FILE" 2>&1 && systemctl reload nginx || warn "nginx reload falhou (ok em dev)."
    fi
  fi
  return 0
}

activate_venv() {
  if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate" || { err "Falha ao ativar venv em $VENV_DIR"; return 1; }
  else
    err "Virtualenv não encontrado em $VENV_DIR. Crie um venv primeiro."
    return 1
  fi
  return 0
}

check_env_secret() {
  if [[ ! -f "$APP_DIR/.env" ]]; then
    warn ".env não encontrado em $APP_DIR. Usando defaults (pode causar problemas)."
    return 0  # tolerante: continua
  fi
  python - <<'PY' 2>>"$LOG_FILE" || { err "SECRET_KEY ausente ou vazia no .env."; return 1; }
from decouple import config
config('SECRET_KEY')
PY
  return 0
}

check_redis() {
  log "Checando Redis em ${REDIS_HOST}:${REDIS_PORT} (com retries)..."
  if ! need_cmd "${REDIS_CLI}"; then
    warn "redis-cli ausente; pulando verificação ativa (Redis pode estar OK)."
    return 0
  fi

  local retries=3
  while [[ $retries -gt 0 ]]; do
    if ${REDIS_CLI} -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping | grep -q "PONG"; then
      ok "Redis OK."
      return 0
    fi
    warn "Redis inacessível (tentativa $((4 - retries))/3). Aguardando 5s..."
    sleep 5
    ((retries--))
  done
  err "Redis inacessível após retries. Verifique o servidor."
  return 1  # agora falha se não conectar, mas start() pode tolerar
}

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -tuln | grep -qE "[:.]${port}[[:space:]]"
  else
    netstat -tuln 2>/dev/null | grep -qE "[: ]${port}[[:space:]]"
  fi
}

check_port_free() {
  local port="$1"
  if port_in_use "$port"; then
    err "Porta ${port} em uso. Pare o serviço ou mude DJANGO_PORT."
    return 1
  fi
  return 0
}

collect_static_if_applicable() {
  python - <<'PY' >/dev/null 2>&1 || { warn "collectstatic pulado (STATIC_ROOT não configurado)."; return 0; }
from django.conf import settings
assert bool(getattr(settings, "STATIC_ROOT", "")), "no STATIC_ROOT"
PY
  log "Executando collectstatic..."
  python manage.py collectstatic --noinput >>"$LOG_FILE" 2>&1 && ok "collectstatic OK." || { warn "collectstatic falhou (veja $LOG_FILE), continuando."; return 0; }
  return 0
}

pg() { pgrep -f "$1" >/dev/null 2>&1; }

stop_pattern() {
  local pattern="$1" name="$2"
  local pids
  pids=$(pgrep -f "$pattern" || true)
  if [[ -z "$pids" ]]; then
    log "$name não estava rodando."
    return 0
  fi
  log "Parando $name (PIDs: $pids)..."
  for pid in $pids; do
    kill "$pid" 2>/dev/null || warn "Falha ao kill $pid (já morto?)."
  done
  sleep 2
  pids=$(pgrep -f "$pattern" || true)
  if [[ -n "$pids" ]]; then
    warn "$name ainda ativo. Forçando kill -9..."
    for pid in $pids; do
      kill -9 "$pid" 2>/dev/null || warn "Falha ao kill -9 $pid."
    done
    sleep 1
    pgrep -f "$pattern" >/dev/null 2>&1 && { err "Falha ao encerrar $name."; return 1; }
  fi
  ok "$name parado."
  return 0
}

get_celery_enabled() {
  python - <<PY 2>>"$LOG_FILE"
from decouple import config
enabled = config("CELERY_ENABLED", default=False, cast=bool)
print("True" if enabled else "False")
PY
}

# ===== Ações =====
start() {
  if ! need_cmd python3 bash; then
    err "Requisitos básicos ausentes. Abortando start."
    exit 1
  fi
  cd "$APP_DIR" || { err "Falha ao entrar em $APP_DIR"; exit 1; }

  if ! activate_venv; then exit 1; fi
  if ! ensure_dirs; then warn "Problemas com dirs, continuando."; fi
  if ! check_env_secret; then exit 1; fi
  
  # Redis: tolerante - se falhar, avisa mas continua (útil se CELERY_ENABLED=False)
  check_redis || warn "Redis falhou, mas continuando (e-mails síncronos se CELERY_ENABLED=False)."
  
  if ! check_port_free "$DJANGO_PORT"; then exit 1; fi
  collect_static_if_applicable  # tolerante

  # Django: sempre inicia
  if pg "$DJANGO_PATTERN"; then
    log "Django já rodando na porta $DJANGO_PORT."
  else
    log "Iniciando Django em ${DJANGO_BIND} ..."
    nohup python manage.py runserver "$DJANGO_BIND" >>"$LOG_FILE" 2>&1 &
    sleep 2
    if pg "$DJANGO_PATTERN"; then
      ok "Django iniciado."
    else
      err "Falha ao iniciar Django (veja $LOG_FILE)."
      exit 1
    fi
  fi

  # Celery: só se enabled
  CELERY_ENABLED=$(get_celery_enabled)
  if [[ "$CELERY_ENABLED" == "True" ]]; then
    if pg "$CELERY_WORKER_PATTERN"; then
      log "Celery Worker já rodando."
    else
      log "Iniciando Celery Worker..."
      eval "$CELERY_WORKER_CMD" || { err "Falha no comando Celery Worker."; exit 1; }
      sleep 2
      if pg "$CELERY_WORKER_PATTERN"; then
        ok "Celery Worker iniciado."
      else
        err "Falha ao iniciar Worker (veja celery_worker.log)."
        exit 1
      fi
    fi

    if pg "$CELERY_BEAT_PATTERN"; then
      log "Celery Beat já rodando."
    else
      log "Iniciando Celery Beat..."
      eval "$CELERY_BEAT_CMD" || { err "Falha no comando Celery Beat."; exit 1; }
      sleep 2
      if pg "$CELERY_BEAT_PATTERN"; then
        ok "Celery Beat iniciado."
      else
        err "Falha ao iniciar Beat (veja celery_beat.log)."
        exit 1
      fi
    fi
  else
    warn "CELERY_ENABLED=False → Celery não iniciado (fallback ativo)."
  fi
}

stop() {
  cd "$APP_DIR" || warn "Falha ao entrar em $APP_DIR, continuando stop."
  activate_venv || warn "Venv falhou, continuando stop."
  log "Parando serviços..."
  stop_pattern "$DJANGO_PATTERN" "Django"
  stop_pattern "$CELERY_WORKER_PATTERN" "Celery Worker"
  stop_pattern "$CELERY_BEAT_PATTERN" "Celery Beat"
}

restart() {
  stop || warn "Stop falhou parcialmente, continuando restart."
  sleep 1
  start
}

status() {
  CELERY_ENABLED=$(get_celery_enabled)
  echo "Status (APP_DIR: $APP_DIR | CELERY_ENABLED=$CELERY_ENABLED):"
  echo "------------------------------------------"
  pg "$DJANGO_PATTERN" && ok "Django: Rodando" || err "Django: Parado"
  if [[ "$CELERY_ENABLED" == "True" ]]; then
    pg "$CELERY_WORKER_PATTERN" && ok "Worker: Rodando" || err "Worker: Parado"
    pg "$CELERY_BEAT_PATTERN" && ok "Beat: Rodando" || err "Beat: Parado"
  else
    warn "Celery: Desativado"
  fi
  echo "------------------------------------------"
  echo "Logs: $LOG_DIR | Manager: $LOG_FILE"
}

inspect() {
  cd "$APP_DIR" || { err "Falha ao entrar em $APP_DIR"; return 1; }
  if ! activate_venv; then return 1; fi
  log "Inspecionando Celery..."
  echo "--- Ativas ---"
  celery -A core.celery inspect active || warn "Falha (worker inativo?)."
  echo "--- Agendadas ---"
  celery -A core.celery inspect scheduled || warn "Falha."
  echo "--- Reservadas ---"
  celery -A core.celery inspect reserved || warn "Falha."
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) restart ;;
  status) status ;;
  inspect) inspect ;;
  *)
    err "Uso: $0 {start|stop|restart|status|inspect}"
    exit 1
    ;;
esac