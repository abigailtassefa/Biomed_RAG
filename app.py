from flask import Flask, request, jsonify, render_template
from neo4j import GraphDatabase
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from google import genai
import os


load_dotenv()


app = Flask(__name__)


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


    query = """

    CALL db.index.vector.queryNodes(
        'symptom_embeddings',
        1,
        $embedding
    )
    YIELD node, score


    MATCH (d:Disease)-[:HAS_SYMPTOM]->(node)

    MATCH (drug:Drug)-[:TREATS]->(d)


    RETURN
        node.Name AS symptom,
        d.Name AS disease,
        drug.Name AS drug,
        drug.Dosage AS dosage

    """


    context = ""


    with driver.session(database=DATABASE) as session:

        result = session.run(
            query,
            embedding=embedding
        )


        for r in result:

            context += f"""
            Symptom: {r['symptom']}
            Disease: {r['disease']}
            Drug: {r['drug']}
            Dosage: {r['dosage']}
            """



    prompt = f"""

    Answer using only this biomedical graph information.

    Question:
    {question}


    Context:
    {context}

    """


    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )


    return response.text



@app.route("/")
def home():

    return render_template(
        "index.html"
    )



@app.route("/ask", methods=["POST"])
def ask():

    data = request.json

    question = data["question"]

    answer = graph_rag(question)


    return jsonify(
        {
            "answer": answer
        }
    )



if __name__ == "__main__":

    app.run(
        debug=True
    )
    