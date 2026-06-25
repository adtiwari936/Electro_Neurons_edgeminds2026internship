from config import Config
from retriever import load_documents, local_search
from planner import plan_subquestions
from synthesizer import answer_question
from reporter import compile_report, save_report, save_evidence
from utils import ensure_dir

def run_agent(topic: str) -> str:
    cfg = Config()

    ensure_dir(cfg.output_dir)
    docs = load_documents(cfg.documents_dir)

    subquestions = plan_subquestions(topic, cfg.max_subquestions)

    answers = {}
    evidence_map = {}

    for question in subquestions:
        evidences = local_search(
            question,
            docs,
            top_k=cfg.top_k,
            chunk_size=cfg.chunk_size,
            overlap=cfg.overlap,
        )
        evidence_map[question] = evidences
        answers[question] = answer_question(question, evidences)

    report = compile_report(topic, subquestions, answers)
    save_report(report, cfg.output_dir)
    save_evidence(evidence_map, cfg.output_dir)

    return {
    "topic": topic,
    "subquestions": subquestions,
    "answers": answers,
    "evidence": evidence_map,
    "report": report
}