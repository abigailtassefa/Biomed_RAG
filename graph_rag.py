from rag_service import close_resources, graph_rag


def main():
    question = input(
        "\nAsk a biomedical question: "
    ).strip()

    if not question:
        print("Please enter a question.")
        return

    answer = graph_rag(question)

    print("\n========== FINAL ANSWER ==========\n")
    print(answer)


if __name__ == "__main__":
    try:
        main()
    finally:
        close_resources()