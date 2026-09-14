from neo4j import GraphDatabase
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from google import genai
import os


load_dotenv()


REQUIRED_ENV_VARIABLES = (
    "NEO4J_URI",
    "NEO4J_USERNAME",
    "NEO4J_PASSWORD",
    "NEO4J_DATABASE",
    "GEMINI_API_KEY",
)


def validate_environment():
    missing_variables = [
        variable
        for variable in REQUIRED_ENV_VARIABLES
        if not os.getenv(variable, "").strip()
    ]

    if missing_variables:
        missing_names = ", ".join(missing_variables)

        raise RuntimeError(
            "Missing required environment variables: "
            f"{missing_names}. "
            "Copy .env.example to .env and provide the required values."
        )


validate_environment()






# Neo4j
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE")


driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)


# Embedding model
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# Gemini
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def graph_rag(question):
    embedding = embedding_model.encode(
        question
    ).tolist()


    symptom_query = """
         MATCH (node:Symptom)
SEARCH node IN (
    VECTOR INDEX symptom_embeddings
    FOR $embedding
    LIMIT 3
) SCORE AS score

OPTIONAL MATCH (d:Disease)-[:HAS_SYMPTOM]->(node)
OPTIONAL MATCH (drug:Drug)-[:TREATS]->(d)

RETURN
    'Symptom' AS match_type,
    node.Name AS matched_name,
    node.Name AS symptom,
    d.Name AS disease,
    d.Aliases AS disease_aliases,
    d.Category AS category,
    drug.Name AS drug,
    drug.Dosage AS dosage,
    score
"""


    disease_query = """
MATCH (node:Disease)
SEARCH node IN (
    VECTOR INDEX disease_embeddings
    FOR $embedding
    LIMIT 3
) SCORE AS score

OPTIONAL MATCH (node)-[:HAS_SYMPTOM]->(symptom:Symptom)
OPTIONAL MATCH (drug:Drug)-[:TREATS]->(node)

RETURN
    'Disease' AS match_type,
    node.Name AS matched_name,
    symptom.Name AS symptom,
    node.Name AS disease,
    node.Aliases AS disease_aliases,
    node.Category AS category,
    drug.Name AS drug,
    drug.Dosage AS dosage,
    score
"""


    drug_query = """
MATCH (node:Drug)
SEARCH node IN (
    VECTOR INDEX drug_embeddings
    FOR $embedding
    LIMIT 3
) SCORE AS score

OPTIONAL MATCH (node)-[:TREATS]->(d:Disease)
OPTIONAL MATCH (d)-[:HAS_SYMPTOM]->(symptom:Symptom)


RETURN
    'Drug' AS match_type,
    node.Name AS matched_name,
    symptom.Name AS symptom,
    d.Name AS disease,
    d.Aliases AS disease_aliases,
    d.Category AS category,
    node.Name AS drug,
    node.Dosage AS dosage,
    score
"""


    records = []

    with driver.session(database=DATABASE) as session:
         symptom_results = session.run(
        symptom_query,
        embedding=embedding
    )

         records.extend(list(symptom_results))

         disease_results = session.run(
        disease_query,
        embedding=embedding
    )

         records.extend(list(disease_results))

         drug_results = session.run(
        drug_query,
        embedding=embedding
    )

         records.extend(list(drug_results))
    
    if not records:
        return (
            "I could not find enough information in the biomedical "
            "knowledge graph to answer that question."
        )
    records.sort(
        key=lambda record: record["score"],
        reverse=True,
    )
    context_parts = []

    for record in records:
        aliases = record["disease_aliases"] or []
        alias_text = ", ".join(aliases) or "Not available"

        context_parts.append(
            f"""
        Matched node type: {record["match_type"]}
        Matched node name: {record["matched_name"]}
        Symptom: {record["symptom"] or "Not available"}
        Disease: {record["disease"] or "Not available"}
        Disease aliases: {alias_text}
        Category: {record["category"] or "Not available"}
        Drug: {record["drug"] or "Not available"}
        Dosage: {record["dosage"] or "Not available"}
        Similarity score: {record["score"]:.3f}
        """
        )

    context = "\n".join(context_parts)

    prompt = f"""
You are a biomedical knowledge graph assistant.

Answer the question using ONLY the information in the
Biomedical Graph Context below.

Rules:
1. Do not use outside knowledge.
2. Do not guess or invent diseases, drugs, or dosages.
3. If the context is missing the information needed to answer,
   say: "The biomedical knowledge graph does not provide enough
   information to answer this question."
4. Disease aliases listed in the context are graph data and may
   be used to connect the user's wording to a disease.
5. Clearly state when a disease, drug, or dosage is unavailable.
6. Keep the answer clear and concise.

User question:
{question}

Biomedical Graph Context:
{context}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text


def close_resources():
    driver.close()
    client.close()
    

