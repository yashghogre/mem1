## mem1

Replicating the [mem0 paper](https://arxiv.org/pdf/2504.19413) for LLM memory and possibly trying to out-perform it XD

### Setup and initialization

1. Setup environment variables in `.env` file. Refer `.env.example` file for variables' info.

2. Start the Nix environment

```bash
nix develop
```

3. Install the Python dependencies

```bash
uv sync
```

4. Add your own model in the root directory in `models/` directory. The model must be in gguf format.

5. Start the program. This will automatically start the underlying docker compose services essential for the working of this project.

```bash
just start
```

> 💡 Tip: To start the mongodb shell (mongosh), use `just mongo`

6. To stop the project, i.e., to stop the running docker containers (refresh the services, if need be), use:

```bash
just stop
```
