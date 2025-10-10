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

3. Add your own model in the `models/` directory. The model must be in gguf format.
