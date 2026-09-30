#!/usr/bin/env pwsh
# Links custom skills (skills/) into the locations Claude Code and other
# agent CLIs scan for them, on native Windows. Mirrors link_custom_skills()
# in install.sh. Requires Developer Mode enabled, or an elevated (Run as
# Administrator) PowerShell session, to create symlinks.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

function Write-Info  { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn  { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err   { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-DeveloperMode {
    $key = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock"
    $value = Get-ItemProperty -Path $key -Name "AllowDevelopmentWithoutDevLicense" -ErrorAction SilentlyContinue
    return ($null -ne $value) -and ($value.AllowDevelopmentWithoutDevLicense -eq 1)
}

function Link-SkillsTarget {
    param(
        [string]$SkillsDir,
        [string]$TargetPath
    )

    $targetParent = Split-Path -Parent $TargetPath
    if (-not (Test-Path $targetParent)) {
        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
    }

    $existing = Get-Item -LiteralPath $TargetPath -Force -ErrorAction SilentlyContinue

    if ($existing -and $existing.LinkType -eq "SymbolicLink") {
        $resolvedTarget = (Get-Item -LiteralPath $SkillsDir).FullName
        $resolvedExisting = $existing.Target
        if ($resolvedExisting -eq $resolvedTarget) {
            Write-Info "Custom skills already linked at $TargetPath"
            return
        }

        Write-Err "$TargetPath is already a symlink to another location ($resolvedExisting). Move it before rerunning."
        exit 1
    }

    if ($existing) {
        $backup = "$TargetPath.backup-$Stamp"
        Move-Item -LiteralPath $TargetPath -Destination $backup
        Write-Info "Preserved existing skills directory at $backup"
    }

    New-Item -ItemType SymbolicLink -Path $TargetPath -Target $SkillsDir | Out-Null
    Write-Info "Linked custom skills to $TargetPath"
}

function Link-CustomSkills {
    $skillsDir = Join-Path $RepoDir "skills"

    if (-not (Test-Path $skillsDir)) {
        Write-Err "Skills directory not found at $skillsDir"
        exit 1
    }

    if (-not (Test-IsAdmin) -and -not (Test-DeveloperMode)) {
        Write-Err "Creating symlinks on Windows requires either Developer Mode (Settings > Privacy & security > For developers) or running this script as Administrator."
        exit 1
    }

    # ~/.agents/skills: Codex, Antigravity, and other tools following the
    # shared agents-skills convention.
    Link-SkillsTarget -SkillsDir $skillsDir -TargetPath (Join-Path $HOME ".agents\skills")

    # ~/.claude/skills: Claude Code only scans this fixed location, not
    # ~/.agents/skills.
    Link-SkillsTarget -SkillsDir $skillsDir -TargetPath (Join-Path $HOME ".claude\skills")
}

function Main {
    Write-Info "Linking custom skills"
    Link-CustomSkills
    Write-Info "Done. Restart Claude Code / Codex / Antigravity to pick up the skills."
}

Main
