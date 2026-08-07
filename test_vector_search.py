from neo4j import GraphDatabase
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import os


load_dotenv()


URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE")


driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)


model = SentenceTransformer("all-MiniLM-L6-v2")


question = "I have high blood sugar. What medicine can help?"


question_embedding = model.encode(question).tolist()


with driver.session(database=DATABASE) as session:

    result = session.run(
        """
        CALL db.index.vector.queryNodes(
            'disease_embeddings',
            3,
            $embedding
        )
        YIELD node, score

        RETURN 
            node.Name AS disease,
            node.Category AS category,
            score
        """,
        embedding=question_embedding
    )


    for record in result:

        print("----------------")
        print("Disease:", record["disease"])
        print("Category:", record["category"])
        print("Similarity:", record["score"])


driver.close()