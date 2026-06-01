# Restart Zrok Share Script
$ZROK_EXE = Join-Path -Path $PSScriptRoot -ChildPath "zrok2.exe"
$TARGET_URL = "http://localhost:8501"

Write-Host "Starting zrok share for $TARGET_URL..." -ForegroundColor Cyan

# Start zrok in a new window to keep it running and visible
Start-Process -FilePath $ZROK_EXE -ArgumentList "share", "public", $TARGET_URL
