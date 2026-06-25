from dataclasses import dataclass
from pathlib import Path
import os

@dataclass
class Config:
    model_name: str = os.getenv("MODEL_NAME", "llama3.2:1b")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    documents_dir: Path = None
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "output"))
    top_k: int = int(os.getenv("TOP_K", "4"))
    max_subquestions: int = int(os.getenv("MAX_SUBQUESTIONS", "5"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "700"))
    overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))

    def __post_init__(self):
        if self.documents_dir is None:
            env_dir = os.getenv("DOCUMENTS_DIR")
            if env_dir:
                self.documents_dir = Path(env_dir)
            else:
                for name in ["documents", "Documents", "DOCUMENTS"]:
                    p = Path(name)
                    if p.exists() and p.is_dir():
                        self.documents_dir = p
                        break
                if self.documents_dir is None:
                    self.documents_dir = Path("documents")

    