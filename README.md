# Dotfiles Configuration

This repository contains configuration files for various tools and applications.

## Installation

One-liner install (fresh setup):

```sh
git clone https://github.com/SagarYadav17/dotfiles.git "$HOME/dotfiles" && cd "$HOME/dotfiles" && ./install.sh
```

Run the installer script:

```sh
./install.sh
```

The script installs dependencies, sets up `nvm`, `uv`, `oh-my-zsh`, required zsh plugins, and runs `stow`.

If you prefer manual setup, use the steps below.

1. Install dependencies if they are not already installed:

   ```sh
   # For Ubuntu
   sudo apt-get install stow zsh git curl wget ripgrep

   # For Fedora
   sudo dnf install stow zsh git curl wget ripgrep
   ```

2. Clone the repository to your `$HOME` directory:

   ```sh
   git clone https://github.com/sagaryadav17/dotfiles.git $HOME/dotfiles
   ```

3. Install nvm

   ```sh
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
   ```

4. Install uv (Python package and project manager)

   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

5. Install `oh-my-zsh` if it is not already installed:

   ```sh
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
   ```

6. Install `zsh-autosuggestions` if it is not already installed:

   ```sh
   git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
   ```

7. Install `zsh-syntax-highlighting` if it is not already installed:

   ```sh
   git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
   ```

8. Run `stow` to create the necessary symlinks:

   ```sh
   cd $HOME/dotfiles
   stow .
   ```

## Contents

- `.zshrc`: Configuration for Zsh shell.
- `.gitconfig`: Configuration for Git.
- `nixos/configuration.nix`: NixOS system configuration, including system packages and zsh as the default shell for `sagar`.

## NixOS

To restore the shared NixOS configuration, copy it to `/etc/nixos/` and keep your machine-generated `hardware-configuration.nix` managed locally:

```sh
sudo cp nixos/configuration.nix /etc/nixos/
sudo nixos-rebuild switch
```

The repo config intentionally avoids enabling a specific desktop environment or display manager, so GNOME, KDE Plasma, Hyprland, Xfce, or another desktop can be added in the host-specific NixOS config without conflicting with this backup.

## Usage

After running `stow .`, the configuration files will be symlinked to your `$HOME` directory, and you can start using them immediately.

## License

This project is licensed under the MIT License.
