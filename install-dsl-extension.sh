#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
EXTENSION_DIR="$ROOT_DIR/vscode-dsl-language"
EXTENSION_ID="sottomonte.omniport-dsl-language"
VSIX_FILE="$(mktemp "${TMPDIR:-/tmp}/${EXTENSION_ID}.XXXXXX.vsix")"

cleanup() {
    rm -f -- "$VSIX_FILE"
}
trap cleanup EXIT

if ! command -v code >/dev/null 2>&1; then
    echo "Errore: il comando 'code' non è disponibile nel PATH." >&2
    exit 1
fi

if [[ ! -f "$EXTENSION_DIR/package.json" ]]; then
    echo "Errore: estensione non trovata in $EXTENSION_DIR" >&2
    exit 1
fi

echo "Creo il pacchetto VSIX..."
(
    cd -- "$EXTENSION_DIR"
    printf 'y\n' | npx --yes @vscode/vsce package \
        --allow-missing-repository \
        --out "$VSIX_FILE"
)

echo "Installo $EXTENSION_ID..."
code --install-extension "$VSIX_FILE" --force

if code --list-extensions | grep -Fxq "$EXTENSION_ID"; then
    echo "Installazione completata: $EXTENSION_ID"
    echo "Esegui 'Developer: Reload Window' da VS Code se i colori non compaiono subito."
else
    echo "Errore: l'estensione non risulta installata." >&2
    exit 1
fi
