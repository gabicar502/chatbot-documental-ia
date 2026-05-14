from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import requests
import streamlit as st
from docx import Document
from google import genai
from pypdf import PdfReader

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".html",
    ".css",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".csv",
    ".sql",
}

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".idea",
    ".vscode",
    "dist",
    "build",
}


@dataclass
class DocumentChunk:
    source: str
    text: str


def get_secret(name: str) -> str | None:
    try:
        return st.secrets.get(name) or os.getenv(name)
    except Exception:
        return os.getenv(name)


def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[Pagina {index}]\n{text}")
    return "\n\n".join(pages)


def read_docx(path: Path) -> str:
    document = Document(str(path))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="ignore")


def iter_repository_files(repo_path: Path) -> Iterable[Path]:
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_EXTENSIONS or path.suffix.lower() in {".pdf", ".docx"}:
            yield path


def chunk_text(text: str, source: str, chunk_size: int = 1300, overlap: int = 180) -> list[DocumentChunk]:
    clean = " ".join(text.split())
    if not clean:
        return []

    chunks: list[DocumentChunk] = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunks.append(DocumentChunk(source=source, text=clean[start:end]))
        if end == len(clean):
            break
        start = max(end - overlap, start + 1)
    return chunks


def load_file(path: Path) -> list[DocumentChunk]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = read_pdf(path)
    elif suffix == ".docx":
        text = read_docx(path)
    elif suffix in TEXT_EXTENSIONS:
        text = read_text_file(path)
    else:
        return []
    return chunk_text(text, path.name)


def load_repository(repo_path: str) -> list[DocumentChunk]:
    root = Path(repo_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("La ruta del repositorio no existe o no es una carpeta.")

    chunks: list[DocumentChunk] = []
    for path in iter_repository_files(root):
        try:
            relative = path.relative_to(root)
            loaded = load_file(path)
            chunks.extend(DocumentChunk(source=f"{root.name}/{relative}", text=chunk.text) for chunk in loaded)
        except Exception:
            continue
    return chunks


def normalize_terms(text: str) -> list[str]:
    return [term for term in re.findall(r"\w+", text.lower()) if len(term) > 2]


def keyword_score(query: str, chunk: DocumentChunk) -> float:
    query_terms = set(normalize_terms(query))
    chunk_terms = normalize_terms(chunk.text)
    if not query_terms or not chunk_terms:
        return 0

    chunk_set = set(chunk_terms)
    overlap = len(query_terms & chunk_set)
    density = sum(chunk_terms.count(term) for term in query_terms) / len(chunk_terms)
    return overlap * 2 + density


def retrieve_context(query: str, chunks: Sequence[DocumentChunk], top_k: int = 6) -> list[DocumentChunk]:
    scored = sorted(((keyword_score(query, chunk), chunk) for chunk in chunks), key=lambda item: item[0], reverse=True)
    relevant = [chunk for score, chunk in scored if score > 0]
    return relevant[:top_k] or [chunk for _, chunk in scored[:top_k]]


def has_document_match(query: str, chunks: Sequence[DocumentChunk]) -> bool:
    if not chunks:
        return False
    best_score = max(keyword_score(query, chunk) for chunk in chunks)
    return best_score >= 2


def build_prompt(question: str, context_chunks: Sequence[DocumentChunk]) -> str:
    context = "\n\n".join(f"Fuente: {chunk.source}\nContenido: {chunk.text}" for chunk in context_chunks)
    return f"""
Eres un chatbot academico especializado en responder preguntas sobre documentos.
Responde siempre en espanol, con claridad y precision.
Usa unicamente la informacion del contexto.
Si la respuesta no aparece en el contexto, responde: "No encuentro esa informacion en los documentos cargados".
No inventes datos. Cita la fuente usada al final de cada respuesta.

Contexto:
{context}

Pregunta del usuario:
{question}
""".strip()


def build_general_prompt(question: str) -> str:
    return f"""
Eres un chatbot academico y conversacional.
Responde en espanol natural, claro y util.
Puedes responder preguntas generales, explicar conceptos, ayudar a redactar, resumir ideas y orientar al usuario.
Si el usuario pregunta por documentos cargados y no recibes contexto, indica que debe cargar o procesar el documento.
No inventes que viste documentos si no se te entrego contexto.

Pregunta del usuario:
{question}
""".strip()


def get_gemini_client() -> genai.Client | None:
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def gemini_model_candidates(model: str) -> list[str]:
    fallback_models = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]
    return [model] + [fallback for fallback in fallback_models if fallback != model]


def generate_with_gemini(prompt: str, model: str) -> str:
    client = get_gemini_client()
    if client is None:
        return "Falta configurar GEMINI_API_KEY. Puedes crear una gratis en Google AI Studio y ponerla en Streamlit Secrets."

    errors: list[str] = []
    for candidate in gemini_model_candidates(model):
        try:
            response = client.models.generate_content(model=candidate, contents=prompt)
            text = response.text or "El modelo no devolvio texto."
            if candidate != model:
                return f"Nota: el modelo principal estaba ocupado, respondi con `{candidate}`.\n\n{text}"
            return text
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")
            if "503" not in str(exc) and "UNAVAILABLE" not in str(exc):
                break

    return (
        "No pude consultar Gemini en este momento. El servicio puede estar saturado o la API key puede tener limites. "
        "Intenta de nuevo en unos minutos.\n\nDetalle tecnico: "
        + " | ".join(errors)
    )


def answer_general_with_gemini(question: str, model: str) -> str:
    return generate_with_gemini(build_general_prompt(question), model)


def answer_with_gemini(question: str, context_chunks: Sequence[DocumentChunk], model: str) -> str:
    return generate_with_gemini(build_prompt(question, context_chunks), model)


def answer_with_ollama(question: str, context_chunks: Sequence[DocumentChunk], model: str) -> str:
    payload = {
        "model": model,
        "prompt": build_prompt(question, context_chunks),
        "stream": False,
        "options": {"temperature": 0.2},
    }
    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.RequestException as exc:
        return f"No pude conectar con Ollama. Verifica que este abierto y que el modelo `{model}` exista. Detalle: {exc}"


def answer_question(
    question: str,
    chunks: Sequence[DocumentChunk],
    provider: str,
    cloud_model: str,
    local_model: str,
    top_k: int,
) -> tuple[str, list[DocumentChunk]]:
    if provider == "Gemini gratis" and not chunks:
        return answer_general_with_gemini(question, cloud_model), []

    if provider == "Gemini gratis" and not has_document_match(question, chunks):
        return answer_general_with_gemini(question, cloud_model), []

    context_chunks = retrieve_context(question, chunks, top_k=top_k)
    if provider == "Gemini gratis":
        return answer_with_gemini(question, context_chunks, cloud_model), context_chunks
    return answer_with_ollama(question, context_chunks, local_model), context_chunks
