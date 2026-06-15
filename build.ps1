# Build propatch.exe as a standalone single-file executable
# Output: dist\propatch.exe

$ErrorActionPreference = "Stop"

Write-Host "Building propatch.exe..." -ForegroundColor Cyan

py -m PyInstaller propatch.spec --clean

if ($LASTEXITCODE -eq 0) {
    $size = (Get-Item "dist\propatch.exe").Length / 1MB
    Write-Host ("Build complete: dist\propatch.exe  ({0:F1} MB)" -f $size) -ForegroundColor Green
} else {
    Write-Host "Build failed." -ForegroundColor Red
    exit 1
}
