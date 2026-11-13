#!/usr/bin/env bash
# Restart in Bash when invoked explicitly with sh.
if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"

log() {
  printf "\033[1;34m[INFO]\033[0m %s\n" "$*"
}

warn() {
  printf "\033[1;33m[WARN]\033[0m %s\n" "$*"
}

error() {
  printf "\033[1;31m[ERROR]\033[0m %s\n" "$*" >&2
}

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

run_with_privileges() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    "$@"
  elif has_cmd sudo; then
    sudo "$@"
  else
    error "Need root privileges to install system packages. Install 'sudo' or run this script as root."
    exit 1
  fi
}

# Move a regular file out of the way before stow links it. A file with the same content as the
# repository copy (second argument) is removed without a backup.
backup_if_regular_file() {
  local target="$1"
  local source="${2:-}"

  if [[ -L "$target" ]]; then
    return
  fi

  if [[ -f "$target" ]]; then
    if [[ -n "$source" ]] && cmp -s "$source" "$target"; then
      rm -f "$target"
      log "Replaced $target (same content as the repository copy)"
      return
    fi

    local backup="${target}.backup-${STAMP}"
    mv "$target" "$backup"
    log "Backed up $target -> $backup"
  fi
}

# RHEL (and clones) have stow, ripgrep and btop only in EPEL.
enable_epel_on_rhel() {
  local id="" id_like="" major
  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    id="$(. /etc/os-release && echo "${ID:-}")"
    id_like="$(. /etc/os-release && echo "${ID_LIKE:-}")"
  fi

  if [[ "$id" == "fedora" || "$id_like" != *rhel* && "$id" != "rhel" ]]; then
    return
  fi

  if rpm -q epel-release >/dev/null 2>&1; then
    log "EPEL already enabled"
  else
    major="$(rpm -E %rhel)"
    log "Enabling EPEL $major"
    run_with_privileges dnf install -y \
      "https://dl.fedoraproject.org/pub/epel/epel-release-latest-${major}.noarch.rpm" \
      || warn "Could not enable EPEL; stow, ripgrep and btop may be missing."
  fi

  if has_cmd crb; then
    run_with_privileges crb enable || warn "Could not enable CodeReady Builder (crb)."
  fi
}

install_system_packages() {
  local packages=(stow zsh git curl wget ripgrep unzip btop)

  log "Checking required system packages"

  if has_cmd apt-get; then
    run_with_privileges apt-get update
    run_with_privileges apt-get install -y "${packages[@]}"
  elif has_cmd dnf; then
    enable_epel_on_rhel
    run_with_privileges dnf install -y "${packages[@]}"
  else
    error "Unsupported system. This installer supports apt (Ubuntu) and dnf (Fedora, RHEL) only."
    exit 1
  fi
}

install_mise() {
  if has_cmd mise; then
    log "mise already installed"
    return
  fi

  log "Installing mise"
  curl -fsSL https://mise.run | sh
}

install_uv() {
  # The mise installer places the binary here on a fresh system.
  export PATH="$HOME/.local/bin:$PATH"

  if mise config get --global tools.uv >/dev/null 2>&1; then
    log "Installing the configured global uv version"
    mise -C "$HOME" install uv
  else
    log "Installing uv with mise"
    mise use --global uv@latest
  fi
}

install_bun() {
  if mise config get --global tools.bun >/dev/null 2>&1; then
    log "Installing the configured global Bun version"
    mise -C "$HOME" install bun
  else
    log "Installing Bun with mise"
    mise use --global bun@latest
  fi
}

install_oh_my_zsh() {
  if [[ -d "$HOME/.oh-my-zsh" ]]; then
    log "oh-my-zsh already installed"
    return
  fi

  log "Installing oh-my-zsh"
  RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
}

clone_or_update_plugin() {
  local repo_url="$1"
  local target_dir="$2"

  if [[ -d "$target_dir/.git" ]]; then
    log "Updating plugin $(basename "$target_dir")"
    git -C "$target_dir" pull --ff-only
  else
    log "Installing plugin $(basename "$target_dir")"
    git clone "$repo_url" "$target_dir"
  fi
}

install_zsh_plugins() {
  local zsh_custom="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
  mkdir -p "$zsh_custom/plugins"

  clone_or_update_plugin \
    https://github.com/zsh-users/zsh-autosuggestions \
    "$zsh_custom/plugins/zsh-autosuggestions"

  clone_or_update_plugin \
    https://github.com/zsh-users/zsh-syntax-highlighting.git \
    "$zsh_custom/plugins/zsh-syntax-highlighting"
}

stow_dotfiles() {
  # Create the folders first. With --no-folding stow links single files into them; without these
  # folders stow would link the whole folder into the repository, and Claude Code and Codex would
  # write credentials and sessions there.
  mkdir -p "$HOME/.claude" "$HOME/.codex" "$HOME/.config/systemd/user"

  backup_if_regular_file "$HOME/.zshrc" "$REPO_DIR/.zshrc"
  backup_if_regular_file "$HOME/.gitconfig" "$REPO_DIR/.gitconfig"
  backup_if_regular_file "$HOME/.profile" "$REPO_DIR/.profile"
  backup_if_regular_file "$HOME/.claude/CLAUDE.md" "$REPO_DIR/.claude/CLAUDE.md"
  backup_if_regular_file "$HOME/.codex/AGENTS.md" "$REPO_DIR/.claude/CLAUDE.md"

  log "Linking dotfiles with stow"
  (cd "$REPO_DIR" && stow --no-folding --restow --target "$HOME" .)

  # Codex reads the same global instructions as Claude Code: one tracked file, two links.
  ln -sfn "$REPO_DIR/.claude/CLAUDE.md" "$HOME/.codex/AGENTS.md"

  # Git does not store this mode; the global Claude instructions are private.
  chmod 600 "$REPO_DIR/.claude/CLAUDE.md"
}

main() {
  log "Starting dotfiles installation"
  install_system_packages
  install_mise
  install_uv
  install_bun
  install_oh_my_zsh
  install_zsh_plugins
  stow_dotfiles
  if command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
    systemctl --user daemon-reload
    systemctl --user enable --now dotfiles-ssh-agent.service
  fi

  log "Installation complete"
  log "Open a new shell session or run: exec zsh"
}

main "$@"
