# pyrefly: ignore [missing-import]
from flask import Flask, render_template, request, Response, jsonify
from pathlib import Path
import os
import json
from config import Config
from retriever import load_documents, local_search
from planner import plan_subquestions
from synthesizer import answer_question
from reporter import compile_report, save_report, save_evidence
from utils import ensure_dir

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/research/stream')
def research_stream():
    topic = request.args.get('topic', '').strip()
    if not topic:
        def err_gen():
            yield f"data: {json.dumps({'status': 'error', 'message': 'Topic cannot be empty'})}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    cfg = Config()
    
    # Allow overriding configurations via query params
    if request.args.get('max_subquestions'):
        try:
            cfg.max_subquestions = int(request.args.get('max_subquestions'))
        except ValueError:
            pass
    if request.args.get('top_k'):
        try:
            cfg.top_k = int(request.args.get('top_k'))
        except ValueError:
            pass

    def event_generator():
        try:
            ensure_dir(cfg.output_dir)

            yield f"data: {json.dumps({'status': 'loading_docs', 'message': f'Scanning directory \"{cfg.documents_dir.name}\" for local documents...'})}\n\n"
            docs = load_documents(cfg.documents_dir)
            yield f"data: {json.dumps({'status': 'loaded_docs', 'message': f'Loaded {len(docs)} documents successfully.'})}\n\n"

            yield f"data: {json.dumps({'status': 'planning', 'message': 'Decomposing topic into sub-questions...'})}\n\n"
            subquestions = plan_subquestions(topic, cfg.max_subquestions)
            yield f"data: {json.dumps({'status': 'planned', 'subquestions': subquestions})}\n\n"

            answers = {}
            evidence_map = {}

            for idx, question in enumerate(subquestions):
                yield f"data: {json.dumps({'status': 'searching', 'index': idx, 'question': question, 'message': f'Retrieving relevant snippets for Q{idx+1}: \"{question}\"...'})}\n\n"
                evidences = local_search(
                    question,
                    docs,
                    top_k=cfg.top_k,
                    chunk_size=cfg.chunk_size,
                    overlap=cfg.overlap,
                )
                evidence_map[question] = evidences

                yield f"data: {json.dumps({'status': 'synthesizing', 'index': idx, 'question': question, 'message': f'Synthesizing evidence-based answer for Q{idx+1}...'})}\n\n"
                answer = answer_question(question, evidences)
                answers[question] = answer

                yield f"data: {json.dumps({
                    'status': 'answered',
                    'index': idx,
                    'question': question,
                    'answer': answer,
                    'evidence': [e.__dict__ for e in evidences]
                })}\n\n"

            yield f"data: {json.dumps({'status': 'compiling', 'message': 'Formatting final research report and saving outputs...'})}\n\n"
            report = compile_report(topic, subquestions, answers)
            save_report(report, cfg.output_dir)
            save_evidence(evidence_map, cfg.output_dir)

            yield f"data: {json.dumps({
                'status': 'done',
                'report': report,
                'evidence': {q: [e.__dict__ for e in evs] for q, evs in evidence_map.items()}
            })}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': f'An error occurred: {str(e)}'})}\n\n"

    return Response(event_generator(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
