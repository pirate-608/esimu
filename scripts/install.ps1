# esimu Windows installer
# Downloads latest release from GitHub and installs to ~/.local/bin
#
# Usage:
#   .\install.ps1 -Repo owner/name              (run as file)
#   $env:ESIMU_REPO = "owner/name"; irm ... | iex (piped from web)
#   irm ... | iex                                 (auto-detect from CWD git remote)

param(
  [string]$Repo = "",
  [string]$Version = "latest"
)

# Suppress progress bars that break Invoke-WebRequest in some shells
$ProgressPreference = "SilentlyContinue"
$ErrorActionPreference = "Stop"

# ── Resolve repository ──────────────────────────────────────────────
if (-not $Repo) { $Repo = $env:ESIMU_REPO }

if (-not $Repo) {
  # Try CWD git remote (works both piped and as-file)
  $remote = git -C (Get-Location) remote get-url origin 2>$null
  if ($remote -match "github\.com[:/](.+?)/(.+?)(\.git)?$") {
    $Repo = "$($Matches[1])/$($Matches[2])"
  }
}

if (-not $Repo) {
  # Hardcoded default — the repo this script lives in
  $Repo = "pirate-608/esimu"
  Write-Host "Repository: $Repo (default)" -ForegroundColor Cyan
} else {
  Write-Host "Repository: $Repo" -ForegroundColor Cyan
}

# ── Determine download URL ──────────────────────────────────────────
if ($Version -eq "latest") {
  $apiUrl = "https://api.github.com/repos/$Repo/releases/latest"
} else {
  $apiUrl = "https://api.github.com/repos/$Repo/releases/tags/$Version"
}

Write-Host "Fetching release info..." -ForegroundColor Cyan
try {
  $release = Invoke-RestMethod -Uri $apiUrl -Headers @{ "Accept" = "application/vnd.github+json" }
} catch {
  Write-Host "Failed to fetch release: $_" -ForegroundColor Red
  exit 1
}

$asset = $release.assets | Where-Object { $_.name -eq "esimu-windows-x64.zip" }
if (-not $asset) {
  Write-Host "Asset 'esimu-windows-x64.zip' not found in release $($release.tag_name)" -ForegroundColor Red
  exit 1
}

# ── Download & extract ──────────────────────────────────────────────
$tmp = Join-Path $env:TEMP "esimu-install"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

$zipPath = Join-Path $tmp "esimu.zip"
Write-Host "Downloading $($asset.name) ($([math]::Round($asset.size / 1KB, 1)) KB)..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath

Write-Host "Extracting..." -ForegroundColor Cyan
Expand-Archive -Path $zipPath -DestinationPath $tmp -Force

# ── Install ─────────────────────────────────────────────────────────
$binDir = Join-Path $env:USERPROFILE ".local\bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null

$exe = Get-ChildItem -Path $tmp -Name "esimu.exe" -Recurse | Select-Object -First 1
if (-not $exe) {
  Write-Host "esimu.exe not found in archive" -ForegroundColor Red
  exit 1
}

$src = Join-Path $tmp $exe
$dst = Join-Path $binDir "esimu.exe"
Copy-Item -Path $src -Destination $dst -Force

Remove-Item -Recurse -Force $tmp

Write-Host ""
Write-Host "esimu v$($release.tag_name) installed to $dst" -ForegroundColor Green

# ── PATH check ──────────────────────────────────────────────────────
$inPath = ($env:PATH -split ";") -contains $binDir
if (-not $inPath) {
  Write-Host ""
  Write-Host "Add to PATH to use from anywhere:" -ForegroundColor Yellow
  Write-Host "  [Environment]::SetEnvironmentVariable('PATH', '$env:PATH;$binDir', 'User')" -ForegroundColor White
  Write-Host ""
  Write-Host "Or add manually via: System Properties → Environment Variables → Path" -ForegroundColor Yellow
}

Write-Host "Run 'esimu --version' to verify." -ForegroundColor Cyan
