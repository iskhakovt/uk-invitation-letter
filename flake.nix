{
  description = "UK visa invitation letter generator";

  inputs = {
    # Unstable rather than nixos-26.05: 26.05's uv is 0.11.x, and CI requires
    # 0.13.4+, the first release that no longer trusts the compromised eMudhra
    # emSign CAs (see .circleci/config.yml).
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    # The package is built from uv.lock with uv2nix, so Nix gets exactly the
    # versions CI tests and dependabot bumps. nixpkgs alone can't provide them:
    # it doesn't package pydantic-yaml at all.
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
    }:
    let
      inherit (nixpkgs) lib;
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      # uv-dynamic-versioning reads the version from git tags, but a flake's
      # source has no .git, so supply one. The release version isn't knowable
      # here; the commit is.
      version = "0.0.0+${self.shortRev or self.dirtyShortRev or "unknown"}";

      # A file's whitespace-separated words, as CI's `$(cat file)` reads them.
      words =
        file:
        builtins.filter (word: builtins.isString word && word != "") (
          builtins.split "[[:space:]]+" (builtins.readFile file)
        );

      # Everything the outputs share, evaluated once per system.
      perSystem = lib.genAttrs systems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonSet =
            (pkgs.callPackage pyproject-nix.build.packages { python = pkgs.python3; }).overrideScope
              (
                lib.composeManyExtensions [
                  pyproject-build-systems.overlays.wheel
                  (workspace.mkPyprojectOverlay { sourcePreference = "wheel"; })
                  (final: prev: {
                    uk-invitation-letter = prev.uk-invitation-letter.overrideAttrs (old: {
                      inherit version;
                      # The source is the same; only the metadata changes.
                      __intentionallyOverridingVersion = true;
                      env = (old.env or { }) // {
                        UV_DYNAMIC_VERSIONING_BYPASS = version;
                      };
                    });
                  })
                ]
              );
        in
        {
          inherit system pkgs pythonSet;

          app = (pkgs.callPackage pyproject-nix.build.util { }).mkApplication {
            venv = pythonSet.mkVirtualEnv "uk-invitation-letter-env" workspace.deps.default;
            package = pythonSet.uk-invitation-letter;
          };

          # The same TeX Live CI's render-test job uses: scheme-small plus the
          # packages it installs from .circleci/texlive-packages.txt. The
          # texlive:latest-small image ships latexmk; nixpkgs' scheme-small doesn't.
          tex = pkgs.texliveSmall.withPackages (
            ps: [ ps.latexmk ] ++ map (name: ps.${name}) (words ./.circleci/texlive-packages.txt)
          );

          # Unwrapped: the wrapper only adds biber, which a letter with no
          # bibliography never runs, and which roughly doubles tectonic's closure.
          tectonic = pkgs.tectonic-unwrapped;
        }
      );
      forAllSystems = f: lib.mapAttrs (_: f) perSystem;
    in
    {
      packages = forAllSystems (
        {
          app,
          tex,
          tectonic,
          pkgs,
          ...
        }:
        let
          # `render` looks its engine up on PATH, so engines are optional: each
          # one included here is put on the wrapper's PATH, ahead of the user's own.
          package = lib.makeOverridable (
            {
              # xelatex (the default `--engine`), lualatex and pdflatex can't be
              # split: even scheme-basic ships all three, because latex-bin builds
              # every format. The engines are a small part of TeX Live's size.
              withTexLive ? true,
              # Smaller than TeX Live, but it downloads packages on first use.
              withTectonic ? false,
            }:
            let
              engines = lib.optional withTexLive tex ++ lib.optional withTectonic tectonic;
              wrapperArgs = [
                "--prefix"
                "PATH"
                ":"
                (lib.makeBinPath engines)
              ]
              # Without TeX Live the CLI's default, xelatex, isn't there, so
              # make tectonic the default. A value the user set is left alone,
              # and `--engine` still overrides either. Not --set-default: that
              # keeps an empty value, which the CLI reads as "use xelatex".
              ++ lib.optionals (withTectonic && !withTexLive) [
                "--run"
                "export UK_INVITATION_LETTER_ENGINE=\"\${UK_INVITATION_LETTER_ENGINE:-tectonic}\""
              ];
            in
            if engines == [ ] then
              app
            else
              app.overrideAttrs (old: {
                nativeBuildInputs = old.nativeBuildInputs ++ [ pkgs.makeWrapper ];
                postFixup = ''
                  wrapProgram $out/bin/uk-invitation-letter ${lib.escapeShellArgs wrapperArgs}
                '';
              })
          ) { };
        in
        {
          # TeX Live, so `nix run` renders with the default engine on a machine
          # with no TeX installed.
          default = package;
          # Tectonic only, and the default engine, at under half the size.
          tectonic = package.override {
            withTexLive = false;
            withTectonic = true;
          };
          # No engines: uses whatever TeX is already on PATH.
          bare = package.override { withTexLive = false; };
        }
      );

      devShells = forAllSystems (
        {
          pkgs,
          tex,
          tectonic,
          ...
        }:
        let
          # Where a standard Linux binary expects its dynamic loader.
          fhsLoader =
            {
              x86_64-linux = "/lib64/ld-linux-x86-64.so.2";
              aarch64-linux = "/lib/ld-linux-aarch64.so.1";
            }
            .${pkgs.stdenv.hostPlatform.system} or null;

          mkDevShell =
            extraPackages:
            pkgs.mkShell {
              packages = [
                pkgs.uv
                pkgs.python3
              ]
              ++ extraPackages;

              env = {
                # Pin the interpreter to the flake rather than letting uv fetch a
                # python-build-standalone build: those link against a loader at a
                # path NixOS doesn't have.
                UV_PYTHON = "${pkgs.python3}/bin/python3";
                UV_PYTHON_DOWNLOADS = "never";
              };

              # The same goes for ruff and pyrefly, which `uv sync` installs as
              # prebuilt binaries. NixOS only has the loader they need with
              # nix-ld, so say so up front rather than at the first `uv run ruff`.
              shellHook = lib.optionalString (fhsLoader != null) ''
                if [ -e /etc/NIXOS ] && [ ! -e ${fhsLoader} ]; then
                  echo "warning: ruff and pyrefly from \`uv sync\` won't start: NixOS has no ${fhsLoader}." >&2
                  echo "  Enable nix-ld (programs.nix-ld.enable = true) to run them." >&2
                fi
              '';
            };

          # baseline-tectonic.pdf was recorded with the Tectonic CI pins.
          tectonicPin = lib.trim (builtins.readFile ./.circleci/tectonic-version.txt);
        in
        {
          # Enough for `uv run pytest`: the render tests are opt-in.
          default = mkDevShell [ ];
          # For `uv run pytest -m render`: every engine the render tests cover,
          # and diff-pdf to compare against the baselines.
          render = mkDevShell [
            tex
            (lib.warnIf (tectonic.version != tectonicPin)
              "nixpkgs has Tectonic ${tectonic.version}, but .circleci/tectonic-version.txt pins ${tectonicPin}; the tectonic render test may not match its baseline."
              tectonic
            )
            pkgs.diff-pdf
          ];
        }
      );

      checks = forAllSystems (
        {
          system,
          pkgs,
          pythonSet,
          tex,
          ...
        }:
        let
          testEnv = pythonSet.mkVirtualEnv "uk-invitation-letter-test-env" (
            workspace.deps.default // { pytest = [ ]; }
          );
          # Runs the test suite against the installed package rather than src/.
          runTests =
            name: extraInputs: pytestArgs:
            pkgs.runCommand "uk-invitation-letter-${name}" { nativeBuildInputs = [ testEnv ] ++ extraInputs; }
              ''
                cp -r ${./.} source
                chmod -R u+w source
                cd source
                # luaotfload writes its font cache under HOME.
                export HOME=$(mktemp -d)
                pytest -p no:cacheprovider ${pytestArgs}
                touch $out
              '';
        in
        self.packages.${system}
        // {
          pytest = runTests "pytest" [ ] "";
          # The TeX Live engines against the committed baselines. Not tectonic:
          # it downloads its packages, and the build sandbox has no network.
          render = runTests "render" [
            tex
            pkgs.diff-pdf
          ] "-m render -k 'not tectonic' --require-engines";
        }
      );

      formatter = forAllSystems ({ pkgs, ... }: pkgs.nixfmt);
    };
}
