{ pkgs ? import <nixpkgs> {} }:

let
  poetry2nix-src = pkgs.fetchFromGitHub {
    owner = "nix-community";
    repo = "poetry2nix";
    rev = "1.13.0";
    sha256 = "1lqzlkn1wxfdq4dvc7b3113b2xj5pjdhnw7qf4540dvh8c01k8dg";
  };
in pkgs.extend (import (poetry2nix-src + "/overlay.nix"))
