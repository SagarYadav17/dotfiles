#!/usr/bin/env pwsh
# Windows setup, the counterpart of install.sh:
#   1. installs applications with winget (list in $WingetPackages),
#   2. installs a global Python 3 with uv (python and python3 on PATH),
#      and graphify with "uv tool install graphifyy",
#   3. links custom skills (skills/) into the locations Claude Code and other
#      agent CLIs scan for them, and links the global instruction files
#      (.claude\CLAUDE.md, linked as both CLAUDE.md and .codex\AGENTS.md). Mirrors install.sh.
# Linking requires Developer Mode enabled, or an elevated (Run as
# Administrator) PowerShell session, to create symlinks.
#
# Usage:  pwsh -ExecutionPolicy Bypass -File .\install.ps1 [-SkipPackages] [-SkipPython] [-SkipGraphify] [-SkipSkills]

param(
    [switch]$SkipPackages,
    [switch]$SkipPython,
    [switch]$SkipGraphify,
    [switch]$SkipSkills
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

# winget package IDs. uv provides the global Python (see Install-Python).
$WingetPackages = @(
    "Microsoft.PowerShell",
    "Git.Git",
    "Termius.Termius",
    "7zip.7zip",
    "Oven-sh.Bun",
    "Google.AntigravityIDE",
    "Bruno.Bruno",
    "Stremio.Stremio",
    "Google.Chrome",
    "Google.AndroidStudio",
    "Microsoft.Teams",
    "ZedIndustries.Zed",
    "Anthropic.Claude",
    "Obsidian.Obsidian",
    "astral-sh.uv"
)
$PythonVersion = "3.13"

function Write-Info  { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn  { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err   { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Update-SessionPath {
    # A program installed by winget is not on PATH of this session until it is reloaded.
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

function Install-Packages {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Warn "winget not found (install 'App Installer' from the Microsoft Store). Skipping packages."
        return
    }

    $failed = @()
    foreach ($id in $WingetPackages) {
        winget list --id $id -e --accept-source-agreements *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Info "$id already installed"
            continue
        }

        Write-Info "Installing $id"
        winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            $failed += $id
        }
    }

    if ($failed.Count -gt 0) {
        Write-Warn "Not installed (check the winget ID or install by hand): $($failed -join ', ')"
    }
}

function Install-Python {
    # uv installs a Python build and puts python / python3 in ~/.local/bin.
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Warn "uv not found. Run without -SkipPackages first, or install it: winget install astral-sh.uv"
        return
    }

    Write-Info "Installing Python $PythonVersion with uv"
    uv python install $PythonVersion --default --preview
    uv tool update-shell
    Update-SessionPath
    $localBin = Join-Path $HOME ".local\bin"
    if ($env:Path -notlike "*$localBin*") {
        $env:Path = "$localBin;$env:Path"
    }

    # The Microsoft Store stub (WindowsApps\python3.exe) comes first on PATH and shadows uv's python3.
    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($python3 -and $python3.Source -like "*WindowsApps*") {
        Write-Warn "python3 still resolves to the Microsoft Store stub ($($python3.Source))."
        Write-Warn "Turn off 'python.exe' and 'python3.exe' in Settings > Apps > Advanced app settings > App execution aliases."
    } elseif ($python3) {
        Write-Info "python3 -> $($python3.Source)"
    } else {
        Write-Warn "python3 not found on PATH yet. Open a new terminal and run: python3 --version"
    }
}

function Install-Graphify {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Warn "uv not found; skipping graphify. Run without -SkipPackages first, or: winget install astral-sh.uv"
        return
    }

    $installed = uv tool list 2>$null | Select-String -Pattern "^graphifyy "
    if ($installed) {
        Write-Info "graphify already installed"
        return
    }

    Write-Info "Installing graphify"
    uv tool install graphifyy
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "graphify install failed. Run by hand: uv tool install graphifyy"
    }
}

function Install-GraphifySkill {
    if (-not (Get-Command graphify -ErrorAction SilentlyContinue)) {
        return
    }
    # ~/.claude/skills and ~/.agents/skills point into this repo, so this writes skills\graphify
    # (git-ignored). Run it after Link-CustomSkills. "windows" is the PowerShell variant of "claude".
    Write-Info "Installing graphify skill"
    foreach ($platform in "windows", "agents") {
        graphify install --platform $platform
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "graphify skill install ($platform) failed"
        }
    }
}

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

function Link-InstructionFile {
    # Links one tracked instruction file into $HOME. Falls back to a copy when symlinks are not
    # allowed; a copy does not follow later changes in the repository.
    # -SourceRelativePath lets two targets (CLAUDE.md and AGENTS.md) share one tracked file.
    param([string]$RelativePath, [string]$SourceRelativePath = $RelativePath)

    $source = Join-Path $RepoDir $SourceRelativePath
    $target = Join-Path $HOME $RelativePath

    if (-not (Test-Path -LiteralPath $source)) {
        Write-Warn "$SourceRelativePath is not in the repository. Skipping."
        return
    }

    $targetParent = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $targetParent)) {
        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
    }

    $existing = Get-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue
    if ($existing) {
        if ($existing.LinkType -eq "SymbolicLink") {
            if (@($existing.Target)[0] -eq (Get-Item -LiteralPath $source).FullName) {
                Write-Info "$target already linked"
                return
            }
            Remove-Item -LiteralPath $target -Force
        } elseif ((Get-FileHash -LiteralPath $source).Hash -eq (Get-FileHash -LiteralPath $target).Hash) {
            Remove-Item -LiteralPath $target -Force
        } else {
            $backup = "$target.backup-$Stamp"
            Move-Item -LiteralPath $target -Destination $backup
            Write-Info "Backed up $target -> $backup"
        }
    }

    try {
        New-Item -ItemType SymbolicLink -Path $target -Target $source -ErrorAction Stop | Out-Null
        Write-Info "Linked $target"
    } catch {
        Copy-Item -LiteralPath $source -Destination $target
        Write-Warn "Could not create a symlink; copied $SourceRelativePath to $target. Run the script again after you change the repository file."
    }
}

function Set-GitLineEndings {
    # Git for Windows defaults to autocrlf=true (CRLF checkouts), which breaks SKILL.md and shell scripts.
    # "input" converts CRLF to LF on commit and leaves LF in the working tree. Matches .gitconfig in this repo.
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Warn "git not found; skipping line-ending config"
        return
    }
    git config --global core.autocrlf input
    git config --global core.eol lf
    Write-Info "Git line endings set to LF (core.autocrlf=input, core.eol=lf)"
}

function Main {
    if (-not $SkipPackages) {
        Install-Packages
        Update-SessionPath
    }

    Set-GitLineEndings

    if (-not $SkipPython) {
        Install-Python
    }

    if (-not $SkipGraphify) {
        Install-Graphify
    }

    if (-not $SkipSkills) {
        Write-Info "Linking custom skills"
        Link-CustomSkills
        Link-InstructionFile -RelativePath ".claude\CLAUDE.md"
        Link-InstructionFile -RelativePath ".codex\AGENTS.md" -SourceRelativePath ".claude\CLAUDE.md"
        if (-not $SkipGraphify) {
            Install-GraphifySkill
        }
    }

    Write-Info "Done. Restart your terminal, then Claude Code / Codex / Antigravity, to pick up the changes."
}

Main
