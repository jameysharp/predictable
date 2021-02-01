{ pkgs ? import <nixpkgs> {} }:

let
  poetry2nix-src = pkgs.fetchFromGitHub {
    owner = "nix-community";
    repo = "poetry2nix";
    rev = "1.13.0";
    sha256 = "1lqzlkn1wxfdq4dvc7b3113b2xj5pjdhnw7qf4540dvh8c01k8dg";
  };

  poetry2nix = import poetry2nix-src {
    inherit pkgs;
    inherit (pkgs) poetry;
  };
in poetry2nix
