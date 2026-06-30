# Import List from typing for type annotations.
# This makes it clear that the function expects a list of Evidence objects.
from typing import List

# Import the function that returns the language model client.
# The model is used to turn evidence into a concise final answer.
from ollama_client import get_llm

# Import the Evidence data structure from the retriever module.
# Each Evidence object is expected to contain file, score, and snippet fields.
from retriever import Evidence


# This constant is the fallback message used when the evidence cannot support a reliable answer.
# Keeping the message fixed ensures consistent behavior in unsupported cases.
INSUFFICIENT = "The provided evidence is insufficient to fully answer this question."


# Define the main function that answers a question using only the supplied evidence.
# The goal is to stay grounded in retrieved context and avoid unsupported assumptions.
def answer_question(question: str, evidences: List[Evidence]) -> str:
    # If no evidence objects were provided, the answer cannot be grounded in source material.
    # In that case, return the predefined insufficient-evidence message immediately.
    if not evidences:
        return INSUFFICIENT

    # This list will store formatted evidence snippets that will later be passed into the prompt.
    # Each block keeps track of the file name and the corresponding snippet.
    context_blocks = []

    # Loop through each evidence item and prepare it for the model context.
    # enumerate(..., start=1) gives each evidence a human-readable index starting from 1.
    for i, e in enumerate(evidences, start=1):
        # Extract the snippet safely and remove extra whitespace.
        # Using (e.snippet or "") protects against None values.
        snippet = (e.snippet or "").strip()

        # Only include non-empty snippets in the final context.
        # Empty snippets would add noise and reduce answer quality.
        if snippet:
            context_blocks.append(f"[{i}] File: {e.file}\nSnippet: {snippet}")

    # If all snippets were empty after cleaning, there is still no usable evidence.
    # Return the fallback message rather than asking the model to guess.
    if not context_blocks:
        return INSUFFICIENT

    # Join all evidence blocks into a single context string separated by blank lines.
    # This creates a readable evidence section for the language model.
    context = "\n\n".join(context_blocks)

    # Build the prompt that instructs the model how to answer.
    # The prompt strongly enforces evidence-only answering and discourages speculation.
    prompt = f"""
You are an evidence-grounded research assistant.

Answer the question using only the evidence below.
Do not use outside knowledge.
Do not invent missing details.
If the evidence supports only part of the answer, provide only the supported part.
If the evidence does not support the answer at all, say exactly:
{INSUFFICIENT}

Rules:
- Be concise and direct.
- Use 3 to 5 short bullet points.
- One claim per bullet.
- Prefer wording that is close to the evidence.
- Do not include explanations that are not directly supported.
- Do not force completeness.
- If support is partial, answer with only supported claims and do not speculate.

Question:
{question}

Evidence:
{context}

Output:
- If supported, return 3 to 5 short bullet points.
- If partially supported, return only the supported bullet points.
- If unsupported, return exactly:
{INSUFFICIENT}
""".strip()

    # Get the configured language model instance.
    # If the model is unavailable, the function will safely fall back to the insufficient message.
    llm = get_llm()

    # If a model client is available, try to generate an answer from the prompt.
    if llm is not None:
        try:
            # Send the prompt to the model and extract the text output.
            # strip() removes extra leading/trailing whitespace from the response.
            response = llm.complete(prompt).text.strip()

            # If the model produced any text at all, return it as the final answer.
            # This preserves the model's concise bullet-point output.
            if response:
                return response
        except Exception:
            # If the model call fails for any reason, ignore the error and fall back safely.
            # This prevents the whole program from crashing due to an LLM runtime issue.
            pass

    # If no valid model output was produced, return the default insufficient-evidence response.
    return INSUFFICIENT