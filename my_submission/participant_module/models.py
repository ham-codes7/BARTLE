"""Catalogue models on CPU through transformers only (no sentence-transformers import, to keep
cold-process import time down).

  Embedder  all-MiniLM-L6-v2, mean pooling + L2 normalisation (the model's own pooling)
  Reranker  ms-marco-MiniLM-L6-v2 cross-encoder, one relevance logit per (query, passage)
  NLI       deberta-v3-base-zeroshot-v2.0-c, P(entailment) of (premise, hypothesis)

Models are loaded lazily from the read-only model store (APCTT_MODEL_STORE), offline. Any failure
leaves the model unavailable and the pipeline continues without it.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def _log(message: str) -> None:
    print(f"[models] {message}", file=sys.stderr, flush=True)


class Models:
    def __init__(self, asset_root: Path, threads: int = 4, seed: int = 42) -> None:
        self.spec: dict[str, Any] = {}
        try:
            self.spec = json.loads((Path(asset_root) / "models.json").read_text(encoding="utf-8"))
        except Exception as exc:
            _log(f"no model spec: {type(exc).__name__}")
        self.store = os.environ.get("APCTT_MODEL_STORE", "")
        self.threads = threads
        self.seed = seed
        self._loaded: dict[str, Any] = {}
        self._failed: set[str] = set()
        self.timings: dict[str, float] = {}
        self._torch = None

    # ------------------------------------------------------------------ loading
    def _path(self, name: str) -> Path | None:
        spec = self.spec.get(name)
        if not spec or not self.store:
            return None
        path = Path(self.store) / spec["repo"] / spec["revision"]
        return path if path.is_dir() else None

    def _torch_ready(self):
        if self._torch is None:
            import torch

            torch.set_num_threads(self.threads)
            torch.manual_seed(self.seed)
            self._torch = torch
        return self._torch

    def available(self, name: str) -> bool:
        return name not in self._failed and self._path(name) is not None

    def get(self, name: str):
        """(tokenizer, model) or None."""
        if name in self._loaded:
            return self._loaded[name]
        if name in self._failed:
            return None
        path = self._path(name)
        if path is None:
            self._failed.add(name)
            _log(f"{name}: not in store")
            return None
        start = time.monotonic()
        try:
            torch = self._torch_ready()
            from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True)
            cls = AutoModel if name == "embedder" else AutoModelForSequenceClassification
            model = cls.from_pretrained(str(path), local_files_only=True, dtype=torch.float32)
            model.eval()
            self._loaded[name] = (tokenizer, model)
        except Exception as exc:
            self._failed.add(name)
            _log(f"{name}: load failed {type(exc).__name__}: {exc}")
            return None
        self.timings[f"load_{name}"] = time.monotonic() - start
        return self._loaded[name]

    def max_length(self, name: str) -> int:
        return int(self.spec.get(name, {}).get("max_length", 256))

    # ------------------------------------------------------------------ inference
    def embed(self, texts: list[str], batch_size: int = 64):
        """L2-normalised embeddings as a numpy array (n, d), or None."""
        loaded = self.get("embedder")
        if loaded is None or not texts:
            return None
        import numpy as np

        torch = self._torch_ready()
        tokenizer, model = loaded
        out = []
        with torch.inference_mode():
            for i in range(0, len(texts), batch_size):
                batch = tokenizer(texts[i : i + batch_size], padding=True, truncation=True,
                                  max_length=self.max_length("embedder"), return_tensors="pt")
                hidden = model(**batch).last_hidden_state
                mask = batch["attention_mask"].unsqueeze(-1).float()
                pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
                pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
                out.append(pooled.numpy())
        return np.concatenate(out, axis=0)

    def rerank(self, query: str, passages: list[str], batch_size: int = 64) -> list[float] | None:
        """Relevance logits of (query, passage) pairs, or None."""
        loaded = self.get("reranker")
        if loaded is None or not passages:
            return None
        torch = self._torch_ready()
        tokenizer, model = loaded
        scores: list[float] = []
        with torch.inference_mode():
            for i in range(0, len(passages), batch_size):
                chunk = passages[i : i + batch_size]
                batch = tokenizer([query] * len(chunk), chunk, padding=True, truncation=True,
                                  max_length=self.max_length("reranker"), return_tensors="pt")
                logits = model(**batch).logits
                scores.extend(float(v) for v in logits[:, 0])
        return scores

    def entailment(self, premises: list[str], hypotheses: list[str], batch_size: int = 16) -> list[float] | None:
        """P(entailment) for each (premise, hypothesis) pair, or None."""
        loaded = self.get("nli")
        if loaded is None or not premises:
            return None
        torch = self._torch_ready()
        tokenizer, model = loaded
        label2id = {v.lower(): k for k, v in model.config.id2label.items()}
        entail = label2id.get("entailment", 0)
        out: list[float] = []
        with torch.inference_mode():
            for i in range(0, len(premises), batch_size):
                batch = tokenizer(premises[i : i + batch_size], hypotheses[i : i + batch_size],
                                  padding=True, truncation="only_first",
                                  max_length=self.max_length("nli"), return_tensors="pt")
                probs = torch.softmax(model(**batch).logits, dim=-1)
                out.extend(float(p) for p in probs[:, entail])
        return out
