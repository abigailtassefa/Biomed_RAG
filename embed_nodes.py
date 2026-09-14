from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE")

# -----------------------------
# Connect to Neo4j
# -----------------------------
driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_diseases():
    """Retrieve every disease with its symptoms and treatment."""

    query = """
    MATCH (d:Disease)

    OPTIONAL MATCH (d)-[:HAS_SYMPTOM]->(s:Symptom)
    OPTIONAL MATCH (drug:Drug)-[:TREATS]->(d)

    RETURN
        d.Name AS disease,
        d.Aliases AS aliases,
        d.Category AS category,
        collect(DISTINCT s.Name) AS symptoms,
        collect(DISTINCT drug.Name) AS drugs
    ORDER BY disease
    """

    with driver.session(database=DATABASE) as session:
        return session.execute_read(
            lambda tx: list(tx.run(query))
        )
def get_drugs():

    query = """
    MATCH (drug:Drug)

    OPTIONAL MATCH (drug)-[:TREATS]->(d:Disease)

    RETURN
        drug.Name AS drug,
        drug.Dosage AS dosage,
        collect(DISTINCT d.Name) AS diseases
    """

    with driver.session(database=DATABASE) as session:
        return list(session.run(query))

def save_drug_embedding(drug_name, embedding):

    query = """
    MATCH (drug:Drug {Name:$name})

    SET drug.embedding = $embedding
    """

    with driver.session(database=DATABASE) as session:

        session.run(
            query,
            name=drug_name,
            embedding=embedding.tolist()
        )

def create_drug_embeddings():

    records = get_drugs()

    for record in records:

        text = f"""
        Drug: {record['drug']}.
        Dosage: {record['dosage']}.
        Treats: {", ".join(record['diseases'])}.
        """

        embedding = model.encode(text)

        save_drug_embedding(
            record["drug"],
            embedding
        )

        print(record["drug"], "saved")

def save_embedding(disease_name, embedding):

    query = """
    MATCH (d:Disease {Name:$name})

    SET d.embedding = $embedding
    """

    with driver.session(database=DATABASE) as session:

        session.run(
            query,
            name=disease_name,
            embedding=embedding.tolist()
        )
def get_symptoms():

    query = """
    MATCH (s:Symptom)

    OPTIONAL MATCH (d:Disease)-[:HAS_SYMPTOM]->(s)

    RETURN
        s.Name AS symptom,
        collect(DISTINCT d.Name) AS diseases
    """

    with driver.session(database=DATABASE) as session:
        return list(session.run(query))

def save_symptom_embedding(symptom_name, embedding):

    query = """
    MATCH (s:Symptom {Name:$name})

    SET s.embedding = $embedding
    """

    with driver.session(database=DATABASE) as session:

        session.run(
            query,
            name=symptom_name,
            embedding=embedding.tolist()
        )

def create_symptom_embeddings():

    records = get_symptoms()

    for record in records:

        text = f"""
        Symptom: {record['symptom']}.
        Associated diseases: {", ".join(record['diseases'])}.
        """

        embedding = model.encode(text)

        save_symptom_embedding(
            record["symptom"],
            embedding
        )

        print(record["symptom"], "saved")  


def create_disease_embeddings():

    records = get_diseases()

    for record in records:
        aliases = record["aliases"] or []

        disease_text = f"""
        Disease: {record['disease']}.
        Category: {record['category']}.
        Symptoms: {", ".join(record['symptoms'])}.
        Treatment: {", ".join(record['drugs'])}.
        Aliases: {", ".join(aliases)}.
        """

        embedding = model.encode(disease_text)

        save_embedding(
            record["disease"],
            embedding
        )

        print(
            record["disease"],
            "embedding saved"
        )


def main():
    create_disease_embeddings()
    create_symptom_embeddings()
    create_drug_embeddings()

if __name__ == "__main__":
    main()
    driver.close()
