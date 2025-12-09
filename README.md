# Mem1 🧠

**A Hybrid Memory Framework for LLMs & AI Agents.**

Mem1 is an advanced memory layer designed to give AI agents long-term, consistent, and structured memory. It goes beyond simple vector retrieval by integrating a **Knowledge Graph** to capture relationships and a **Vector Database** for semantic search.

This project is an implementation inspired by the [Mem0 research paper](https://arxiv.org/pdf/2504.19413), extended with a robust GraphRAG approach to handle entity relationships (e.g., *User -> working on -> Project*).

---

## 🚀 Key Features

* **Hybrid Memory Architecture:** Combines **Qdrant** (Vector DB) for semantic similarity with **Memgraph** (Graph DB) for structural associativity.
* **GraphRAG Capabilities:** Automatically extracts entities (Person, Project, Tool) and relationships from user conversations.
* **Smart Entity Resolution:** Uses Fuzzy Search + LLM verification to de-duplicate entities (e.g., mapping "JS" and "Node" to `JavaScript`).
* **Dynamic Fact Management:** Intelligently decides whether to `ADD` a new fact, `UPDATE` an existing one, or `IGNORE` redundancy.
* **Deep Context Retrieval:** Performs 2-hop graph traversals to fetch context that is structurally related but might not be semantically similar.
* **Observability:** Integrated with **Langfuse** for tracing and monitoring agent performance.

## 🛠️ Tech Stack

* **Language:** Python 3.11+
* **Vector Database:** Qdrant
* **Graph Database:** Memgraph (Neo4j compatible)
* **App Database:** MongoDB (via Beanie/Motor)
* **Embeddings:** HuggingFace Text Embeddings Inference (TEI)
* **Environment:** Nix & Docker Compose
* **Dependency Management:** `uv`

---

## 🏗️ Architecture

When a user sends a message, Mem1 processes it through the following pipeline:

1. **Summarization:** Compresses recent chat history.
2. **Fact Extraction:** Identifies new candidate facts.
3. **Semantic Retrieval:** Queries **Qdrant** for similar past memories.
4. **Graph Retrieval:** Traverses **Memgraph** to find related entities (2-hop neighborhood).
5. **Memory Write:**
    * Updates Vector DB with the new fact.
    * Extracts triplets *(Subject, Predicate, Object)*.
    * Resolves entities (Entity Resolution) and upserts them into the Knowledge Graph.

---

## ⚡ Getting Started

### Prerequisites

* **Docker & Docker Compose** (Essential for running DBs)
* **Nix** (Optional, for reproducible dev environment)
* **Just** (Command runner)

### 1. Environment Setup

Clone the repository and set up your environment variables.

```bash
cp .env.example .env
```

Make sure to populate .env with your API keys (OpenAI, etc.) and configuration preferences.

### 2. Initialize Environment

If you are using Nix:

```bash
nix develop
```

If you are using standard Python:

```bash
pip install uv
uv sync
```

### 3. Start Infrastructure

Start the underlying services (Qdrant, Memgraph, MongoDB, Langfuse, TEI) using Docker Compose. We use `just` for convenience.

```bash
just start
```

### 4. Run the Application

Once the Docker services are healthy, start the main application:

```bash
just app
```

To view the application logs:

```bash
just logs
```

## 📊 Visualizing Memory

Mem1 includes **Memgraph Lab** to visualize your agent's Knowledge Graph in real-time.

1. Open your browser to http://localhost:3001.

2. Connection Details:

    - **Host:** `localhost`

    - **Port:** `7687` (or 7688 if configured differently in docker-compose)

    - **Username/Password:** See your docker-compose.yml (Default: memgraph / memg_password)

3. Run a Query: To see the entities created by your agent:

```bash
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100;
```

Thanks :)
