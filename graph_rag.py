from neo4j import GraphDatabase
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from google import genai
import os


# -----------------------------------
# Load environment variables
# -----------------------------------

load_dotenv()


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# -----------------------------------
# Neo4j connection
# -----------------------------------

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)


# -----------------------------------
# Gemini setup
# -----------------------------------

client = genai.Client(
    api_key=GEMINI_API_KEY
)




# -----------------------------------
# Embedding model
# -----------------------------------

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# -----------------------------------
# User question
# -----------------------------------

question = input(
    "\nAsk a biomedical question: "
)


# -----------------------------------
# Convert question to embedding
# -----------------------------------

question_embedding = embedding_model.encode(
    question
).tolist()



# -----------------------------------
# Retrieve information from graph
# -----------------------------------

query = """

CALL db.index.vector.queryNodes(
    'symptom_embeddings',
    3,
    $embedding
)

YIELD node, score


MATCH (d:Disease)-[:HAS_SYMPTOM]->(node)


MATCH (drug:Drug)-[:TREATS]->(d)


RETURN
    node.Name AS symptom,
    d.Name AS disease,
    d.Category AS category,
    drug.Name AS drug,
    drug.Dosage AS dosage,
    score

ORDER BY score DESC

"""


context = ""


with driver.session(database=NEO4J_DATABASE) as session:


    results = session.run(
        query,
        embedding=question_embedding
    )


    for record in results:


        context += f"""

        Symptom:
        {record['symptom']}

        Disease:
        {record['disease']}

        Category:
        {record['category']}

        Treatment:
        {record['drug']}

        Dosage:
        {record['dosage']}

        -------------------

        """



# -----------------------------------
# Check retrieved context
# -----------------------------------

print("\n========== RETRIEVED GRAPH CONTEXT ==========\n")

print(context)



# -----------------------------------
# Create prompt for Gemini
# -----------------------------------

prompt = f"""

You are a biomedical assistant.

Answer the user's question using ONLY the information
provided in the context.

If the context does not contain enough information,
say that the graph does not provide enough information.

User Question:

{question}


Biomedical Graph Context:

{context}


Provide a clear and concise answer.

"""


# -----------------------------------
# Generate final answer
# -----------------------------------

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt

)


print("\n========== FINAL ANSWER ==========\n")

print(response.text)



# -----------------------------------
# Close connection
# -----------------------------------

driver.close()