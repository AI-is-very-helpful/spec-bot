# Run Azure Functions with venv (Windows PowerShell)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if venv exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

# Activate venv
& ".venv\Scripts\Activate.ps1"

# Install dependencies if needed
try {
    python -c "import azure.functions" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing dependencies..."
        pip install -r requirements.txt
    }
} catch {
    Write-Host "Installing dependencies..."
    pip install -r requirements.txt
}

# Run Azure Functions
Write-Host "Starting Azure Functions..."
func start
