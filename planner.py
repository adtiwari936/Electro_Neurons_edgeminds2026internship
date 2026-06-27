import json
from typing import List
from ollama_client import get_llm

def plan_subquestions(topic: str, max_subquestions: int = 5) -> List[str]:
    prompt = (
        "Create 3 to 5 focused research sub-questions for the topic below. "
        "The questions should be short, non-overlapping, and useful for local document search. "
        "Return only a JSON array of strings.\n\n"
        f"Topic: {topic}"
    )

    llm = get_llm()

    if llm is not None:
        try:
            response = llm.complete(prompt).text.strip()
            
            cleaned_response = response
            if "```" in cleaned_response:
                parts = cleaned_response.split("```")
                for part in parts:
                    candidate = part.strip()
                    if candidate.startswith("json"):
                        candidate = candidate[4:].strip()
                    if candidate.startswith("[") and candidate.endswith("]"):
                        cleaned_response = candidate
                        break
            
            if not (cleaned_response.startswith("[") and cleaned_response.endswith("]")):
                start_idx = cleaned_response.find("[")
                end_idx = cleaned_response.rfind("]")
                if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                    cleaned_response = cleaned_response[start_idx:end_idx + 1]

            arr = json.loads(cleaned_response)

            if isinstance(arr, list) and arr:
                cleaned = [str(x).strip() for x in arr if str(x).strip()]
                return cleaned[:max_subquestions]
        except Exception:
            pass

    return [
        f"What is the main goal of {topic}?",
        f"What are the important component of {topic}?",
        f"How is {topic} implemented locally?",
        f"What are the major constraints of {topic}?",
    ][:max_subquestions]