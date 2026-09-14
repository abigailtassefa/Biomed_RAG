import atexit

from flask import Flask, jsonify, render_template, request
from google.genai import errors as genai_errors
from neo4j.exceptions import DriverError, Neo4jError

from rag_service import close_resources, graph_rag


app = Flask(__name__)

atexit.register(close_resources)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be valid JSON."
        }), 400

    question = data.get("question")

    if not isinstance(question, str) or not question.strip():
        return jsonify({
            "error": "Please enter a question."
        }), 400

    try:
        answer = graph_rag(question.strip())

        return jsonify({
            "answer": answer
        })

    except (DriverError, Neo4jError):
        app.logger.exception("Neo4j request failed")

        return jsonify({
            "error": (
                "The biomedical database is currently unavailable. "
                "Please try again later."
            )
        }), 503

    except genai_errors.APIError:
        app.logger.exception("Gemini API request failed")

        return jsonify({
            "error": (
                "The answer-generation service is currently unavailable. "
                "Please try again later."
            )
        }), 502

    except Exception:
        app.logger.exception("Unexpected application error")

        return jsonify({
            "error": (
                "An unexpected error occurred. "
                "Please try again later."
            )
        }), 500


if __name__ == "__main__":
    app.run()