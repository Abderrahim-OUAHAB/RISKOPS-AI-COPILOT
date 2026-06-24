$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

python scripts/dev/demo_seed.py
exit $LASTEXITCODE
