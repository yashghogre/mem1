## mem1

Replicating the mem0 paper for LLM memory and possibly trying to out-perform it XD

### Setup and initialization

1. Start the Nix environment

```bash
nix develop
```

2. Install the Python dependencies

```bash
uv sync
```

3. Install `llama-cpp-python` library (TODO: Add this in pyproject.toml for `uv sync`)

```bash
uv pip install llama-cpp-python --no-cache-dir
```

4. Add your own model in the root directory in `models/` directory. The model must be in gguf format.
