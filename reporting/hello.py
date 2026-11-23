from reporting.llm import generate


def main():
    prompt = "Explain what artificial intelligence is in one sentence."
    response = generate(prompt)
    print(response)


if __name__ == "__main__":
    main()
