with import <nixpkgs> {};

stdenv.mkDerivation {
  name = "full-history-env";
  buildInputs = [
    python3Full
    pipenv

    # The python modules listed in Pipfile.lock require the
    # following packages to be installed locally in order to compile
    # their binary extensions.
  ];
  src = null;
  shellHook = ''
    # set SOURCE_DATE_EPOCH so that we can use python wheels
    SOURCE_DATE_EPOCH=$(date +%s)
  '';
}
