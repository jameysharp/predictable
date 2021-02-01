{ pkgs ? import <nixpkgs> {} }:

let
  app = (import ./poetry.nix { inherit pkgs; }).mkPoetryApplication {
    projectDir = ./.;
  };
in pkgs.dockerTools.streamLayeredImage {
  name = "predictable";
  contents = [
    app.dependencyEnv

    # handy for `docker enter`:
    pkgs.busybox
  ];

  # Note that gunicorn automatically listens on all addresses and to the
  # correct port but only if the PORT environment variable is set, so do that
  # when you deploy this image.
  config.Cmd = [ "/bin/gunicorn" "predictable:app" ];
}
