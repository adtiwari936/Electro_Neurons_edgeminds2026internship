# EDGE MINDS HACKATHON 2026

#### Team Name : Electro_Neurons

#### Team ID : EDGM26-DWDPMR

#### Team Lead : Aditya Tiwari

#### Team Members : Shubhankar, Anshuman Shukla, Dheeraj Yadav

## Problem Statement :

Build an AI agent where the SLM is the brain - planning steps, calling tools, evaluating
results, and self-correcting. Minimum 3 custom tools and multi-step execution. Apply to
research assistants, data analysis, DevOps monitoring, or personal productivity

## Solution / Project Proposal :

**Abstract & Problem**

Edge devices need low‑latency, offline monitoring, but current solutions are either fragile rule‑based scripts or cloud‑dependent agents with latency and privacy issues. We build a fully on‑device agent that runs within a 1.2B‑parameter budget using a lightweight SLM like Llama‑3.2‑1B via Ollama.

**Solution Overview**

Brain: Local ≈1B SLM (Llama‑3.2‑1B) running through Ollama, optimized for edge hardware (4–8 GB RAM).

Agent Loop: Minimal Python ReAct loop (reason → tool call → observation → next step) with simple regex parsing, no heavy frameworks.

Custom Tools (local, easy to implement):

get_system_status() – CPU, RAM, disk, thermals via shell commands.

scan_local_directory(path) – detect missing configs, large files, log bloat.

save_edge_log(payload) – append structured diagnostics to a local log file.

**Self‑Correction**

If a tool call fails, the Python layer captures the error and feeds it back to the SLM as an Observation. The model then adjusts its plan (e.g., fixes arguments, tries fallback paths) and issues a corrected tool call. This creates an offline, self‑healing edge agent that is simple to implement yet showcases real multi‑step, tool‑using, and self‑correcting behavior within a strict 1.2B parameter budget.
