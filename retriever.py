# Import Path from pathlib for working with file-system paths in a clean and platform-independent way.
# Path objects make it easier to navigate folders, check existence, and read files.
from pathlib import Path

# dataclass is used to create simple classes that primarily store data.
# It automatically generates useful methods such as __init__ and __repr__.
from dataclasses import dataclass

# Dict, List, and Tuple are type hints that improve readability and make the code easier to understand and maintain.
# They describe the expected structure of inputs and outputs.
from typing import Dict, List, Tuple

# math is used here for logarithmic scoring in the BM25-style ranking formula.
import math

# re is the regular expression module used for text cleaning, token extraction, and paragraph splitting.
import re


# Import helper functions from a custom utility module.
# read_text_file is expected to read file content as text.
# chunk_text is expected to split a long string into overlapping chunks.
from utils import read_text_file, chunk_text


# Evidence is a lightweight data container that stores a search result.
# It keeps track of the source file, relevance score, and a short matching snippet.
@dataclass
class Evidence:
    file: str
    score: float
    snippet: str


# This regular expression extracts word-like tokens from text.
# It matches sequences of letters and digits, and ignores punctuation.
_WORD_RE = re.compile(r"\b[a-z0-9]+\b", re.IGNORECASE)


# Convert a text string into normalized tokens.
# The function lowercases the input and extracts all word tokens.
# Returning a list of tokens makes scoring and matching easier.
def normalize(text: str) -> List[str]:
    return _WORD_RE.findall((text or "").lower())


# Load all supported documents from a folder.
# Only .txt and .md files are considered searchable documents.
# The function returns a dictionary mapping file paths to their text content.
def load_documents(folder: Path) -> Dict[str, str]:
    docs = {}

    # If the folder does not exist, return an empty document set.
    # This prevents errors when the search folder has not been created yet.
    if not folder.exists():
        return docs

    # Recursively scan the folder and its subfolders.
    # rglob("*") finds every file and directory inside the folder tree.
    for path in folder.rglob("*"):
        # Process only files with .txt or .md extensions.
        if path.is_file() and path.suffix.lower() in {".txt", ".md"}:
            try:
                # Read the file content as text using the helper function.
                text = read_text_file(path)

                # Store only non-empty documents after trimming whitespace.
                if text and text.strip():
                    docs[str(path)] = text
            except Exception:
                # Ignore files that cannot be read.
                # This keeps the indexing process robust even if one file is corrupted or unreadable.
                pass

    return docs


# Split text into smart chunks.
# This function prefers paragraph boundaries first, then falls back to generic chunking if needed.
# chunk_size controls the approximate size of each chunk, and overlap preserves context across chunks.
def smart_chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> List[str]:
    # Remove leading and trailing whitespace.
    text = (text or "").strip()

    # If the input is empty, return no chunks.
    if not text:
        return []

    # Split the text into paragraphs using blank lines as separators.
    # Each paragraph is stripped of surrounding whitespace.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]

    # If paragraph splitting fails to produce useful parts, use the generic chunking helper.
    if not paragraphs:
        return chunk_text(text, chunk_size, overlap)

    chunks = []
    current = ""

    # Build chunks paragraph by paragraph so that sentence and paragraph meaning are preserved.
    for para in paragraphs:
        # If the paragraph still fits inside the current chunk, append it.
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}".strip()
        else:
            # Save the current chunk if it is not empty before starting a new one.
            if current:
                chunks.append(current)
            current = para

    # Add the last chunk if it exists.
    if current:
        chunks.append(current)

    # If only one chunk exists, fall back to generic chunking so overlap logic is handled consistently.
    if len(chunks) <= 1:
        return chunk_text(text, chunk_size, overlap)

    merged = []

    # Rebuild chunks with overlap from the previous chunk tail.
    # Overlap helps preserve context across adjacent chunks during retrieval.
    for i, chunk in enumerate(chunks):
        if i == 0:
            merged.append(chunk)
        else:
            prev_tail = chunks[i - 1][-overlap:] if overlap > 0 else ""
            merged.append((prev_tail + "\n" + chunk).strip())

    return merged


# Convert each document into searchable corpus chunks.
# Every chunk is paired with its originating file path and token list.
def build_corpus_chunks(
    docs: Dict[str, str],
    chunk_size: int = 700,
    overlap: int = 120,
) -> List[Tuple[str, str, List[str]]]:
    corpus = []

    # Process each file and its text content.
    for file, content in docs.items():
        # Split the document into manageable semantic chunks.
        chunks = smart_chunk_text(content, chunk_size=chunk_size, overlap=overlap)

        # Tokenize each chunk and store only chunks that contain useful tokens.
        for chunk in chunks:
            tokens = normalize(chunk)
            if tokens:
                corpus.append((file, chunk, tokens))

    return corpus


# Compute inverse document frequency values for the whole corpus.
# IDF gives higher weight to terms that appear in fewer chunks and lower weight to common terms.
def compute_idf(corpus_tokens: List[List[str]]) -> Dict[str, float]:
    df = {}
    n_docs = len(corpus_tokens)

    # Count in how many chunks each token appears.
    for tokens in corpus_tokens:
        for token in set(tokens):
            df[token] = df.get(token, 0) + 1

    idf = {}

    # Use a BM25-style IDF formula to compute term rarity.
    for token, freq in df.items():
        idf[token] = math.log(1 + (n_docs - freq + 0.5) / (freq + 0.5))

    return idf


# Compute BM25-like relevance score between the query and a document chunk.
# This scoring method rewards matching query words, rare terms, and balanced document length.
def bm25_score(
    query_tokens: List[str],
    doc_tokens: List[str],
    idf: Dict[str, float],
    avgdl: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    # If either side is empty, there is no meaningful score.
    if not query_tokens or not doc_tokens:
        return 0.0

    score = 0.0
    doc_len = len(doc_tokens)
    tf = {}

    # Count term frequency in the document chunk.
    for tok in doc_tokens:
        tf[tok] = tf.get(tok, 0) + 1

    # Score each query token based on its frequency and rarity.
    for tok in query_tokens:
        if tok not in tf:
            continue
        freq = tf[tok]
        tok_idf = idf.get(tok, 0.0)
        denom = freq + k1 * (1 - b + b * (doc_len / avgdl if avgdl > 0 else 1))
        score += tok_idf * ((freq * (k1 + 1)) / denom)

    return score


# Measure how many unique query tokens appear in the document.
# This adds a simple coverage-based signal to the ranking.
def keyword_coverage_score(query_tokens: List[str], doc_tokens: List[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0

    qset = set(query_tokens)
    dset = set(doc_tokens)
    overlap = len(qset & dset)

    # Normalize by the number of unique query terms.
    return overlap / max(len(qset), 1)


# Add bonus points if the full query or key phrases appear in the chunk text.
# This improves ranking for exact or near-exact matches.
def phrase_bonus(query: str, chunk: str) -> float:
    query = (query or "").strip().lower()
    chunk_l = (chunk or "").lower()

    # If either string is empty, no phrase bonus can be applied.
    if not query or not chunk_l:
        return 0.0

    bonus = 0.0

    # Give a strong bonus when the complete query string appears inside the chunk.
    if query in chunk_l:
        bonus += 1.5

    # Also reward matching adjacent word pairs from the query.
    # This helps with partial phrase matching.
    query_words = query.split()
    if len(query_words) >= 2:
        for i in range(len(query_words) - 1):
            phrase = f"{query_words[i]} {query_words[i+1]}"
            if phrase in chunk_l:
                bonus += 0.3

    return bonus


# Combine the base BM25 score with additional ranking adjustments.
# This function improves retrieval quality using coverage, phrase matching, and simple length heuristics.
def rerank_score(query: str, query_tokens: List[str], chunk: str, doc_tokens: List[str], base_score: float) -> float:
    # Compute how much of the query is covered by the chunk.
    coverage = keyword_coverage_score(query_tokens, doc_tokens)

    # Compute exact and phrase-based bonus points.
    bonus = phrase_bonus(query, chunk)

    # Reward chunks whose beginning contains query terms, because they often introduce the topic quickly.
    starts_strong = 0.15 if any(tok in normalize(chunk[:220]) for tok in query_tokens) else 0.0

    # Penalize chunks that are too short or too long, since very small chunks may lack context
    # and very large chunks may dilute relevance.
    length_penalty = 0.0
    if len(chunk) < 120:
        length_penalty -= 0.2
    elif len(chunk) > 1800:
        length_penalty -= 0.15

    # Final score combines all signals.
    return base_score + (coverage * 2.0) + bonus + starts_strong + length_penalty


# Perform local document search over the loaded documents.
# The function ranks chunks using BM25-like scoring and then reranks the top candidates.
# It returns a list of Evidence objects with the best matching snippets.
def local_search(
    query: str,
    docs: Dict[str, str],
    top_k: int = 4,
    candidate_k: int = 10,
    chunk_size: int = 700,
    overlap: int = 120,
    snippet_chars: int = 900,
) -> List[Evidence]:
    # Tokenize the query for matching and scoring.
    query_tokens = normalize(query)

    # If there is no meaningful query or no documents, return no results.
    if not query_tokens or not docs:
        return []

    # Build searchable chunks from the provided documents.
    corpus = build_corpus_chunks(docs, chunk_size=chunk_size, overlap=overlap)
    if not corpus:
        return []

    # Collect token lists from the corpus to compute IDF values.
    corpus_tokens = [tokens for _, _, tokens in corpus]
    idf = compute_idf(corpus_tokens)

    # Compute average document length for BM25 normalization.
    avgdl = sum(len(tokens) for tokens in corpus_tokens) / max(len(corpus_tokens), 1)

    scored = []

    # Score each chunk using BM25.
    for file, chunk, tokens in corpus:
        base = bm25_score(query_tokens, tokens, idf, avgdl)
        if base <= 0:
            continue
        scored.append((file, chunk, tokens, base))

    # If nothing gets a positive score, no relevant evidence is available.
    if not scored:
        return []

    # Sort by base relevance and keep only the best candidate pool.
    scored.sort(key=lambda x: x[3], reverse=True)
    candidates = scored[:max(candidate_k, top_k)]

    reranked = []

    # Apply a second ranking pass using coverage and phrase bonuses.
    for file, chunk, tokens, base in candidates:
        final_score = rerank_score(query, query_tokens, chunk, tokens, base)
        reranked.append(
            Evidence(
                file=file,
                score=final_score,
                snippet=chunk[:snippet_chars].strip()
            )
        )

    # Sort the reranked results from most relevant to least relevant.
    reranked.sort(key=lambda x: x.score, reverse=True)

    deduped: List[Evidence] = []
    seen = set()

    # Remove duplicate or near-duplicate evidence entries.
    # The duplicate key uses the file name and the beginning of the snippet.
    for ev in reranked:
        key = (ev.file, ev.snippet[:200])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ev)

        # Stop once the required number of top results has been collected.
        if len(deduped) >= top_k:
            break

    return deduped