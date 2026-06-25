import json
from agent import run_agent


def keyword_score(text, keywords):
    text = text.lower()

    found = 0

    for keyword in keywords:
        if keyword.lower() in text:
            found += 1

    return found / len(keywords)


def retrieval_score(evidence_map, expected_sources):

    retrieved_files = set()

    for evidences in evidence_map.values():
        for e in evidences:
            filename = e.file.split("\\")[-1]
            retrieved_files.add(filename)

    expected_files = set(expected_sources)

    matched = len(
        expected_files.intersection(retrieved_files)
    )

    return matched / len(expected_files)
   
def faithfulness_score(answer, evidences):

    evidence_text = " ".join(
        e.snippet.lower()
        for e in evidences
    )

    answer_words = set(
        answer.lower().split()
    )

    matched = 0

    for word in answer_words:
        if word in evidence_text:
            matched += 1

    return matched / max(len(answer_words), 1)


with open("evaluation_dataset.json", "r") as f:
    dataset = json.load(f)

results = []

for case in dataset:

    print(f"Running: {case['topic']}")

    result = run_agent(case["topic"])

    accuracy = keyword_score(
        result["report"],
        case["expected_keywords"]
    )

    retrieval = retrieval_score(
        result["evidence"],
        case["expected_sources"]
    )

    faithfulness_scores = []

    for question, answer in result["answers"].items():

        evidences = result["evidence"][question]

        score = faithfulness_score(
            answer,
            evidences
        )

        faithfulness_scores.append(score)

    faithfulness = (
        sum(faithfulness_scores)
        / len(faithfulness_scores)
    )

    print("Accuracy =", accuracy)
    print("Retrieval =", retrieval)
    print("Faithfulness =", faithfulness)

    results.append({
        "topic": case["topic"],
        "accuracy_score": accuracy,
        "retrieval_score": retrieval,
        "faithfulness_score": faithfulness
    })
with open("evaluation_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Evaluation completed.")