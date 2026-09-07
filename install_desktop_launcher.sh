#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
desktop_dir="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
mkdir -p "$desktop_dir"
launcher="$desktop_dir/KSA ENGINE.desktop"

cat > "$launcher" <<EOF
[Desktop Entry]
Type=Application
Name=KSA ENGINE
Comment=Open the KSA ENGINE game creator
Exec=$project_dir/launch_ksa_engine.sh
Path=$project_dir
Icon=$project_dir/assets/ksa-engine-k.svg
Terminal=true
Categories=Game;Development;
StartupWMClass=KSA ENGINE
EOF

chmod +x "$launcher" "$project_dir/launch_ksa_engine.sh"
printf 'Installed: %s\n' "$launcher"
