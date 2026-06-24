$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

$checks = @(
    @{ Name = "Health"; Url = "http://localhost:8000/health" },
    @{ Name = "Ready"; Url = "http://localhost:8000/ready" },
    @{ Name = "Streamlit"; Url = "http://localhost:8501" },
    @{ Name = "Airflow"; Url = "http://localhost:8080/login/" }
)

foreach ($check in $checks) {
    try {
        $response = Invoke-WebRequest -Uri $check.Url -UseBasicParsing -TimeoutSec 10
        Write-Host "$($check.Name): $($response.StatusCode)"
    }
    catch {
        Write-Host "$($check.Name): unavailable - $($_.Exception.Message)"
    }
}

Write-Host ""
docker compose ps
