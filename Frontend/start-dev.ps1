$env:Path = "C:\Users\thang\.local\node;" + $env:Path
Write-Host "Starting Prior Authorization Intelligence dev server on port 3000..." -ForegroundColor Cyan
npm run dev
