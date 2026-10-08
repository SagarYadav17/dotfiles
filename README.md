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

The script installs dependencies (including `unzip` and `btop`), sets up `mise`, `uv`, `graphify` (`uv tool install graphifyy`), Bun, `oh-my-zsh`, required zsh plugins, runs `stow`, and links the repository's custom skills into `$HOME/.agents/skills`.

The installer requires Bash and supports `apt` (Ubuntu) and `dnf` (Fedora, RHEL). On RHEL and its clones it first enables EPEL (and CodeReady Builder when `crb` exists), because `stow`, `ripgrep` and `btop` come from there.

The installer requires Bash. You can also run `bash ./install.sh`; invoking it with `sh ./install.sh` automatically restarts it in Bash.

## Windows

Run `install.ps1` from PowerShell 7 (or Windows PowerShell) in the Windows clone of this repository:

```powershell
pwsh -ExecutionPolicy Bypass -File .\install.ps1
```

It does four things; skip any of them with `-SkipPackages`, `-SkipPython`, `-SkipGraphify` or `-SkipSkills`:

1. Installs the applications listed in `$WingetPackages` with `winget` (already installed ones are skipped).
2. Installs a global Python 3.13 with `uv` (`python` and `python3` in `%USERPROFILE%\.local\bin`). Turn off the `python.exe` and `python3.exe` entries in Settings > Apps > Advanced app settings > App execution aliases, or the Microsoft Store stub hides `python3`.
3. Installs `graphify` with `uv tool install graphifyy`.
4. Links `skills/` to `%USERPROFILE%\.claude\skills` and `%USERPROFILE%\.agents\skills`, and links `.claude\CLAUDE.md` into your user folder as both `.claude\CLAUDE.md` and `.codex\AGENTS.md` (a copy if symlinks are not allowed). Creating symlinks needs Developer Mode or an Administrator shell.

Keep a separate clone on Windows and sync through git. Under WSL2 the skills are linked by `install.sh` inside Linux.

If you prefer manual setup, use the steps below.

1. Install dependencies if they are not already installed:

   ```sh
   # For Ubuntu
   sudo apt-get install stow zsh git curl wget ripgrep unzip btop

   # For Fedora
   sudo dnf install stow zsh git curl wget ripgrep unzip btop

   # For RHEL: enable EPEL first (stow, ripgrep and btop are in EPEL)
   sudo dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-$(rpm -E %rhel).noarch.rpm
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

9. Run `stow` to create the necessary symlinks. Create the folders first and use `--no-folding`; without them stow could link the whole `~/.claude` folder into the repository, and Claude Code would write its credentials and sessions there:

   ```sh
   mkdir -p ~/.claude ~/.codex
   cd $HOME/dotfiles
   stow --no-folding .
   chmod 600 .claude/CLAUDE.md
   ```

10. (Optional) Link custom skills for other agents:

   If you're running the full `install.sh`, this is handled automatically.
   For manual setups only, link the skills directory:

   ```sh
   mkdir -p "$HOME/.agents"
   ln -s "$HOME/dotfiles/skills" "$HOME/.agents/skills"
   ```

## Contents

- `.zshrc`: Configuration for Zsh shell.
- `.gitconfig`: Configuration for Git (`core.autocrlf=input`, `fetch.prune=true`). Repositories under `~/work/` also read `~/.gitconfig.work`, which is not tracked: create it on a machine that needs another identity.
- `.claude/CLAUDE.md`: Global instructions for Claude Code and Codex (the Project Memory block). `~/.codex/AGENTS.md` is a second link to this one file, so the two cannot differ. Edit the copy in this repository, not the one in your home folder: some editors replace a symlink with a normal file.
- `skills/`: Custom agent skills shared through `$HOME/.agents/skills` and `$HOME/.claude/skills`.
- `plugins/`: Claude Code plugins that are not skills (for example `minecraft-hud`). They are not linked automatically.
- `install.sh`, `install.ps1`: Installers for Linux and Windows.
- `CHANGELOG.MD`: Notable changes. Add each notable change under `Unreleased`, in Keep a Changelog categories and ASD-STE100 Simplified Technical English (skill `ste-output`).

## Usage

After running `stow .`, the configuration files will be symlinked to your `$HOME` directory, and you can start using them immediately.

## License

This project is licensed under the MIT License.
