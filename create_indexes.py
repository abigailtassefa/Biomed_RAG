import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")


driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)


VECTOR_INDEX_QUERIES = [
    """
    CREATE VECTOR INDEX symptom_embeddings IF NOT EXISTS
    FOR (symptom:Symptom)
    ON symptom.embedding
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 384,
            `vector.similarity_function`: 'cosine'
        }
    }
    """,
    """
    CREATE VECTOR INDEX disease_embeddings IF NOT EXISTS
    FOR (disease:Disease)
    ON disease.embedding
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 384,
            `vector.similarity_function`: 'cosine'
        }
    }
    """,
    """
    CREATE VECTOR INDEX drug_embeddings IF NOT EXISTS
    FOR (drug:Drug)
    ON drug.embedding
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 384,
            `vector.similarity_function`: 'cosine'
        }
    }
    """
]


INDEX_NAMES = [
    "symptom_embeddings",
    "disease_embeddings",
    "drug_embeddings"
]


def create_vector_indexes():
    with driver.session(database=NEO4J_DATABASE) as session:
        for query in VECTOR_INDEX_QUERIES:
            session.run(query).consume()

        result = session.run(
            """
            SHOW VECTOR INDEXES
            YIELD name, state, populationPercent
            WHERE name IN $index_names
            RETURN name, state, populationPercent
            ORDER BY name
            """,
            index_names=INDEX_NAMES
        )

        indexes = list(result)

    for index in indexes:
        print(
            f"{index['name']}: "
            f"{index['state']} "
            f"({index['populationPercent']}%)"
        )


def main():
    try:
        driver.verify_connectivity()
        create_vector_indexes()
        print("Vector-index setup completed.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()