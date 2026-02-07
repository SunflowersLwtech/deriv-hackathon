param(
    [string]$EnvName = $(if ($env:TRADEIQ_CONDA_ENV) { $env:TRADEIQ_CONDA_ENV } else { "tradeiq" }),
    [string]$Host = $(if ($env:TRADEIQ_HOST) { $env:TRADEIQ_HOST } else { "127.0.0.1" }),
    [int]$Port = $(if ($env:TRADEIQ_PORT) { [int]$env:TRADEIQ_PORT } else { 8000 })
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$BackendDir = Join-Path $ProjectRoot "backend"

$condaCmd = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaCmd) {
    throw "conda not found in PATH."
}

# Initialize conda for this PowerShell session.
$condaHook = conda shell.powershell hook | Out-String
Invoke-Expression $condaHook

conda activate $EnvName

if ($env:CONDA_DEFAULT_ENV -ne $EnvName) {
    throw "Failed to activate conda env '$EnvName'. Current: '$($env:CONDA_DEFAULT_ENV)'"
}

Write-Host "Conda env active: $($env:CONDA_DEFAULT_ENV)"
Write-Host "Python: $((Get-Command python).Source)"

Set-Location $BackendDir
python manage.py runserver "$Host`:$Port"
