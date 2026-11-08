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
      forAllSystems = f: lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});

      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      # uv-dynamic-versioning reads the version from git tags, but a flake's
      # source has no .git, so supply one. The release version isn't knowable
      # here; the commit is.
      version = "0.0.0+${self.shortRev or self.dirtyShortRev or "unknown"}";

      pythonSet =
        pkgs:
        (pkgs.callPackage pyproject-nix.build.packages { python = pkgs.python3; }).overrideScope (
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

      # The same TeX Live CI's render-test job uses: scheme-small plus the
      # packages it installs from .circleci/texlive-packages.txt. The
      # texlive:latest-small image ships latexmk; nixpkgs' scheme-small doesn't.
      tex =
        pkgs:
        pkgs.texliveSmall.withPackages (
          ps:
          [ ps.latexmk ]
          ++ map (name: ps.${name}) (
            lib.filter (name: name != "") (
              lib.splitString "\n" (builtins.readFile ./.circleci/texlive-packages.txt)
            )
          )
        );

      # Unwrapped: the wrapper only adds biber, which a letter with no
      # bibliography never runs, and which roughly doubles tectonic's closure.
      tectonic = pkgs: pkgs.tectonic-unwrapped;

      # `render` looks its engine up on PATH, so engines are optional: each one
      # included here is put on the wrapper's PATH, ahead of the user's own.
      mkPackage =
        pkgs:
        lib.makeOverridable (
          {
            # xelatex (the default `--engine`), lualatex and pdflatex can't be
            # split: even scheme-basic ships all three, because latex-bin builds
            # every format. The engines are a small part of TeX Live's size.
            withTexLive ? true,
            # Smaller than TeX Live, but it downloads packages on first use.
            withTectonic ? false,
          }:
          let
            set = pythonSet pkgs;
            app = (pkgs.callPackage pyproject-nix.build.util { }).mkApplication {
              venv = set.mkVirtualEnv "uk-invitation-letter-env" workspace.deps.default;
              package = set.uk-invitation-letter;
            };
            engines = lib.optional withTexLive (tex pkgs) ++ lib.optional withTectonic (tectonic pkgs);
          in
          if engines == [ ] then
            app
          else
            app.overrideAttrs (old: {
              nativeBuildInputs = old.nativeBuildInputs ++ [ pkgs.makeWrapper ];
              postFixup = ''
                wrapProgram $out/bin/uk-invitation-letter \
                  --prefix PATH : ${lib.makeBinPath engines}
              '';
            })
        ) { };

      mkDevShell =
        pkgs: extraPackages:
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
        };
    in
    {
      packages = forAllSystems (
        pkgs:
        let
          package = mkPackage pkgs;
        in
        {
          # TeX Live, so `nix run` renders with the default engine on a machine
          # with no TeX installed.
          default = package;
          # Tectonic only: `render --engine tectonic`, at under half the size.
          tectonic = package.override {
            withTexLive = false;
            withTectonic = true;
          };
          # No engines: uses whatever TeX is already on PATH.
          bare = package.override { withTexLive = false; };
        }
      );

      devShells = forAllSystems (pkgs: {
        # Enough for `uv run pytest`: the render tests are opt-in.
        default = mkDevShell pkgs [ ];
        # For `uv run pytest -m render`: every engine the render tests cover,
        # and diff-pdf to compare against the baselines.
        render = mkDevShell pkgs [
          (tex pkgs)
          (tectonic pkgs)
          pkgs.diff-pdf
        ];
      });

      checks = forAllSystems (
        pkgs:
        let
          set = pythonSet pkgs;
          testEnv = set.mkVirtualEnv "uk-invitation-letter-test-env" (
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
        self.packages.${pkgs.stdenv.hostPlatform.system}
        // {
          pytest = runTests "pytest" [ ] "";
          # The TeX Live engines against the committed baselines. Not tectonic:
          # it downloads its packages, and the build sandbox has no network.
          render = runTests "render" [
            (tex pkgs)
            pkgs.diff-pdf
          ] "-m render -k 'not tectonic' --require-engines";
        }
      );

      formatter = forAllSystems (pkgs: pkgs.nixfmt);
    };
}
