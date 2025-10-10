{
  description="Nix environment for the project with CUDA support";

  inputs={
    nixpkgs.url="github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs={ self, nixpkgs }: {
    devShells.x86_64-linux.default = let
      pkgs = import nixpkgs{
        system = "x86_64-linux";
        config = {
          allowUnfree = true;
          cudaSupport = true;
        };
    };
    in
    pkgs.mkShell {
      buildInputs = with pkgs; [
        python311
        uv

        git
        gcc
        cmake
        ninja
        pkg-config

        rustc
        cargo

        cudaPackages.cudatoolkit
        cudaPackages.cuda_nvcc
        cudaPackages.libcublas
        cudaPackages.cuda_cudart

        stdenv.cc.cc.lib
        zlib
        libffi

      ];

      shellHook = ''
      export CUDA_HOME="${pkgs.cudaPackages.cudatoolkit}"
      export CUDA_PATH="${pkgs.cudaPackages.cudatoolkit}"
      export LD_LIBRARY_PATH="${pkgs.cudaPackages.cudatoolkit}/lib:${pkgs.cudaPackages.libcublas}/lib:${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"

      export CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_COMPILER=${pkgs.cudaPackages.cuda_nvcc}/bin/nvcc"
      export FORCE_CMAKE=1

      export PATH="${pkgs.cudaPackages.cuda_nvcc}/bin:$PATH"

      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "  Nix shell activated!"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo ""
      echo "  Python: $(python --version)"
      echo "  uv:     $(uv --version)"
      echo "  nvcc:   $(nvcc --version | head -n1)"
      echo ""
      echo "  CUDA support is configured."
      echo "  Ready to build llama-cpp-python with GPU support."
      echo ""
      '';
    };
  };
}
