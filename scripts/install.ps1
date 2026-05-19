[CmdletBinding()]
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "WindowsVoiceCreature"),
    [string]$RepoZipUrl = "https://github.com/monaxovdulov/windows-voice-creature/archive/refs/heads/main.zip",
    [switch]$WithVoiceModel,
    [switch]$Dev,
    [switch]$NoShortcut,
    [switch]$Start
)

$ErrorActionPreference = "Stop"
$InstallMarker = ".windows-voice-creature-install"

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-Windows {
    if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
        throw "This installer supports Windows 10/11 only."
    }
}

function Assert-Uv {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        throw "uv is required. Install uv first: https://docs.astral.sh/uv/"
    }
}

function Get-RepoRootFromScript {
    if ($PSScriptRoot) {
        $candidate = Split-Path -Parent $PSScriptRoot
        if (Test-Path -LiteralPath (Join-Path $candidate "pyproject.toml")) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    $current = (Get-Location).Path
    if (Test-Path -LiteralPath (Join-Path $current "pyproject.toml")) {
        return (Resolve-Path -LiteralPath $current).Path
    }

    return $null
}

function Assert-SafeInstallPath {
    param([string]$Path)

    $full = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetPathRoot($full)
    if ($full.TrimEnd("\") -eq $root.TrimEnd("\")) {
        throw "Refusing to use drive root as InstallDir: $full"
    }

    $profile = [System.IO.Path]::GetFullPath([Environment]::GetFolderPath("UserProfile"))
    if ($full.TrimEnd("\") -eq $profile.TrimEnd("\")) {
        throw "Refusing to use the user profile root as InstallDir: $full"
    }
}

function Install-FromZip {
    param(
        [string]$Destination,
        [string]$Url
    )

    Assert-SafeInstallPath $Destination

    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("windows-voice-creature-" + [guid]::NewGuid().ToString("N"))
    $zipPath = Join-Path $tempRoot "source.zip"
    New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

    try {
        Write-Step "Downloading source archive"
        Invoke-WebRequest -Uri $Url -OutFile $zipPath

        Write-Step "Extracting source"
        Expand-Archive -Path $zipPath -DestinationPath $tempRoot -Force
        $sourceRoot = Get-ChildItem -Path $tempRoot -Directory |
            Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "pyproject.toml") } |
            Select-Object -First 1

        if (-not $sourceRoot) {
            throw "Downloaded archive does not contain pyproject.toml."
        }

        if (Test-Path -LiteralPath $Destination) {
            $marker = Join-Path $Destination $InstallMarker
            if (-not (Test-Path -LiteralPath $marker)) {
                throw "InstallDir already exists and was not created by this installer: $Destination"
            }
            Write-Step "Replacing existing install directory"
            Remove-Item -LiteralPath $Destination -Recurse -Force
        }

        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        Copy-Item -Path (Join-Path $sourceRoot.FullName "*") -Destination $Destination -Recurse -Force
        New-Item -ItemType File -Force -Path (Join-Path $Destination $InstallMarker) | Out-Null
        return (Resolve-Path -LiteralPath $Destination).Path
    }
    finally {
        if (Test-Path -LiteralPath $tempRoot) {
            Remove-Item -LiteralPath $tempRoot -Recurse -Force
        }
    }
}

function Invoke-UvSync {
    param([string]$ProjectRoot)

    Push-Location $ProjectRoot
    try {
        if ($Dev) {
            Write-Step "Installing project with dev dependencies via uv"
            uv sync --extra dev
        }
        else {
            Write-Step "Installing project via uv"
            uv sync
        }
    }
    finally {
        Pop-Location
    }
}

function Install-VoiceModel {
    param([string]$ProjectRoot)

    $modelScript = Join-Path $ProjectRoot "scripts\download_vosk_model.ps1"
    if (-not (Test-Path -LiteralPath $modelScript)) {
        throw "Vosk model script not found: $modelScript"
    }

    Write-Step "Downloading Vosk Russian model"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $modelScript
}

function New-DesktopShortcut {
    param([string]$ProjectRoot)

    $startScript = Join-Path $ProjectRoot "scripts\start.ps1"
    $desktop = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktop "Windows Voice Creature.lnk"
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "powershell.exe"
    $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startScript`""
    $shortcut.WorkingDirectory = $ProjectRoot
    $shortcut.Description = "Start Windows Voice Creature"
    $shortcut.Save()
    Write-Host "Shortcut: $shortcutPath"
}

Assert-Windows
Assert-Uv

$repoRoot = Get-RepoRootFromScript
if ($repoRoot) {
    Write-Step "Using local repository: $repoRoot"
    $projectRoot = $repoRoot
}
else {
    $projectRoot = Install-FromZip -Destination $InstallDir -Url $RepoZipUrl
}

Invoke-UvSync -ProjectRoot $projectRoot

if ($WithVoiceModel) {
    Install-VoiceModel -ProjectRoot $projectRoot
}

if (-not $NoShortcut) {
    Write-Step "Creating desktop shortcut"
    New-DesktopShortcut -ProjectRoot $projectRoot
}

if ($Start) {
    Write-Step "Starting Windows Voice Creature"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projectRoot "scripts\start.ps1")
}

Write-Host ""
Write-Host "Installed to: $projectRoot" -ForegroundColor Green
Write-Host "Run: powershell -NoProfile -ExecutionPolicy Bypass -File `"$projectRoot\scripts\start.ps1`""
