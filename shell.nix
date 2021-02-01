{ pkgs ? import <nixpkgs> {} }:

let
  poetry2nix = import ./poetry.nix { inherit pkgs; };
  app = poetry2nix.mkPoetryEnv {
    projectDir = ./.;
    editablePackageSources.app = ./.;
  };
in pkgs.mkShell { buildInputs = [ app pkgs.poetry ]; }
