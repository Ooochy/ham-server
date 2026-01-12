from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


SERVER_DIR = Path(__file__).resolve().parent
DATA_DIR = SERVER_DIR / "data"
PDF_DIR = SERVER_DIR / "pdfs"


@dataclass(frozen=True)
class BankSpec:
    id: str
    label: str
    json_file: Optional[str]
    pdf_file: str


BANK_SPECS: List[BankSpec] = [
    BankSpec(id="a", label="A类题库", json_file="A类题库.json", pdf_file="A类题库.pdf"),
    BankSpec(id="b", label="B类题库", json_file="B类题库.json", pdf_file="B类题库.pdf"),
    BankSpec(id="c", label="C类题库", json_file="C类题库.json", pdf_file="C类题库.pdf"),
    BankSpec(id="all", label="总题库", json_file="总题库.json", pdf_file="总题库.pdf"),
    BankSpec(id="all_img", label="总题库附图标记", json_file=None, pdf_file="总题库附图标记.pdf"),
]
BANK_BY_ID: Dict[str, BankSpec] = {b.id: b for b in BANK_SPECS}


def _load_bank_json(bank_id: str) -> Dict[str, Any]:
    spec = BANK_BY_ID.get(bank_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Unknown bank")
    if not spec.json_file:
        raise HTTPException(status_code=404, detail="This bank has no questions")

    path = DATA_DIR / spec.json_file
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"Missing data file: {spec.json_file}")

    return json.loads(path.read_text(encoding="utf-8"))


def _bank_question_count(spec: BankSpec) -> int:
    if not spec.json_file:
        return 0
    path = DATA_DIR / spec.json_file
    if not path.exists():
        return 0
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return int(obj.get("count") or len(obj.get("questions") or []))
    except Exception:
        return 0


def _parse_origins() -> List[str]:
    # Default to the deployed frontends; values must match the browser's origin exactly.
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://cuihongyu.com,http://cuihongyu.com:8080,http://39.106.43.84,http://39.106.43.84:8080,https://cuihongyu.com,https://cuihongyu.com:8080",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


def _parse_origin_regex() -> Optional[str]:
    # Regex fallback covers both :80 and :8080 for 39.106.43.84; override via CORS_ORIGIN_REGEX.
    env_val = os.getenv("CORS_ORIGIN_REGEX")
    if env_val:
        try:
            re.compile(env_val)
            return env_val
        except re.error:
            pass
    return r"^https?://39\.106\.43\.84(?::8080)?$"


app = FastAPI(title="HAM Question Bank API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_origins(),
    allow_origin_regex=_parse_origin_regex(),
    allow_credentials=False,
    # Allow OPTIONS for browser preflight and keep GET for the API itself.
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/banks")
def list_banks() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for spec in BANK_SPECS:
        out.append(
            {
                "id": spec.id,
                "label": spec.label,
                "hasQuestions": bool(spec.json_file),
                "questionCount": _bank_question_count(spec),
                "pdfUrl": f"/api/pdfs/{spec.id}",
            }
        )
    return out


@app.get("/api/banks/{bank_id}")
def get_bank(bank_id: str) -> Dict[str, Any]:
    return _load_bank_json(bank_id)


@app.get("/api/pdfs/{bank_id}")
def get_pdf(bank_id: str) -> FileResponse:
    spec = BANK_BY_ID.get(bank_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Unknown bank")

    pdf_path = PDF_DIR / spec.pdf_file
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    # Do NOT set Content-Disposition with non-ASCII filenames here.
    # Some servers/frameworks will fail to encode such headers (causing 500),
    # and browsers can still render PDFs inline based on Content-Type.
    return FileResponse(path=str(pdf_path), media_type="application/pdf")
