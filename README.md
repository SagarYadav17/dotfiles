# Dotfiles Configuration

This repository contains configuration files for various tools and applications.

## Installation

One-liner install (fresh setup):

```sh
git clone https://github.com/SagarYadav17/dotfiles.git "$HOME/dotfiles" && cd "$HOME/dotfiles" && ./install.sh
```

Run the installer script:

```sh
# Standard installation
./install.sh

# VM installation (imports Launchpad SSH keys to ~/.ssh/authorized_keys)
./install.sh --ssh-keys    # or: ./install.sh --vm
```

You can also import your Launchpad SSH keys manually:

```sh
mkdir -p ~/.ssh && chmod 700 ~/.ssh
curl -fsSL "https://launchpad.net/~sagaryadav17/+sshkeys" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

The script installs dependencies (including `unzip` and `btop`), sets up `mise`, `uv`, Bun, `oh-my-zsh`, required zsh plugins, runs `stow`.

The installer requires Bash and supports `apt` (Ubuntu) and `dnf` (Fedora, RHEL). On RHEL and its clones it first enables EPEL (and CodeReady Builder when `crb` exists), because `stow`, `ripgrep` and `btop` come from there.

The installer requires Bash. You can also run `bash ./install.sh`; invoking it with `sh ./install.sh` automatically restarts it in Bash.

## Windows

Windows has no installer script and needs no clone. Paste this in PowerShell to install the applications with `winget`:

```powershell
winget install --id=Valve.Steam -e --silent ; winget install --id=Discord.Discord -e --silent ; winget install --id=7zip.7zip -e --silent ; winget install --id=Spotify.Spotify -e --silent ; winget install --id=Microsoft.PowerShell -e --silent ; winget install --id=EpicGames.EpicGamesLauncher -e --silent ; winget install --id=Stremio.Stremio -e --silent
```

Under WSL2, `install.sh` runs inside Linux as usual.

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
   "$HOME/.local/bin/mise" use --global uv@latest
   ```

5. Install `oh-my-zsh` if it is not already installed:

   ```sh
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
   ```

6. Install Bun if it is not already installed:

   ```sh
   "$HOME/.local/bin/mise" use --global bun@latest
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
   mkdir -p ~/.claude ~/.codex ~/.config/systemd/user
   cd $HOME/dotfiles
   stow --no-folding .
   chmod 600 .claude/CLAUDE.md
   ```

The installer enables a systemd user service for `ssh-agent` when available.
A shell uses its existing agent when one is already set.

## Install skills from GitHub

The marketplace provides the same skills to Claude Code and Codex. Run these commands in Claude Code:

```
/plugin marketplace add SagarYadav17/dotfiles
/plugin install sagar-skills@sagar
```

Skills get the prefix `sagar-skills:`, for example `/sagar-skills:ste-output`. To get new commits, run `/plugin marketplace update sagar`, or turn on auto-update for the marketplace in `/plugin`.

For Codex, add the marketplace from a terminal:

```sh
codex plugin marketplace add SagarYadav17/dotfiles
codex plugin add sagar-skills@sagar
```

Run `codex plugin marketplace upgrade sagar` to fetch new commits. Restart Codex after updating. You can also select the repository marketplace in the Codex desktop plugin directory.

For Kimi Code CLI, install the plugin from chat or terminal:

```sh
/plugins install https://github.com/SagarYadav17/dotfiles
```

Or install from a local clone:

```sh
kimi plugin install "$HOME/dotfiles"
```

For Antigravity, `install.sh` automatically links the repository to `~/.gemini/config/plugins/sagar-skills`. You can review or toggle the plugin at `customization://sagar-skills`.

Notes:

- Install the marketplace plugin separately in each agent.
- Project Memory requires its installed skill directory and local vault access.

## Contents

- `.zshrc`: Configuration for Zsh shell.
- `.profile`: Login-shell `PATH`. It adds the mise shims (`~/.local/share/mise/shims`), so `node` and `codex` work in bash, in non-interactive shells and in desktop apps, not only in an interactive zsh. Log out and log in again after the first install.
- `.gitconfig`: Configuration for Git (`core.autocrlf=input`, `fetch.prune=true`). Repositories under `~/work/` also read `~/.gitconfig.work`, which is not tracked: create it on a machine that needs another identity.
- `.claude/CLAUDE.md`: Global instructions for Claude Code and Codex: the Project Memory block, and STE (skill `ste-output`) as the default writing style. Say "stop ste" or "normal mode" to turn STE off for one session. The Antigravity CLI (`agy`) has no global rules file, so it does not get these instructions. `~/.codex/AGENTS.md` is a second link to this one file, so the two cannot differ. Edit the copy in this repository, not the one in your home folder: some editors replace a symlink with a normal file.
- `skills/`: Custom skills packaged for the Claude Code and Codex marketplaces.
- `install.sh`: Installer for Linux.
- `CHANGELOG.MD`: Notable changes. Add each notable change under `Unreleased`, in Keep a Changelog categories and ASD-STE100 Simplified Technical English (skill `ste-output`).

## Usage

After running `stow .`, the configuration files will be symlinked to your `$HOME` directory, and you can start using them immediately.

## License

This project is licensed under the MIT License.
