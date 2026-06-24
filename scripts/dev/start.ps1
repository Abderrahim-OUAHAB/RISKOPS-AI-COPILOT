$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

Write-Host "Starting AI RiskOps Copilot with Docker..."
$elapsed = Measure-Command { docker compose up -d --build }
Write-Host "Docker build/start completed in $([math]::Round($elapsed.TotalSeconds, 2)) seconds."

function Wait-Url {
    param(
        [string]$Name,
        [string]$Url,
        [int]$TimeoutSeconds = 120
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -lt 500) {
                Write-Host "$Name ready: $($response.StatusCode)"
                return
            }
        }
        catch {
            Start-Sleep -Seconds 3
        }
    }

    Write-Host "$Name not ready after $TimeoutSeconds seconds."
}

Wait-Url -Name "Backend" -Url "http://localhost:8000/health"
Wait-Url -Name "Streamlit" -Url "http://localhost:8501"
Wait-Url -Name "Airflow" -Url "http://localhost:8080/login/"

& "$PSScriptRoot\healthcheck.ps1"

Write-Host ""
Write-Host "Useful URLs"
Write-Host "- FastAPI docs: http://localhost:8000/docs"
Write-Host "- Streamlit: http://localhost:8501"
Write-Host "- Airflow: http://localhost:8080"
Write-Host "- Health: http://localhost:8000/health"
Write-Host "- Ready: http://localhost:8000/ready"
Write-Host "- MLflow: local ./mlruns directory"
