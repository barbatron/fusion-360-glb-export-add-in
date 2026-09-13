$ErrorActionPreference = 'Stop'

$distDir = Join-Path $PSScriptRoot 'dist'
$zipPath = Join-Path $distDir 'Export-As-Glb-submission.zip'

$requiredFiles = @(
    'Export As Glb.manifest',
    'Export As Glb.py'
)

$optionalFiles = @(
    'LICENSE',
    'README.md',
    'addon-icon.svg'
)

foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $PSScriptRoot $file
    if (-not (Test-Path $fullPath -PathType Leaf)) {
        throw "Missing required file: $file"
    }
}

if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}

if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

$filesToPack = @()
foreach ($file in ($requiredFiles + $optionalFiles)) {
    $fullPath = Join-Path $PSScriptRoot $file
    if (Test-Path $fullPath -PathType Leaf) {
        $filesToPack += $fullPath
    }
}

Compress-Archive -Path $filesToPack -DestinationPath $zipPath -Force
Write-Host "Created $zipPath"
