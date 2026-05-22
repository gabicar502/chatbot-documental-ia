from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from rag_utils import DocumentChunk, answer_question, load_file, load_repository


st.set_page_config(
    page_title="Chatbot Local Ollama",
    page_icon="LOCAL",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@500&display=swap');
    :root {
        --bg: #07111f;
        --panel: rgba(15, 23, 42, .82);
        --line: rgba(148, 163, 184, .18);
        --text: #e5eefc;
        --muted: #9aa8bd;
        --green: #6ee7b7;
        --amber: #f6d58b;
    }
    .stApp {
        background:
            radial-gradient(circle at 18% 4%, rgba(110, 231, 183, .12), transparent 24rem),
            radial-gradient(circle at 86% 10%, rgba(246, 213, 139, .12), transparent 26rem),
            linear-gradient(135deg, #040e1f 0%, #07111f 50%, #101827 100%);
        color: var(--text);
        font-family: "Inter", sans-serif;
    }
    [data-testid="stSidebar"] {
        background: rgba(10, 18, 32, .96);
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] * {
        color: var(--text) !important;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-baseweb="base-input"] {
        background: #030b16 !important;
        color: var(--text) !important;
        border-color: rgba(148, 163, 184, .24) !important;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stCaptionContainer {
        color: var(--muted) !important;
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    .block-container {
        max-width: 1320px;
        padding-top: 1.5rem;
    }
    .hero {
        padding: 2rem;
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.015)), var(--panel);
        border-radius: 18px;
        box-shadow: 0 24px 70px rgba(0, 0, 0, .25);
        margin-bottom: 1rem;
    }
    .hero .eyebrow {
        color: var(--green);
        font-family: "JetBrains Mono", monospace;
        font-size: .72rem;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: .7rem;
    }
    .hero h1 {
        color: #f8fafc;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0 0 .4rem 0;
        letter-spacing: 0;
    }
    .hero p {
        color: var(--muted);
        margin: 0;
        max-width: 820px;
        font-size: 1.02rem;
    }
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
        margin: 1rem 0 1.15rem 0;
    }
    .stat-card, .panel-card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1rem;
    }
    .label {
        color: var(--muted);
        font-family: "JetBrains Mono", monospace;
        font-size: .68rem;
        letter-spacing: .08em;
        text-transform: uppercase;
    }
    .value {
        color: #f8fafc;
        font-size: 1.55rem;
        font-weight: 800;
        margin-top: .25rem;
    }
    .hint {
        color: var(--amber);
        font-size: .82rem;
        margin-top: .25rem;
    }
    [data-testid="stChatMessage"] {
        background: rgba(15, 23, 42, .72);
        border: 1px solid var(--line);
        border-radius: 14px;
    }
    [data-testid="stChatMessage"] * {
        color: var(--text) !important;
    }
    [data-testid="stChatInput"] textarea {
        background: #0b1321 !important;
        color: var(--text) !important;
        border: 1px solid var(--line) !important;
    }
    .source-pill {
        display: inline-block;
        padding: .32rem .65rem;
        margin: .15rem;
        border-radius: 999px;
        color: var(--green);
        background: rgba(110, 231, 183, .10);
        border: 1px solid rgba(110, 231, 183, .25);
        font-size: .82rem;
    }
    [data-testid="stFileUploader"] section {
        background: #030b16 !important;
        border: 1px dashed rgba(110, 231, 183, .32) !important;
        border-radius: 14px !important;
    }
    [data-testid="stFileUploader"] * {
        color: var(--text) !important;
    }
    .stButton > button {
        border-radius: 12px;
        font-weight: 800;
    }
    .stButton > button[kind="primary"] {
        background: var(--green);
        color: #052013;
        border: 0;
    }
    code {
        color: var(--green) !important;
        background: #030b16 !important;
        border-radius: 6px;
        padding: .12rem .3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    st.session_state.setdefault("chunks", [])
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("source_names", [])
    st.session_state.setdefault("uploader_key", 0)


def save_uploaded_files(uploaded_files) -> list[Path]:
    temp_dir = Path(tempfile.mkdtemp(prefix="chatbot_local_"))
    paths: list[Path] = []
    seen_files = set()
    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.getvalue()
        signature = (uploaded_file.name, len(file_bytes))
        if signature in seen_files:
            continue
        seen_files.add(signature)
        path = temp_dir / uploaded_file.name
        path.write_bytes(file_bytes)
        paths.append(path)
    return paths


def build_knowledge_base(uploaded_files, repo_path: str) -> tuple[list[DocumentChunk], list[str]]:
    chunks: list[DocumentChunk] = []
    source_names: list[str] = []
    clean_repo_path = repo_path.strip().strip('"').strip("'")

    for path in save_uploaded_files(uploaded_files):
        loaded = load_file(path)
        chunks.extend(loaded)
        if loaded:
            source_names.append(path.name)

    if clean_repo_path:
        try:
            repo_chunks = load_repository(clean_repo_path)
            chunks.extend(repo_chunks)
            if repo_chunks:
                source_names.append(Path(clean_repo_path).name)
        except ValueError as exc:
            st.warning(f"No se cargó el repositorio: {exc}. Los archivos subidos sí se procesaron.")

    return chunks, source_names


init_state()

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Local AI • Ollama • RAG</div>
        <h1>Chatbot documental local</h1>
        <p>Interfaz web local para consultar documentos con Ollama. Funciona sin enviar tus archivos a la nube y responde usando el contenido que proceses.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<span class="source-pill">Ollama local</span>', unsafe_allow_html=True)
    st.header("Modelo")
    local_model = st.text_input("Modelo Ollama", value="llama3.1")
    st.caption("Debe existir en tu equipo. Ejemplo: `ollama pull llama3.1`.")
    top_k = 6

    st.divider()
    st.header("Documentos")
    uploaded_files = st.file_uploader(
        "Sube PDF, Word o archivos",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt", "md", "py", "js", "ts", "html", "css", "json", "csv", "sql"],
        key=f"uploaded_files_local_{st.session_state.uploader_key}",
    )
    repo_path = st.text_input(
        "Carpeta de repo opcional",
        placeholder="Déjalo vacío para PDF o Word",
        help="Este campo es solo para carpetas de código. Para PDF o Word usa el botón de subir archivos.",
    )

    if st.button("Procesar documentos", type="primary", use_container_width=True):
        with st.spinner("Leyendo documentos..."):
            st.session_state.chunks, st.session_state.source_names = build_knowledge_base(uploaded_files, repo_path)
        st.success(f"Listo: {len(st.session_state.chunks)} fragmentos procesados.")

    if st.button("Limpiar documentos", use_container_width=True):
        st.session_state.chunks = []
        st.session_state.source_names = []
        st.session_state.uploader_key += 1
        st.rerun()

active_model = local_model
st.markdown(
    f"""
    <div class="stat-grid">
        <div class="stat-card">
            <div class="label">Documentos</div>
            <div class="value">{len(st.session_state.source_names)}</div>
            <div class="hint">Archivos cargados</div>
        </div>
        <div class="stat-card">
            <div class="label">Fragmentos RAG</div>
            <div class="value">{len(st.session_state.chunks)}</div>
            <div class="hint">Contexto local</div>
        </div>
        <div class="stat-card">
            <div class="label">Modelo activo</div>
            <div class="value" style="font-size:1.1rem">{active_model}</div>
            <div class="hint">Proveedor: Ollama</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_chat, tab_sources, tab_help = st.tabs(["Chat", "Fuentes", "Ayuda local"])

with tab_chat:
    left, right = st.columns([2.35, 1])

    with right:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.write("Estado")
        st.code("http://localhost:11434")
        st.caption("Si Ollama no está abierto, inicia la aplicación de Ollama o ejecuta `ollama serve`.")
        st.markdown("</div>", unsafe_allow_html=True)

    with left:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input("Pregunta solo sobre el documento procesado...")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.spinner("Consultando Ollama local..."):
                answer, sources = answer_question(
                    question=question,
                    chunks=st.session_state.chunks,
                    provider="Ollama local",
                    cloud_model="",
                    local_model=local_model,
                    top_k=top_k,
                )

            with st.chat_message("assistant"):
                st.markdown(answer)
                if sources:
                    with st.expander("Fuentes consultadas"):
                        for source in sources:
                            st.caption(source.source)
                            st.write(source.text[:520] + ("..." if len(source.text) > 520 else ""))

            st.session_state.messages.append({"role": "assistant", "content": answer})

with tab_sources:
    st.subheader("Documentos cargados")
    if st.session_state.source_names:
        pills = "".join(f'<span class="source-pill">{name}</span>' for name in st.session_state.source_names)
        st.markdown(pills, unsafe_allow_html=True)
    else:
        st.info("Todavía no has procesado documentos.")

with tab_help:
    st.subheader("Cómo ejecutar el chatbot local")
    st.markdown(
        """
        1. Instala Ollama.
        2. Descarga un modelo:

        ```powershell
        ollama pull llama3.1
        ```

        3. Ejecuta esta interfaz:

        ```powershell
        streamlit run app_local_ollama.py
        ```

        4. Carga y procesa documentos antes de preguntar por su contenido.
        """
    )
