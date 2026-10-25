# PowerShell installer for powerdesigner-com-edit Agent Skill
[CmdletBinding()]
param (
    [ValidateSet("global", "project", "both")]
    [string]$Scope = "global",

    [ValidateSet("all", "gemini", "claude")]
    [string]$Target = "all",

    [string]$ProjectDir = $PWD.Path,

    [switch]$Link
)

$ErrorActionPreference = "Stop"

Write-Host "Installing powerdesigner-com-edit Agent Skill..." -ForegroundColor Cyan

$RepoRoot = $PSScriptRoot
if (-not $RepoRoot) {
    $RepoRoot = $PWD.Path
}

function Deploy-Skill([string]$Destination) {
    $parent = Split-Path -Parent $Destination
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    if (Test-Path $Destination) {
        Remove-Item -Recurse -Force $Destination
    }

    if ($Link) {
        New-Item -ItemType Junction -Path $Destination -Target $RepoRoot | Out-Null
        Write-Host "Linked skill to: $Destination" -ForegroundColor Green
    } else {
        $exclude = @(".git", "__pycache__", "build", "dist", "*.egg-info", ".vscode")
        Copy-Item -Path $RepoRoot -Destination $Destination -Recurse -Force
        foreach ($pattern in $exclude) {
            $matched = Join-Path $Destination $pattern
            if (Test-Path $matched) {
                Remove-Item -Recurse -Force $matched
            }
        }
        Write-Host "Installed skill to: $Destination" -ForegroundColor Green
    }
}

# 1. Project-Level Deployment
if ($Scope -eq "project" -or $Scope -eq "both") {
    Write-Host "`nDeploying to Project Level: $ProjectDir" -ForegroundColor Cyan
    $projectTargets = @(
        (Join-Path $ProjectDir ".agents\skills\powerdesigner-com-edit"),
        (Join-Path $ProjectDir ".claude\skills\powerdesigner-com-edit"),
        (Join-Path $ProjectDir ".gemini\skills\powerdesigner-com-edit")
    )
    foreach ($dest in $projectTargets) {
        Deploy-Skill -Destination $dest
    }
    Write-Host "Project-level skill deployment finished!" -ForegroundColor Green
}

# 2. Global User-Level Deployment
if ($Scope -eq "global" -or $Scope -eq "both") {
    $HomeDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
    Write-Host "`nDeploying to Global User Level ($HomeDir):" -ForegroundColor Cyan

    $globalTargets = @()
    if ($Target -eq "all" -or $Target -eq "gemini") {
        $globalTargets += (Join-Path $HomeDir ".gemini\skills\powerdesigner-com-edit")
    }
    if ($Target -eq "all" -or $Target -eq "claude") {
        $globalTargets += (Join-Path $HomeDir ".claude\skills\powerdesigner-com-edit")
    }

    foreach ($dest in $globalTargets) {
        Deploy-Skill -Destination $dest
    }
    Write-Host "Global skill deployment finished!" -ForegroundColor Green
}

Write-Host "`nAll set! Coding assistants in this environment can now invoke 'powerdesigner-com-edit'." -ForegroundColor Yellow
