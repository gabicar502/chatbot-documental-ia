from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from rag_utils import DocumentChunk, answer_question, load_file, load_repository


st.set_page_config(
    page_title="Chatbot Documental IA",
    page_icon="IA",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');
    :root {
        --bg: #081425;
        --panel: rgba(15, 23, 42, .72);
        --panel-strong: rgba(17, 28, 45, .94);
        --line: rgba(148, 163, 184, .16);
        --text: #d8e3fb;
        --muted: #9aa8bd;
        --gold: #e2c383;
        --blue: #b9c8de;
        --danger: #ffb4ab;
    }
    .stApp {
        background:
            radial-gradient(circle at 18% 0%, rgba(226, 195, 131, .10), transparent 24rem),
            radial-gradient(circle at 86% 14%, rgba(185, 200, 222, .12), transparent 28rem),
            linear-gradient(135deg, #040e1f 0%, #081425 44%, #111c2d 100%);
        color: var(--text);
        font-family: "Inter", sans-serif;
    }
    [data-testid="stSidebar"] {
        background: var(--panel-strong);
        border-right: 1px solid var(--line);
        overflow: hidden !important;
    }
    [data-testid="stSidebar"] * {
        color: var(--text) !important;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-baseweb="base-input"] {
        color: var(--text) !important;
        background: #040e1f !important;
        border-color: rgba(148, 163, 184, .22) !important;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stCaptionContainer {
        color: var(--muted) !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: .55rem;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        margin: .15rem 0 .35rem 0 !important;
        font-size: 1.05rem !important;
        line-height: 1.2 !important;
    }
    [data-testid="stSidebar"] hr {
        margin: .65rem 0 !important;
    }
    [data-testid="stSidebar"] .stRadio,
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stTextInput,
    [data-testid="stSidebar"] .stSlider,
    [data-testid="stSidebar"] .stFileUploader {
        margin-bottom: .2rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] section {
        min-height: 132px !important;
        padding: .75rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] section > div {
        padding: .35rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] small,
    [data-testid="stSidebar"] [data-testid="stFileUploader"] svg {
        display: none !important;
    }
    [data-testid="stSidebar"] button {
        min-height: 2.35rem !important;
        padding-top: .35rem !important;
        padding-bottom: .35rem !important;
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        max-width: 1360px;
    }
    .hero {
        padding: 2.2rem;
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.015)), var(--panel);
        border-radius: 18px;
        margin-bottom: 1.2rem;
        box-shadow: 0 24px 70px rgba(0, 0, 0, .26);
        backdrop-filter: blur(14px);
        position: relative;
        overflow: hidden;
    }
    .hero:after {
        content: "";
        position: absolute;
        width: 360px;
        height: 360px;
        right: -120px;
        top: -160px;
        background: radial-gradient(circle, rgba(226,195,131,.18), transparent 68%);
        pointer-events: none;
    }
    .hero h1 {
        font-size: 2.8rem;
        margin: 0 0 .5rem 0;
        color: #f8fafc;
        font-weight: 800;
        letter-spacing: 0;
    }
    .hero p {
        font-size: 1.05rem;
        color: var(--muted);
        margin: 0;
        max-width: 780px;
    }
    .eyebrow {
        color: var(--gold);
        font-family: "JetBrains Mono", monospace;
        font-size: .72rem;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: .8rem;
    }
    .brand-block {
        border-bottom: 1px solid var(--line);
        margin: .1rem 0 .65rem 0;
        padding-bottom: .55rem;
    }
    .brand-title {
        color: #f8fafc;
        font-size: 1.08rem;
        font-weight: 800;
        margin: 0;
    }
    .brand-subtitle {
        color: var(--gold);
        font-family: "JetBrains Mono", monospace;
        font-size: .66rem;
        letter-spacing: .12em;
        margin-top: .15rem;
    }
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
        margin-bottom: 1.2rem;
    }
    .stat-card {
        padding: 1.1rem;
        border-radius: 16px;
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(255,255,255,.055), rgba(255,255,255,.015)), var(--panel);
        box-shadow: inset 0 0 18px rgba(226,195,131,.025);
    }
    .stat-card .label {
        color: var(--muted);
        font-family: "JetBrains Mono", monospace;
        font-size: .68rem;
        letter-spacing: .08em;
        text-transform: uppercase;
    }
    .stat-card .value {
        color: #f8fafc;
        font-size: 1.85rem;
        font-weight: 800;
        margin-top: .3rem;
    }
    .stat-card .hint {
        color: var(--gold);
        font-size: .78rem;
        margin-top: .35rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid var(--line);
        background: var(--panel);
        box-shadow: 0 18px 45px rgba(0,0,0,.18);
    }
    .metric-card,
    .metric-card * {
        color: var(--text) !important;
    }
    [data-testid="stChatMessage"] {
        background: rgba(15, 23, 42, .70);
        border: 1px solid var(--line);
        border-radius: 14px;
        box-shadow: 0 12px 28px rgba(0, 0, 0, .18);
    }
    [data-testid="stChatMessage"] *,
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] strong {
        color: var(--text) !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #f8fafc !important;
        background: #101827 !important;
        border: 1px solid var(--line) !important;
    }
    .stAlert,
    .stAlert * {
        color: #0f172a !important;
    }
    code {
        color: var(--gold) !important;
        background: #111827 !important;
        border-radius: 6px;
        padding: .12rem .3rem;
    }
    .source-pill {
        display: inline-block;
        padding: .32rem .6rem;
        margin: .15rem;
        border-radius: 999px;
        color: var(--gold);
        background: rgba(226, 195, 131, .10);
        border: 1px solid rgba(226, 195, 131, .25);
        font-size: .82rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: .75rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(15, 23, 42, .66);
        border-radius: 999px;
        padding: .5rem 1rem;
        border: 1px solid var(--line);
        color: var(--text);
    }
    .stTabs [aria-selected="true"] {
        color: var(--gold) !important;
        border-color: rgba(226,195,131,.45) !important;
        background: rgba(226,195,131,.10) !important;
    }
    .doc-table {
        width: 100%;
        border-collapse: collapse;
        overflow: hidden;
        border-radius: 16px;
        border: 1px solid var(--line);
        background: rgba(15, 23, 42, .64);
    }
    .doc-table th {
        color: var(--muted);
        font-family: "JetBrains Mono", monospace;
        font-size: .68rem;
        letter-spacing: .08em;
        text-transform: uppercase;
        padding: .85rem 1rem;
        text-align: left;
        border-bottom: 1px solid var(--line);
    }
    .doc-table td {
        color: var(--text);
        padding: .95rem 1rem;
        border-bottom: 1px solid rgba(148,163,184,.08);
    }
    .status-pill {
        color: var(--gold);
        background: rgba(226, 195, 131, .10);
        border: 1px solid rgba(226, 195, 131, .22);
        padding: .25rem .55rem;
        border-radius: 999px;
        font-size: .75rem;
        font-weight: 700;
    }
    .stButton > button {
        border-radius: 12px;
        font-weight: 800;
        border: 1px solid rgba(226,195,131,.25);
    }
    .stButton > button[kind="primary"] {
        background: var(--blue);
        color: #0d1c2d;
        border: 0;
    }
    [data-testid="stFileUploader"] section {
        background: #040e1f !important;
        border: 1px dashed rgba(226,195,131,.32) !important;
        border-radius: 14px !important;
    }
    [data-testid="stFileUploader"] * {
        color: var(--text) !important;
    }
    h1, h2, h3, h4, p, label, span, div {
        letter-spacing: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    st.session_state.setdefault("chunks", [])
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("source_names", [])


def save_uploaded_files(uploaded_files) -> list[Path]:
    temp_dir = Path(tempfile.mkdtemp(prefix="chatbot_web_"))
    paths = []
    for uploaded_file in uploaded_files:
        path = temp_dir / uploaded_file.name
        path.write_bytes(uploaded_file.getvalue())
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
            st.warning(f"No se cargo el repositorio: {exc}. Los archivos subidos si se procesaron.")

    return chunks, source_names


init_state()

loaded_docs = len(st.session_state.source_names)
loaded_chunks = len(st.session_state.chunks)
active_model = "gemini-2.5-flash"

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Knowledge Base • RAG • Gemini Cloud</div>
        <h1>DocIntelligence</h1>
        <p>Consulta PDFs, Word, archivos de texto y repositorios con una interfaz web en la nube. La app procesa documentos, recupera contexto y responde con IA basada en tus fuentes.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        <div class="brand-block">
            <div class="brand-title">DocIntelligence</div>
            <div class="brand-subtitle">ENTERPRISE DEMO</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.header("Modelo")
    provider = "Gemini gratis"
    st.markdown('<span class="source-pill">Gemini gratis</span>', unsafe_allow_html=True)
    cloud_model = st.selectbox(
        "Modelo Gemini",
        ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"],
        index=0,
    )
    local_model = "llama3.1"
    top_k = 6

    st.divider()
    st.header("Documentos")
    uploaded_files = st.file_uploader(
        "Sube PDF, Word o archivos",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt", "md", "py", "js", "ts", "html", "css", "json", "csv", "sql"],
    )
    repo_path = st.text_input(
        "Carpeta de repo opcional",
        placeholder="Dejalo vacio para PDF o Word",
        help="Este campo es solo para carpetas de codigo. Para PDF o Word usa el boton de subir archivos.",
    )

    if st.button("Procesar documentos", type="primary", use_container_width=True):
        try:
            with st.spinner("Leyendo y preparando la base de conocimiento..."):
                st.session_state.chunks, st.session_state.source_names = build_knowledge_base(uploaded_files, repo_path)
            st.success(f"Listo: {len(st.session_state.chunks)} fragmentos procesados.")
        except Exception as exc:
            st.error(f"No se pudo procesar la informacion: {exc}")

active_model = cloud_model if provider == "Gemini gratis" else local_model
st.markdown(
    f"""
    <div class="stat-grid">
        <div class="stat-card">
            <div class="label">Documentos</div>
            <div class="value">{len(st.session_state.source_names)}</div>
            <div class="hint">Archivos listos para consulta</div>
        </div>
        <div class="stat-card">
            <div class="label">Fragmentos RAG</div>
            <div class="value">{len(st.session_state.chunks)}</div>
            <div class="hint">Contexto indexado en memoria</div>
        </div>
        <div class="stat-card">
            <div class="label">Modelo activo</div>
            <div class="value" style="font-size:1.15rem">{active_model}</div>
            <div class="hint">Proveedor: {provider}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_chat, tab_sources, tab_deploy = st.tabs(["Chat", "Fuentes", "Nube"])

with tab_chat:
    left, right = st.columns([2.3, 1])

    with right:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Fragmentos", len(st.session_state.chunks))
        st.write("Modelo activo")
        st.code(cloud_model if provider == "Gemini gratis" else local_model)
        st.write("Consejo")
        st.caption("Para respuestas buenas, primero sube los documentos y pulsa Procesar documentos.")
        st.markdown("</div>", unsafe_allow_html=True)

    with left:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input("Pregunta algo sobre tus documentos...")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            if not st.session_state.chunks:
                answer = "Primero sube documentos y pulsa **Procesar documentos**."
                sources = []
            else:
                with st.spinner("Buscando contexto y generando respuesta..."):
                    answer, sources = answer_question(
                        question=question,
                        chunks=st.session_state.chunks,
                        provider=provider,
                        cloud_model=cloud_model,
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
        rows = "".join(
            f"""
            <tr>
                <td>{name}</td>
                <td>{sum(1 for chunk in st.session_state.chunks if chunk.source == name)}</td>
                <td><span class="status-pill">Indexed</span></td>
            </tr>
            """
            for name in st.session_state.source_names
        )
        st.markdown(
            f"""
            <table class="doc-table">
                <thead>
                    <tr>
                        <th>Document Name</th>
                        <th>Chunks</th>
                        <th>Vector Status</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Todavia no has procesado documentos.")

    st.subheader("Que hace la app")
    st.write(
        "La aplicacion lee los documentos, los divide en fragmentos, busca los fragmentos relacionados con la pregunta "
        "y se los entrega al modelo para que responda con contexto. Esta tecnica se llama RAG."
    )

with tab_deploy:
    st.subheader("Como montarlo en la nube")
    st.markdown(
        """
        1. Sube estos archivos a un repositorio de GitHub.
        2. Entra a Streamlit Community Cloud y crea una app nueva.
        3. Selecciona el repositorio, la rama y el archivo `app.py`.
        4. En **Advanced settings**, agrega el secreto:

        ```toml
        GEMINI_API_KEY = "tu_api_key"
        ```

        5. Despliega la app y comparte la URL publica.
        """
    )
    st.info("Gemini tiene capa gratuita con limites. Para una exposicion o demo academica suele ser suficiente.")
