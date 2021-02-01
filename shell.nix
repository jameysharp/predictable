{ pkgs ? import <nixpkgs> {} }:

let
  poetry2nix = import ./poetry.nix { inherit pkgs; };
  app = poetry2nix.mkPoetryEnv {
    projectDir = ./.;
    editablePackageSources.predictable = ./.;
  };
in pkgs.mkShell { buildInputs = [ app pkgs.poetry ]; }
