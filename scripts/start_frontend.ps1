param(
    [string]$EnvName = $(if ($env:TRADEIQ_CONDA_ENV) { $env:TRADEIQ_CONDA_ENV } else { "tradeiq" }),
    [string]$Host = $(if ($env:TRADEIQ_FRONTEND_HOST) { $env:TRADEIQ_FRONTEND_HOST } else { "127.0.0.1" }),
    [int]$Port = $(if ($env:TRADEIQ_FRONTEND_PORT) { [int]$env:TRADEIQ_FRONTEND_PORT } else { 3000 })
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$FrontendDir = Join-Path $ProjectRoot "frontend"

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

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm not found in PATH."
}

Write-Host "Conda env active: $($env:CONDA_DEFAULT_ENV)"
Write-Host "Python: $((Get-Command python).Source)"
Write-Host "Node: $((Get-Command node).Source)"
Write-Host "NPM: $((Get-Command npm).Source)"

Set-Location $FrontendDir

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    if (Test-Path "package-lock.json") {
        npm ci
    } else {
        npm install
    }
}

npm run dev -- --hostname $Host --port $Port
