# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"
export ANDROID_HOME="$HOME/Android/Sdk"

export PATH="$HOME/.local/bin:$PATH"
export PATH="$PATH:$ANDROID_HOME/emulator"
export PATH="$PATH:$ANDROID_HOME/platform-tools"

# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="robbyrussell"

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(
    git
    pip
    gitignore
    zsh-autosuggestions
    zsh-syntax-highlighting
)

source $ZSH/oh-my-zsh.sh

# Reuse the user service when the session did not provide an agent.
if [ -z "$SSH_AUTH_SOCK" ]; then
    if [ -n "$XDG_RUNTIME_DIR" ] && command -v systemctl >/dev/null 2>&1 &&
       systemctl --user start dotfiles-ssh-agent.service >/dev/null 2>&1 &&
       [ -S "$XDG_RUNTIME_DIR/dotfiles-ssh-agent.sock" ]; then
        export SSH_AUTH_SOCK="$XDG_RUNTIME_DIR/dotfiles-ssh-agent.sock"
    else
        eval "$(ssh-agent -s)"
    fi
fi
eval "$(mise activate zsh)"

# bun
export BUN_INSTALL="${BUN_INSTALL:-$HOME/.bun}"
export PATH="$PATH:$BUN_INSTALL/bin"
[ -s "$BUN_INSTALL/_bun" ] && source "$BUN_INSTALL/_bun"
