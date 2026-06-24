param(
    [switch]$Yes
)

$ErrorActionPreference = "Stop"

if (-not $Yes) {
    Write-Host "This reset removes Docker containers and the postgres volume."
    Write-Host "Run scripts/dev/reset.ps1 -Yes to confirm."
    exit 1
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

docker compose down -v
Write-Host "Docker containers and volumes removed. Tracked project files were not deleted."
