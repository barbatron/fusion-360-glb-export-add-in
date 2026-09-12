$ErrorActionPreference = 'Stop'
$repoZip = 'https://github.com/barbatron/fusion-360-glb-export-add-in/archive/refs/heads/main.zip'
$addinName = 'Export As Glb'
$addinRoot = Join-Path $env:APPDATA 'Autodesk\Autodesk Fusion 360\API\AddIns'
$zipPath = Join-Path $env:TEMP 'fusion-360-glb-export-add-in.zip'
$extractRoot = Join-Path $env:TEMP 'fusion-360-glb-export-add-in'

if (Test-Path $extractRoot) { Remove-Item -Recurse -Force $extractRoot }
if (!(Test-Path $addinRoot)) { New-Item -ItemType Directory -Path $addinRoot | Out-Null }
Invoke-WebRequest -Uri $repoZip -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $extractRoot -Force

$repoRoot = Join-Path $extractRoot 'fusion-360-glb-export-add-in-main'
$sourceDir = Join-Path $repoRoot $addinName
$targetDir = Join-Path $addinRoot $addinName

if (!(Test-Path $sourceDir)) { throw "Expected add-in folder not found in zip: $sourceDir" }
if (Test-Path $targetDir) { Remove-Item -Recurse -Force $targetDir }
Copy-Item -Path $sourceDir -Destination $targetDir -Recurse
Write-Host "Installed '$addinName' to: $targetDir"
