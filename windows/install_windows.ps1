# Run PowerShell as Administrator.
$ErrorActionPreference = "Stop"

$InstallDir = "C:\Program Files\NetworkMonitor"
$TaskName = "Network Security Monitor"

Write-Host "[1/7] Checking Python..."
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python 3.11+ is required."
}

Write-Host "[2/7] Checking Nmap..."
$nmap = Get-Command nmap -ErrorAction SilentlyContinue
if (-not $nmap) {
    throw "Nmap is required. Install Nmap for Windows first."
}

Write-Host "[3/7] Checking Npcap..."
$npcap = Get-Service npcap -ErrorAction SilentlyContinue
if (-not $npcap) {
    throw "Npcap is required for packet capture. Install Npcap first."
}

Write-Host "[4/7] Copying project..."
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$SourceDir = Split-Path -Parent $PSScriptRoot
Copy-Item "$SourceDir\*" $InstallDir -Recurse -Force

Write-Host "[5/7] Creating virtual environment..."
python -m venv "$InstallDir\.venv"

& "$InstallDir\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$InstallDir\.venv\Scripts\pip.exe" install -r "$InstallDir\requirements.txt"

if (-not (Test-Path "$InstallDir\.env")) {
    Copy-Item "$InstallDir\.env.example" "$InstallDir\.env"
}

Write-Host "[6/7] Registering Scheduled Task..."
$pythonExe = "$InstallDir\.venv\Scripts\python.exe"
$mainPy = "$InstallDir\main.py"

$action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "`"$mainPy`"" `
    -WorkingDirectory $InstallDir

$trigger = New-ScheduledTaskTrigger -AtStartup

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -RestartCount 10 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Force | Out-Null

Write-Host "[7/7] Starting..."
Start-ScheduledTask -TaskName $TaskName

Write-Host ""
Write-Host "Installation complete."
Write-Host "Edit: $InstallDir\config.json"
Write-Host "Edit: $InstallDir\.env"
Write-Host "Task: $TaskName"
