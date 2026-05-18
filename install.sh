#!/usr/bin/env bash
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

backup_if_regular_file() {
  local target="$1"

  if [[ -L "$target" ]]; then
    return
  fi

  if [[ -f "$target" ]]; then
    local backup="${target}.backup-${STAMP}"
    mv "$target" "$backup"
    log "Backed up $target -> $backup"
  fi
}

install_system_packages() {
  local packages=(stow zsh git curl wget ripgrep)

  log "Checking required system packages"

  if has_cmd apt-get; then
    run_with_privileges apt-get update
    run_with_privileges apt-get install -y "${packages[@]}"
  elif has_cmd dnf; then
    run_with_privileges dnf install -y "${packages[@]}"
  elif has_cmd pacman; then
    run_with_privileges pacman -Sy --noconfirm "${packages[@]}"
  elif has_cmd zypper; then
    run_with_privileges zypper --non-interactive install "${packages[@]}"
  else
    warn "Unsupported package manager. Install these manually: ${packages[*]}"
  fi
}

install_nvm() {
  if [[ -d "$HOME/.nvm" ]]; then
    log "nvm already installed"
    return
  fi

  log "Installing nvm"
  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
}

install_uv() {
  if has_cmd uv; then
    log "uv already installed"
    return
  fi

  log "Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
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
  backup_if_regular_file "$HOME/.zshrc"
  backup_if_regular_file "$HOME/.gitconfig"

  log "Linking dotfiles with stow"
  (cd "$REPO_DIR" && stow --restow --target "$HOME" .)
}

main() {
  log "Starting dotfiles installation"
  install_system_packages
  install_nvm
  install_uv
  install_oh_my_zsh
  install_zsh_plugins
  stow_dotfiles

  log "Installation complete"
  log "Open a new shell session or run: exec zsh"
}

main "$@"
