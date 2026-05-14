$ErrorActionPreference = "Stop"

$modelName = "vosk-model-small-ru-0.22"
$zipPath = Join-Path $PSScriptRoot "$modelName.zip"
$modelsDir = Join-Path (Split-Path $PSScriptRoot -Parent) "models"
$targetDir = Join-Path $modelsDir $modelName
$url = "https://alphacephei.com/vosk/models/$modelName.zip"

if (Test-Path $targetDir) {
    Write-Host "Model already exists: $targetDir"
    exit 0
}

New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null
Write-Host "Downloading $url"
Invoke-WebRequest -Uri $url -OutFile $zipPath

Write-Host "Extracting to $modelsDir"
Expand-Archive -Path $zipPath -DestinationPath $modelsDir -Force
Remove-Item $zipPath

Write-Host "Done: $targetDir"

