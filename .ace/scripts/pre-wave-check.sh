#!/bin/bash
# pre-wave-check.sh — Valida compilação, bootstrap e health check do projeto
#
# Executa 3 verificações:
#   1. BUILD:   tsc --noEmit, npm run build, go build, etc.
#   2. BOOT:    Inicia a aplicação e verifica se sobe
#   3. HEALTH:  Verifica se o endpoint de health responde
#
# Uso:
#   .ace/scripts/pre-wave-check.sh                    # todas as verificações
#   .ace/scripts/pre-wave-check.sh --build-only        # só compilação
#   .ace/scripts/pre-wave-check.sh --boot-only         # só bootstrap
#   .ace/scripts/pre-wave-check.sh --health-only       # só health check
#   .ace/scripts/pre-wave-check.sh --setup-cmd "..."   # comando de setup (npm install)
#   .ace/scripts/pre-wave-check.sh --build-cmd "..."   # comando de build customizado
#   .ace/scripts/pre-wave-check.sh --boot-cmd "..."    # comando de bootstrap customizado
#   .ace/scripts/pre-wave-check.sh --health-url "..."  # URL de health customizada
#   .ace/scripts/pre-wave-check.sh --health-port N     # porta do health check
#   .ace/scripts/pre-wave-check.sh --timeout N         # timeout em segundos (padrão: 15)
#
# Exit code:
#   0 — todas as verificações passaram
#   1 — alguma verificação falhou

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

# ── Configuração ──

BUILD_ONLY=false
BOOT_ONLY=false
HEALTH_ONLY=false
CUSTOM_BUILD=""
CUSTOM_BOOT=""
CUSTOM_HEALTH_URL=""
CUSTOM_HEALTH_PORT=""
CUSTOM_SETUP=""
TIMEOUT=15
PASS=0
FAIL=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --build-only)    BUILD_ONLY=true ;;
        --boot-only)     BOOT_ONLY=true ;;
        --health-only)   HEALTH_ONLY=true ;;
        --setup-cmd)     CUSTOM_SETUP="$2"; shift ;;
        --build-cmd)     CUSTOM_BUILD="$2"; shift ;;
        --boot-cmd)      CUSTOM_BOOT="$2"; shift ;;
        --health-url)    CUSTOM_HEALTH_URL="$2"; shift ;;
        --health-port)   CUSTOM_HEALTH_PORT="$2"; shift ;;
        --timeout)       TIMEOUT="$2"; shift ;;
        *) echo "❌ Opção desconhecida: $1"; exit 1 ;;
    esac
    shift
done

# ── Auto-detecção de stack ──

detect_stack() {
    if [[ -f "package.json" ]]; then
        if [[ -f "tsconfig.json" ]]; then
            echo "typescript"
        else
            echo "node"
        fi
    elif [[ -f "go.mod" ]]; then
        echo "go"
    elif [[ -f "Cargo.toml" ]]; then
        echo "rust"
    elif [[ -f "pyproject.toml" ]]; then
        echo "python"
    elif [[ -f "setup.py" ]]; then
        echo "python"
    elif [[ -f "Makefile" ]]; then
        echo "make"
    else
        echo "unknown"
    fi
}

detect_entry_point() {
    local stack="$1"
    case "$stack" in
        typescript|node)
            # Procura o entry point mais provável
            for candidate in dist/main.js dist/index.js dist/server.js src/main.ts src/index.ts app.py main.py; do
                [[ -f "$candidate" ]] && echo "$candidate" && return
            done
            # Lê do package.json se disponível
            if [[ -f "package.json" ]]; then
                local main
                main=$(python3 -c "import json; print(json.load(open('package.json')).get('main', ''))" 2>/dev/null || echo "")
                [[ -n "$main" ]] && echo "$main" && return
            fi
            echo "dist/main.js"  # palpite
            ;;
        go)
            echo "." ;;
        python)
            echo "main.py" ;;
        rust)
            echo "" ;;
        *)
            echo "" ;;
    esac
}

detect_health_port() {
    [[ -n "$CUSTOM_HEALTH_PORT" ]] && echo "$CUSTOM_HEALTH_PORT" && return
    # Tenta ler de .env ou variável de ambiente
    local port
    port=$(grep -E "^PORT=" .env 2>/dev/null | cut -d= -f2 | head -1 || echo "")
    [[ -n "$port" ]] && echo "$port" && return
    port=$(grep -E "^SERVER_PORT=" .env 2>/dev/null | cut -d= -f2 | head -1 || echo "")
    [[ -n "$port" ]] && echo "$port" && return
    port=$(grep -E "^APP_PORT=" .env 2>/dev/null | cut -d= -f2 | head -1 || echo "")
    [[ -n "$port" ]] && echo "$port" && return
    # Health check específicos por stack
    if [[ -f "package.json" ]]; then
        python3 -c "
import json
d=json.load(open('package.json'))
scripts=d.get('scripts',{})
for k in ['start','dev','serve']:
    s=scripts.get(k,'')
    if 'PORT=' in s or '--port' in s:
        import re; m=re.search(r'(?:PORT=|--port\s+)(\d+)',s)
        if m: print(m.group(1)); exit(0)
print('3000')  # fallback Next.js/NestJS
" 2>/dev/null || echo "3000"
    else
        echo "3000"
    fi
}

# ── Verificações ──

check_build() {
    echo ""
    echo "🔧 [1/3] Compilação"
    echo "────────────────────"

    if [[ -n "$CUSTOM_BUILD" ]]; then
        echo "   Comando: $CUSTOM_BUILD"
        if eval "$CUSTOM_BUILD" 2>&1; then
            echo "   ✅ Compilação OK"
            PASS=$((PASS + 1))
        else
            echo "   ❌ Compilação FALHOU"
            FAIL=$((FAIL + 1))
        fi
        return
    fi

    local stack
    stack=$(detect_stack)
    echo "   Stack detectado: $stack"

    case "$stack" in
        typescript)
            # Setup se necessário
            if [[ ! -d "node_modules" ]] && [[ -n "$CUSTOM_SETUP" ]]; then
                echo "   Setup: $CUSTOM_SETUP"
                eval "$CUSTOM_SETUP" 2>&1 || true
            fi
            if npx tsc --noEmit 2>&1; then
                echo "   ✅ tsc --noEmit OK"
                PASS=$((PASS + 1))
            else
                echo "   ❌ tsc --noEmit FALHOU"
                FAIL=$((FAIL + 1))
            fi
            ;;
        node)
            if npm run build 2>&1; then
                echo "   ✅ npm run build OK"
                PASS=$((PASS + 1))
            else
                echo "   ❌ npm run build FALHOU"
                FAIL=$((FAIL + 1))
            fi
            ;;
        go)
            if go build ./... 2>&1; then
                echo "   ✅ go build ./... OK"
                PASS=$((PASS + 1))
            else
                echo "   ❌ go build ./... FALHOU"
                FAIL=$((FAIL + 1))
            fi
            ;;
        rust)
            if cargo build 2>&1; then
                echo "   ✅ cargo build OK"
                PASS=$((PASS + 1))
            else
                echo "   ❌ cargo build FALHOU"
                FAIL=$((FAIL + 1))
            fi
            ;;
        python)
            if python3 -m compileall . -q 2>&1; then
                echo "   ✅ compileall OK"
                PASS=$((PASS + 1))
            else
                echo "   ❌ compileall FALHOU"
                FAIL=$((FAIL + 1))
            fi
            ;;
        make)
            if make build 2>&1; then
                echo "   ✅ make build OK"
                PASS=$((PASS + 1))
            else
                echo "   ❌ make build FALHOU"
                FAIL=$((FAIL + 1))
            fi
            ;;
        *)
            echo "   ⚠️  Stack não reconhecido. Pule com --build-cmd ou remova com --boot-only."
            ;;
    esac
}

check_boot() {
    echo ""
    echo "🚀 [2/3] Bootstrap"
    echo "────────────────────"

    if [[ -n "$CUSTOM_BOOT" ]]; then
        echo "   Comando: $CUSTOM_BOOT"
        # Executa em background, espera, verifica se subiu, mata
        eval "$CUSTOM_BOOT" &
        local boot_pid=$!
        sleep 3
        if kill -0 "$boot_pid" 2>/dev/null; then
            echo "   ✅ Aplicação iniciou (PID $boot_pid)"
            PASS=$((PASS + 1))
            # Deixa rodando para o health check
            echo "$boot_pid" > /tmp/.llc-boot-pid
        else
            wait "$boot_pid"
            local exit_code=$?
            if [[ $exit_code -eq 0 ]]; then
                echo "   ✅ Bootstrap concluído"
                PASS=$((PASS + 1))
            else
                echo "   ❌ Bootstrap FALHOU (exit code: $exit_code)"
                FAIL=$((FAIL + 1))
            fi
        fi
        return
    fi

    local stack
    stack=$(detect_stack)

    local entry
    entry=$(detect_entry_point "$stack")

    if [[ -z "$entry" ]]; then
        echo "   ⚠️  Entry point não detectado. Pule com --boot-cmd."
        return
    fi

    echo "   Entry point: $entry"

    local boot_pid=""
    case "$stack" in
        typescript|node)
            if [[ "$entry" == *.ts ]]; then
                npx ts-node "$entry" &
                boot_pid=$!
            elif [[ -f "$entry" ]]; then
                node "$entry" &
                boot_pid=$!
            elif [[ -f "package.json" ]]; then
                npm start &
                boot_pid=$!
            fi
            ;;
        go)
            go run . &
            boot_pid=$!
            ;;
        python)
            if [[ "$entry" == *"uvicorn"* ]] || [[ "$entry" == *"fastapi"* ]]; then
                eval "$entry" &
            elif [[ -f "$entry" ]]; then
                python3 "$entry" &
            else
                echo "   ⚠️  Entry point não encontrado: $entry"
                return
            fi
            boot_pid=$!
            ;;
        *)
            echo "   ⚠️  Bootstrap automático não suportado para $stack. Use --boot-cmd."
            return
            ;;
    esac

    if [[ -n "$boot_pid" ]]; then
        sleep "$TIMEOUT"
        if kill -0 "$boot_pid" 2>/dev/null; then
            echo "   ✅ Aplicação iniciou (PID $boot_pid)"
            PASS=$((PASS + 1))
            echo "$boot_pid" > /tmp/.llc-boot-pid
        else
            wait "$boot_pid"
            local exit_code=$?
            if [[ $exit_code -eq 0 ]]; then
                echo "   ✅ Bootstrap concluído"
                PASS=$((PASS + 1))
            else
                echo "   ❌ Bootstrap FALHOU (exit code: $exit_code)"
                FAIL=$((FAIL + 1))
            fi
        fi
    fi
}

check_health() {
    echo ""
    echo "❤️  [3/3] Health Check"
    echo "───────────────────────"

    local port
    port=$(detect_health_port)

    local url="${CUSTOM_HEALTH_URL:-http://localhost:$port/api/v1/health}"

    echo "   URL: $url"

    # Aguarda o servidor ficar pronto (até TIMEOUT segundos)
    local waited=0
    local interval=1
    while [[ $waited -lt $TIMEOUT ]]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo "   ✅ Health check OK ($url)"
            PASS=$((PASS + 1))
            return
        fi
        sleep "$interval"
        waited=$((waited + interval))
    done

    echo "   ❌ Health check FALHOU ($url — sem resposta em ${TIMEOUT}s)"
    FAIL=$((FAIL + 1))
}

cleanup() {
    if [[ -f /tmp/.llc-boot-pid ]]; then
        local pid
        pid=$(cat /tmp/.llc-boot-pid 2>/dev/null || echo "")
        if [[ -n "$pid" ]]; then
            kill "$pid" 2>/dev/null || true
        fi
        rm -f /tmp/.llc-boot-pid
    fi
}

trap cleanup EXIT

# ── Execução ──

echo ""
echo "════════════════════════════════════════════"
echo "  🔍 Pré-Wave Check — Validação de Prontidão"
echo "════════════════════════════════════════════"

# Setup (opcional)
if [[ -n "$CUSTOM_SETUP" ]]; then
    echo ""
    echo "📦 Setup: $CUSTOM_SETUP"
    eval "$CUSTOM_SETUP" 2>&1
fi

if [[ "$BUILD_ONLY" == false && "$BOOT_ONLY" == false && "$HEALTH_ONLY" == false ]]; then
    check_build
    check_boot
    check_health
elif [[ "$BUILD_ONLY" == true ]]; then
    check_build
elif [[ "$BOOT_ONLY" == true ]]; then
    check_boot
elif [[ "$HEALTH_ONLY" == true ]]; then
    check_health
fi

cleanup

echo ""
echo "════════════════════════════════════════════"
echo "  Resultado: $PASS passaram, $FAIL falharam"
echo "════════════════════════════════════════════"

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
exit 0
