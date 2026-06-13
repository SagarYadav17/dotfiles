{ config, pkgs, ... }:

{
  # Bootloader.
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  networking.hostName = "bifrost";
  networking.networkmanager.enable = true;

  time.timeZone = "Asia/Kolkata";

  i18n.defaultLocale = "en_IN";

  i18n.extraLocaleSettings = {
    LC_ADDRESS = "en_IN";
    LC_IDENTIFICATION = "en_IN";
    LC_MEASUREMENT = "en_IN";
    LC_MONETARY = "en_IN";
    LC_NAME = "en_IN";
    LC_NUMERIC = "en_IN";
    LC_PAPER = "en_IN";
    LC_TELEPHONE = "en_IN";
    LC_TIME = "en_IN";
  };

  services.xserver.xkb = {
    layout = "us";
    variant = "";
  };

  services.printing.enable = true;

  services.pulseaudio.enable = false;
  security.rtkit.enable = true;
  services.pipewire = {
    enable = true;
    alsa.enable = true;
    alsa.support32Bit = true;
    pulse.enable = true;
    # jack.enable = true;
  };

  # services.xserver.libinput.enable = true;

  users.users.sagar = {
    isNormalUser = true;
    description = "Sagar Yadav";
    extraGroups = [ "networkmanager" "wheel" ];
    shell = pkgs.zsh;
  };

  programs.firefox.enable = true;

  programs.zsh = {
    enable = true;
    ohMyZsh.enable = true;
  };

  nixpkgs.config.allowUnfree = true;

  # System packages to restore on a fresh NixOS install.
  environment.systemPackages = with pkgs; [
    vim
    wget
    zed-editor
    google-chrome
    brave
    obsidian
    tailscale
    wireshark
    zsh
    oh-my-zsh
    git
    android-studio
    codex
    ghostty
    stow
  ];

  system.stateVersion = "26.05";
}
