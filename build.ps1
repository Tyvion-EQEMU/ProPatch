# Build profetch.exe as a standalone single-file executable
# Output: dist\profetch.exe

$ErrorActionPreference = "Stop"

Write-Host "Building profetch.exe..." -ForegroundColor Cyan

py -m PyInstaller profetch.spec --clean

if ($LASTEXITCODE -eq 0) {
    $size = (Get-Item "dist\profetch.exe").Length / 1MB
    Write-Host ("Build complete: dist\profetch.exe  ({0:F1} MB)" -f $size) -ForegroundColor Green
} else {
    Write-Host "Build failed." -ForegroundColor Red
    exit 1
}
