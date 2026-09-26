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

The script installs dependencies (including `unzip` and `btop`), sets up `mise`, `uv`, Bun, `oh-my-zsh`, required zsh plugins, runs `stow`, and links the repository's custom skills into `$HOME/.agents/skills`.

The installer requires Bash. You can also run `bash ./install.sh`; invoking it with `sh ./install.sh` automatically restarts it in Bash.

If you prefer manual setup, use the steps below.

1. Install dependencies if they are not already installed:

   ```sh
   # For Ubuntu
   sudo apt-get install stow zsh git curl wget ripgrep unzip btop

   # For Fedora
   sudo dnf install stow zsh git curl wget ripgrep unzip btop
   ```

2. Clone the repository to your `$HOME` directory:

   ```sh
   git clone https://github.com/sagaryadav17/dotfiles.git $HOME/dotfiles
   ```

3. Install mise (runtime version manager)

   ```sh
   curl https://mise.run | sh
   ```

4. Install uv (Python package and project manager)

   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

5. Install `oh-my-zsh` if it is not already installed:

   ```sh
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
   ```

6. Install Bun if it is not already installed:

   ```sh
   curl -fsSL https://bun.com/install | bash
   ```

7. Install `zsh-autosuggestions` if it is not already installed:

   ```sh
   git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
   ```

8. Install `zsh-syntax-highlighting` if it is not already installed:

   ```sh
   git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
   ```

9. Run `stow` to create the necessary symlinks:

   ```sh
   cd $HOME/dotfiles
   stow .
   ```

10. Link custom skills for other agents:

   ```sh
   mkdir -p "$HOME/.agents"
   ln -s "$HOME/dotfiles/skills" "$HOME/.agents/skills"
   ```

## Contents

- `.zshrc`: Configuration for Zsh shell.
- `.gitconfig`: Configuration for Git.
- `skills/`: Custom agent skills shared through `$HOME/.agents/skills`.

## Usage

After running `stow .`, the configuration files will be symlinked to your `$HOME` directory, and you can start using them immediately.

## License

This project is licensed under the MIT License.
