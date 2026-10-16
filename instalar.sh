#!/bin/bash
# Empacota o jogo com a biblioteca Python do SDK e instala no console.
#
#   ./instalar.sh [host-ssh] [pasta-do-sdk]
#   padrão: r36s e ../r36s-a11y-sdk (clone de github.com/gogabs/r36s-a11y-sdk)
#
# Não reinicia nada: a galeria percebe o jogo novo sozinha. Com o jogo aberto,
# não instala, porque ele carrega os sons sob demanda da pasta instalada.
set -euo pipefail
HOST=${1:-r36s}
HERE=$(cd "$(dirname "$0")" && pwd)
SDK=${2:-$HERE/../r36s-a11y-sdk}
SDK_PY="$SDK/python/r36s_a11y"
if [ ! -d "$SDK_PY" ]; then
  if [ "$#" -ge 2 ]; then
    echo "SDK não encontrado no caminho solicitado: $SDK"; exit 1
  fi
  SDK_PY="$HERE/r36s_a11y"
fi
[ -d "$SDK_PY" ] || { echo "SDK não encontrado."; exit 1; }
echo "SDK selecionada: $SDK_PY"

if ssh "$HOST" 'for p in /proc/[0-9]*; do readlink "$p/cwd"; done 2>/dev/null | grep -q "^/opt/a11y/games/comes-e-bebes"'; then
  echo "O Comes e Bebes está aberto no console. Feche o jogo e rode de novo."
  exit 1
fi

PKG=$(mktemp -d)
trap 'rm -rf "$PKG"' EXIT
mkdir -p "$PKG/comes-e-bebes"
cp -r "$HERE/game.json" "$HERE/main.py" "$HERE/comes" "$HERE/sounds" "$SDK_PY" "$PKG/comes-e-bebes/"
find "$PKG" -name __pycache__ -prune -exec rm -rf {} +

tar -C "$PKG" -czf - comes-e-bebes | ssh "$HOST" '
  set -e; cd /opt/a11y/games
  rm -rf .comes-e-bebes.novo && mkdir .comes-e-bebes.novo
  tar -xzf - -C .comes-e-bebes.novo
  rm -rf comes-e-bebes && mv .comes-e-bebes.novo/comes-e-bebes . && rmdir .comes-e-bebes.novo
  echo "instalado: $(ls comes-e-bebes/sounds | wc -l) sons"; df -h /opt/a11y | tail -1'
