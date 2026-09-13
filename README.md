# Biomedical Graph RAG

A biomedical question-answering application that combines a Neo4j knowledge graph, semantic vector search, and Google Gemini.

The application converts a user's question into an embedding, searches biomedical entities stored in Neo4j, expands their graph relationships, and asks Gemini to generate an answer using the retrieved graph context.

## Features

- Biomedical knowledge graph stored in Neo4j AuraDB
- Synthetic biomedical dataset
- Disease, symptom, and drug embeddings
- Semantic vector search using Sentence Transformers
- Graph-based context expansion
- Gemini-generated natural-language answers
- Flask web interface
- Frontend and backend input validation
- Separate Neo4j, Gemini, and application error handling
- Grounding instructions to reduce unsupported medical answers
- Reproducible graph and vector-index setup

## How It Works

1. The user submits a biomedical question.
2. `all-MiniLM-L6-v2` converts the question into a 384-dimensional embedding.
3. Neo4j searches three vector indexes:
   - `symptom_embeddings`
   - `disease_embeddings`
   - `drug_embeddings`
4. The application follows graph relationships to retrieve related symptoms, diseases, drugs, categories, and dosages.
5. The retrieved records are formatted as context.
6. Gemini generates an answer using the retrieved graph information.
7. If the context is insufficient, Gemini is instructed not to guess.

## Technologies Used

- Python
- Flask
- Neo4j AuraDB
- Cypher
- Sentence Transformers
- Google Gemini
- HTML
- JavaScript

## Project Structure

```text
Biomed_RAG/
├── data/
│   └── graph_data.json
├── templates/
│   └── index.html
├── app.py
├── create_indexes.py
├── embed_nodes.py
├── graph_rag.py
├── setup_graph.py
├── test_vector_search.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Prerequisites

Before running the project, you need:

- Python 3.10 or newer
- Git
- A Neo4j AuraDB instance
- A Gemini API key
- An internet connection for Neo4j, Gemini, and the initial embedding-model download

Create a Neo4j AuraDB instance at:

https://console.neo4j.io/

Create a Gemini API key at:

https://aistudio.google.com/app/apikey

> Neo4j AuraDB Free instances may pause after a period of inactivity. Make sure the instance is running before starting the application.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/abigailtassefa/Biomed_RAG.git
cd Biomed_RAG
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install the dependencies

```bash
python -m pip install -r requirements.txt
```

The first use of Sentence Transformers may download the `all-MiniLM-L6-v2` model from Hugging Face.

## Environment Configuration

Copy the environment-variable template.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder values with your own credentials:

```env
NEO4J_URI=neo4j+s://your-instance-id.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password
NEO4J_DATABASE=neo4j
GEMINI_API_KEY=your-gemini-api-key
```

Do not commit `.env`. It contains private credentials and is excluded through `.gitignore`.

## Prepare the Neo4j Database

A newly created Neo4j AuraDB instance is empty. This repository contains the synthetic graph data and scripts needed to reconstruct the database.

Make sure the AuraDB instance is running and the `.env` credentials are configured before continuing.

### 1. Import the graph data

```bash
python setup_graph.py
```

This imports:

- 46 nodes
- 63 relationships

The graph contains these node labels:

- `Patient`
- `Disease`
- `Symptom`
- `Drug`
- `DrugRating`

It contains these relationship types:

- `HAS_DISEASE`
- `HAS_SYMPTOM`
- `TAKES`
- `TREATS`
- `RATED`
- `BELONGS_TO`

The setup script uses `MERGE`, so running it more than once should not duplicate the graph.

### 2. Create the vector indexes

```bash
python create_indexes.py
```

This creates:

- `symptom_embeddings`
- `disease_embeddings`
- `drug_embeddings`

Each vector index uses:

- 384 dimensions
- Cosine similarity

The dimension is 384 because the project uses the `all-MiniLM-L6-v2` embedding model.

The script uses `IF NOT EXISTS`, so it can be run again without creating duplicate indexes.

### 3. Generate node embeddings

```bash
python embed_nodes.py
```

This generates embeddings for:

- Disease nodes
- Symptom nodes
- Drug nodes

The embeddings are stored in each node's `embedding` property.

### 4. Confirm the vector indexes

In the Neo4j Query interface, run:

```cypher
SHOW VECTOR INDEXES
YIELD name, state, populationPercent
RETURN name, state, populationPercent
ORDER BY name
```

Before using the application, confirm that these indexes show the state `ONLINE`:

```text
disease_embeddings
drug_embeddings
symptom_embeddings
```

## Run the Application

Start the Flask application:

```bash
python app.py
```

Open the following address in a browser:

```text
http://127.0.0.1:5000
```

Enter a biomedical question and select **Ask**.

## Complete Setup Command Order

After creating and configuring an empty Neo4j AuraDB instance, run:

```bash
python setup_graph.py
python create_indexes.py
python embed_nodes.py
python app.py
```

## Run the Command-Line Version

To ask a question directly from the terminal, run:

```bash
python graph_rag.py
```

Enter a biomedical question when prompted.

## Test Vector Search

Run:

```bash
python test_vector_search.py
```

This performs a direct Neo4j vector search and prints matching records and similarity scores.

## Example Questions

Symptom-based question:

```text
What medicine helps with high blood sugar?
```

Disease-based question:

```text
What symptoms does Type 2 Diabetes have?
```

Drug-based question:

```text
What condition does Metformin treat?
```

## Example Response

The exact answer depends on the records retrieved from the graph. An example is:

```text
Based on the biomedical knowledge graph, Metformin is used to
treat Type 2 Diabetes, which is associated with high blood sugar.
```

If the graph context is insufficient, the application responds with a message similar to:

```text
The biomedical knowledge graph does not provide enough
information to answer this question.
```

## Graph Schema

The application primarily retrieves information using these patterns:

```text
(Disease)-[:HAS_SYMPTOM]->(Symptom)
(Drug)-[:TREATS]->(Disease)
```

The complete synthetic graph also contains:

```text
(Patient)-[:HAS_DISEASE]->(Disease)
(Patient)-[:TAKES]->(Drug)
(Patient)-[:RATED]->(DrugRating)
(DrugRating)-[:BELONGS_TO]->(Drug)
```


## Synthetic Dataset

`data/graph_data.json` contains the synthetic nodes and
relationships required to reconstruct the database.

Embedding arrays are not stored in this file because they are
large and can be regenerated by running:

```bash
python embed_nodes.py 

## Request Validation

The `/ask` endpoint verifies that:

- The request body contains valid JSON.
- A `question` field is present.
- The question is a string.
- The question is not empty or made entirely of spaces.

Invalid input returns HTTP status `400`.

The frontend also checks for empty input so users receive immediate feedback.

## Error Handling

The application handles several types of failure:

- Invalid requests return HTTP `400`.
- Gemini API failures return HTTP `502`.
- Neo4j failures return HTTP `503`.
- Unexpected application failures return HTTP `500`.

Detailed technical errors are logged in the Flask terminal. The browser receives safer, user-friendly messages without stack traces or credentials.

## Security Improvements

- Flask debug mode is disabled.
- The frontend uses `textContent` instead of `innerHTML`.
- Requests are validated by both the frontend and backend.
- Neo4j and Gemini errors are handled separately.
- Credentials are loaded from `.env`.
- `.env` is excluded from Git.
- Only `.env.example` with placeholder values is committed.
- Graph-import labels and relationship types are restricted to expected values.

## Troubleshooting

### Missing environment variables

If the application reports missing environment variables:

1. Confirm that `.env` exists in the project root.
2. Compare it with `.env.example`.
3. Ensure every required value is present and non-empty.
4. Restart the application after changing `.env`.

### Neo4j is unavailable

Confirm that:

- The AuraDB instance is running.
- `NEO4J_URI` is correct.
- `NEO4J_USERNAME` is correct.
- `NEO4J_PASSWORD` is correct.
- `NEO4J_DATABASE` contains the correct database name.
- The computer has an internet connection.

### A vector index is unavailable

Run:

```cypher
SHOW VECTOR INDEXES
```

Confirm that the required indexes exist and have the state `ONLINE`.

If they do not exist, run:

```bash
python create_indexes.py
```

Then regenerate the embeddings:

```bash
python embed_nodes.py
```

### Gemini is unavailable

Confirm that:

- `GEMINI_API_KEY` is valid.
- The configured Gemini model is currently available.
- The account has available API quota.
- The computer has an internet connection.

### Hugging Face warning

The embedding model can normally be downloaded without authentication. An optional Hugging Face token can provide higher download rate limits, but it is not required to run this project.

### The graph does not contain enough information

This project uses a small synthetic dataset. Questions outside that dataset may produce an insufficient-information response.

Semantic retrieval may also fail to recognize some synonyms unless they are represented in the graph or embedding text.

## Limitations

- The project uses a small synthetic biomedical dataset.
- Answers are limited to information retrieved from that graph.
- Semantic retrieval may not recognize every synonym.
- Vector search may return the nearest node even when the similarity is weak.
- The application does not currently provide source citations in its answers.
- The Flask server started by `app.py` is intended for development and demonstration.
- The application is an educational prototype, not a clinical system.

## Medical Disclaimer

This project is for educational purposes only.

It does not provide medical diagnosis, professional treatment recommendations, or medical advice. Do not use its responses as a substitute for guidance from a qualified healthcare professional.

## Future Improvements

- Add automated tests
- Calibrate a minimum retrieval-similarity threshold
- Add explicit medical synonyms and aliases
- Reduce duplicated RAG logic between `app.py` and `graph_rag.py`
- Improve the web interface
- Add retrieved-source information to answers
- Use a production WSGI server for deployment

## Author

Abigail 