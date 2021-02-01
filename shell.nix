{ pkgs ? import <nixpkgs> {} }:

let
  _pkgs = import ./poetry.nix { inherit pkgs; };
  app = _pkgs.poetry2nix.mkPoetryEnv {
    projectDir = ./.;
    editablePackageSources.predictable = ./.;
  };
in _pkgs.mkShell { buildInputs = [ app _pkgs.poetry ]; }
