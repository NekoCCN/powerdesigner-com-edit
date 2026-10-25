# PowerShell installer for powerdesigner-com-edit Agent Skill
[CmdletBinding()]
param (
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"

Write-Host "Installing powerdesigner-com-edit Agent Skill..." -ForegroundColor Cyan

$RepoUrl = "https://github.com/NekoCCN/powerdesigner-com-edit.git"
$TempDir = Join-Path $env:TEMP "pd-com-edit-install"

if (Test-Path $TempDir) {
    Remove-Item -Recurse -Force $TempDir
}

Write-Host "Cloning repository..." -ForegroundColor Gray
git clone --depth 1 $RepoUrl $TempDir

$HomeDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)

$Targets = @()
if ($Target -eq "all" -or $Target -eq "gemini") {
    $Targets += (Join-Path $HomeDir ".gemini\skills\powerdesigner-com-edit")
}
if ($Target -eq "all" -or $Target -eq "claude") {
    $Targets += (Join-Path $HomeDir ".claude\skills\powerdesigner-com-edit")
}

foreach ($dest in $Targets) {
    $parent = Split-Path -Parent $dest
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    if (Test-Path $dest) {
        Remove-Item -Recurse -Force $dest
    }
    Copy-Item -Path $TempDir -Destination $dest -Recurse -Force
    # Clean up .git in destination
    $gitFolder = Join-Path $dest ".git"
    if (Test-Path $gitFolder) {
        Remove-Item -Recurse -Force $gitFolder
    }
    Write-Host "Installed skill to: $dest" -ForegroundColor Green
}

Remove-Item -Recurse -Force $TempDir
Write-Host "Skill installation completed successfully!" -ForegroundColor Green
Write-Host "You can now prompt Claude Code or Antigravity: 'Use powerdesigner-com-edit to check diagram overlaps.'" -ForegroundColor Yellow
