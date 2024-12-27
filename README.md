# Dotfiles Configuration

This repository contains configuration files for various tools and applications.

## Installation

1. Clone the repository to your `$HOME` directory:

   ```sh
   git clone https://github.com/sagaryadav17/dotfiles.git $HOME/dotfiles
   ```

2. Install `stow` and `zsh` if it is not already installed:

   ```sh
   # For Ubuntu
   sudo apt-get install stow zsh

   # For Fedora and CentOS
   sudo dnf install stow zsh
   ```

3. Install `oh-my-zsh` if it is not already installed:

   ```sh
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
   ```

4. Install `zsh-autosuggestions` if it is not already installed:

   ```sh
   git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
   ```

5. Install `zsh-syntax-highlighting` if it is not already installed:

   ```sh
   git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
   ```

6. Run `stow` to create the necessary symlinks:

   ```sh
   cd $HOME/dotfiles
   stow .
   ```

## Contents

- `.zshrc`: Configuration for Zsh shell.
- `.gitconfig`: Configuration for Git.

## Usage

After running `stow .`, the configuration files will be symlinked to your `$HOME` directory, and you can start using them immediately.

## License

This project is licensed under the MIT License.
