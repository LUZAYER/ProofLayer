#!/usr/bin/env bash
# ==============================================================================
# ProofLayer (প্রুফলেয়ার) — Enterprise Security Gateway & Console Launcher
# Dynamically discovers and binds to any available port starting from 4000
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONSOLE_DIR="$SCRIPT_DIR/apps/console"
START_PORT=4000
DEV_MODE=false
FORCE_BUILD=false
START_GATEWAY=false
GATEWAY_START_PORT=8001
GATEWAY_PID=""

# ANSI Color codes
BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Print Banner
echo -e "${CYAN}${BOLD}"
echo "  ____                 __ _                                "
echo " |  _ \ _ __ ___   ___/ _| |    __ _ _   _  ___ _ __       "
echo " | |_) | '__/ _ \ / _ \ |_| |   / _\` | | | |/ _ \ '__|     "
echo " |  __/| | | (_) | (_) |  _| |__| (_| | |_| |  __/ |       "
echo " |_|   |_|  \___/ \___/|_| |_____\__,_|\__, |\___|_|       "
echo "                                       |___/               "
echo "   প্রুফলেয়ার · Multilingual AI Agent Governance Gateway    "
echo -e "${NC}"

# Parse command line options
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dev|-d)
      DEV_MODE=true
      shift
      ;;
    --build|-b)
      FORCE_BUILD=true
      shift
      ;;
    --gateway|-g|--full)
      START_GATEWAY=true
      shift
      ;;
    --port|-p)
      START_PORT="$2"
      shift 2
      ;;
    --help|-h)
      echo -e "${BOLD}Usage:${NC} ./up.sh [options]"
      echo ""
      echo "Options:"
      echo "  --port, -p <port>     Start scanning from custom port (default: 4000)"
      echo "  --dev, -d             Run Next.js in development mode (hot-reloading)"
      echo "  --build, -b           Force a production build before starting"
      echo "  --gateway, -g, --full Also launch the FastAPI gateway on an available port"
      echo "  --help, -h            Show this help dialog"
      exit 0
      ;;
    *)
      echo -e "${YELLOW}Warning: Unknown option '$1'. Ignoring.${NC}"
      shift
      ;;
  esac
done

# Function: Find next available TCP port
find_available_port() {
  local target_port="${1:-4000}"
  python3 -c "
import socket, sys
start = int(sys.argv[1])
port = start
while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', port))
            print(port)
            break
    except OSError:
        port += 1
" "$target_port"
}

# Cleanup on exit or Ctrl+C
cleanup() {
  echo ""
  echo -e "${YELLOW}Shutting down ProofLayer services...${NC}"
  if [[ -n "$GATEWAY_PID" ]]; then
    kill "$GATEWAY_PID" 2>/dev/null || true
  fi
  echo -e "${GREEN}Services stopped cleanly.${NC}"
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 1. Discover available port for the Web Console starting from $START_PORT (>= 4000)
echo -e "${CYAN}→ Scanning for available port starting from ${BOLD}${START_PORT}${NC}${CYAN}...${NC}"
AVAILABLE_PORT=$(find_available_port "$START_PORT")

if [[ "$AVAILABLE_PORT" -ne "$START_PORT" ]]; then
  echo -e "${YELLOW}  Port ${START_PORT} is currently occupied.${NC}"
fi
echo -e "${GREEN}✔ Bound to available port: ${BOLD}${AVAILABLE_PORT}${NC}"

# 2. Check and start backend gateway if requested
GATEWAY_URL="http://localhost:8000"
if [[ "$START_GATEWAY" == true ]]; then
  GW_PORT=$(find_available_port "$GATEWAY_START_PORT")
  echo -e "${CYAN}→ Launching FastAPI Gateway on port ${BOLD}${GW_PORT}${NC}${CYAN}...${NC}"
  PYTHONPATH="$SCRIPT_DIR" python3 -m uvicorn services.gateway.app:app --host 0.0.0.0 --port "$GW_PORT" > /dev/null 2>&1 &
  GATEWAY_PID=$!
  GATEWAY_URL="http://localhost:$GW_PORT"
  echo -e "${GREEN}✔ FastAPI Gateway running at ${BOLD}${GATEWAY_URL}${NC}"
fi

# 3. Ensure console dependencies are installed
if [[ ! -d "$CONSOLE_DIR/node_modules" ]]; then
  echo -e "${CYAN}→ Installing npm dependencies in apps/console...${NC}"
  (cd "$CONSOLE_DIR" && npm install)
fi

# 4. Handle production build if necessary
if [[ "$DEV_MODE" == false ]]; then
  if [[ ! -d "$CONSOLE_DIR/.next" || "$FORCE_BUILD" == true ]]; then
    echo -e "${CYAN}→ Building Next.js production bundle...${NC}"
    (cd "$CONSOLE_DIR" && npm run build)
  fi
fi

# 5. Launch the Web Console
echo ""
echo -e "${GREEN}${BOLD}========================================================================${NC}"
echo -e "${GREEN}${BOLD}  ProofLayer (প্রুফলেয়ার) is UP and ready!${NC}"
echo -e "${GREEN}${BOLD}  Console & Masterclass Home: ${CYAN}http://localhost:${AVAILABLE_PORT}${NC}"
if [[ "$START_GATEWAY" == true ]]; then
  echo -e "${GREEN}${BOLD}  FastAPI Gateway API Docs:   ${CYAN}${GATEWAY_URL}/docs${NC}"
fi
echo -e "${GREEN}${BOLD}========================================================================${NC}"
echo -e "${BLUE}Press ${BOLD}Ctrl+C${NC}${BLUE} at any time to stop the server.${NC}"
echo ""

cd "$CONSOLE_DIR"
export NEXT_PUBLIC_GATEWAY_URL="$GATEWAY_URL"
export PORT="$AVAILABLE_PORT"

if [[ "$DEV_MODE" == true ]]; then
  exec ./node_modules/.bin/next dev -p "$AVAILABLE_PORT"
else
  exec ./node_modules/.bin/next start -p "$AVAILABLE_PORT"
fi
