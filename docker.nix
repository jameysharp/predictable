{ pkgs ? import <nixpkgs> {} }:

let
  _pkgs = import ./poetry.nix { inherit pkgs; };
  app = _pkgs.poetry2nix.mkPoetryApplication {
    projectDir = ./.;
  };
in _pkgs.dockerTools.streamLayeredImage {
  name = "predictable";
  contents = [
    app.dependencyEnv

    # handy for `docker enter`:
    _pkgs.busybox
  ];

  # Note that gunicorn automatically listens on all addresses and to the
  # correct port but only if the PORT environment variable is set, so do that
  # when you deploy this image.
  config.Cmd = [ "/bin/gunicorn" "predictable:app" ];
}
