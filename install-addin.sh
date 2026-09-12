#!/usr/bin/env bash
set -euo pipefail

repo_zip="https://github.com/barbatron/fusion-360-glb-export-add-in/archive/refs/heads/main.zip"
addin_name="Export As Glb"
addin_root="${HOME}/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns"
zip_path="${TMPDIR:-/tmp}/fusion-360-glb-export-add-in.zip"
extract_root="${TMPDIR:-/tmp}/fusion-360-glb-export-add-in"

rm -rf "$extract_root"
mkdir -p "$addin_root"
curl -L "$repo_zip" -o "$zip_path"
unzip -q -o "$zip_path" -d "$extract_root"

repo_root="$extract_root/fusion-360-glb-export-add-in-main"
source_dir="$repo_root/$addin_name"
target_dir="$addin_root/$addin_name"

if [[ ! -d "$source_dir" ]]; then
  echo "Expected add-in folder not found in zip: $source_dir" >&2
  exit 1
fi

rm -rf "$target_dir"
cp -R "$source_dir" "$target_dir"
echo "Installed '$addin_name' to: $target_dir"
