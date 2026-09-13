import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")


# Each node type has a stable ID property.
NODE_IDENTIFIERS = {
    "Patient": "PatientID",
    "Disease": "DiseaseID",
    "Symptom": "SymptomID",
    "Drug": "DrugID",
    "DrugRating": "RatingID",
}


# Only these relationship types may be imported.
ALLOWED_RELATIONSHIPS = {
    "BELONGS_TO",
    "HAS_DISEASE",
    "HAS_SYMPTOM",
    "RATED",
    "TAKES",
    "TREATS",
}


driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)


def load_graph_data():
    data_path = (
        Path(__file__).resolve().parent
        / "data"
        / "graph_data.json"
    )

    with data_path.open("r", encoding="utf-8") as data_file:
        return json.load(data_file)


def import_nodes(session, nodes):
    node_lookup = {}

    for node in nodes:
        labels = node["labels"]

        if len(labels) != 1:
            raise ValueError(
                f"Expected one label for node {node['export_id']}."
            )

        label = labels[0]

        if label not in NODE_IDENTIFIERS:
            raise ValueError(f"Unsupported node label: {label}")

        id_property = NODE_IDENTIFIERS[label]
        properties = node["properties"]
        identifier = properties.get(id_property)

        if identifier is None:
            raise ValueError(
                f"{label} node is missing {id_property}."
            )

        query = f"""
        MERGE (node:`{label}` {{`{id_property}`: $identifier}})
        SET node += $properties
        """

        session.run(
            query,
            identifier=identifier,
            properties=properties
        ).consume()

        node_lookup[node["export_id"]] = {
            "label": label,
            "id_property": id_property,
            "identifier": identifier
        }

    return node_lookup


def import_relationships(
    session,
    relationships,
    node_lookup
):
    for relationship in relationships:
        relationship_type = relationship["type"]

        if relationship_type not in ALLOWED_RELATIONSHIPS:
            raise ValueError(
                "Unsupported relationship type: "
                f"{relationship_type}"
            )

        start_node = node_lookup[relationship["start_id"]]
        end_node = node_lookup[relationship["end_id"]]

        query = f"""
        MATCH
            (start:`{start_node["label"]}`
                {{`{start_node["id_property"]}`: $start_identifier}})
        MATCH
            (end:`{end_node["label"]}`
                {{`{end_node["id_property"]}`: $end_identifier}})
        MERGE
            (start)-[relationship:`{relationship_type}`]->(end)
        SET relationship += $properties
        """

        session.run(
            query,
            start_identifier=start_node["identifier"],
            end_identifier=end_node["identifier"],
            properties=relationship["properties"]
        ).consume()


def setup_graph():
    graph_data = load_graph_data()
    nodes = graph_data["nodes"]
    relationships = graph_data["relationships"]

    with driver.session(database=NEO4J_DATABASE) as session:
        node_lookup = import_nodes(session, nodes)

        import_relationships(
            session,
            relationships,
            node_lookup
        )

    print(f"Imported {len(nodes)} nodes.")
    print(f"Imported {len(relationships)} relationships.")


def main():
    try:
        driver.verify_connectivity()
        setup_graph()
        print("Graph setup completed successfully.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()