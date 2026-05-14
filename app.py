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
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(20, 184, 166, .16), transparent 24rem),
            radial-gradient(circle at bottom right, rgba(249, 115, 22, .10), transparent 26rem),
            linear-gradient(135deg, #f8fafc 0%, #eef7f4 48%, #f7f3ea 100%);
        color: #0f172a;
    }
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, .88);
        border-right: 1px solid rgba(15, 23, 42, .10);
    }
    [data-testid="stSidebar"] * {
        color: #0f172a !important;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-baseweb="base-input"] {
        color: #f8fafc !important;
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1220px;
    }
    .hero {
        padding: 2rem;
        border: 1px solid rgba(15, 23, 42, .10);
        background: rgba(255, 255, 255, .82);
        border-radius: 18px;
        margin-bottom: 1.25rem;
        box-shadow: 0 18px 45px rgba(15, 23, 42, .08);
    }
    .hero h1 {
        font-size: 2.5rem;
        margin: 0 0 .5rem 0;
        color: #0f172a;
    }
    .hero p {
        font-size: 1.05rem;
        color: #475569;
        margin: 0;
        max-width: 780px;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid rgba(15, 23, 42, .10);
        background: rgba(255, 255, 255, .86);
        box-shadow: 0 14px 34px rgba(15, 23, 42, .07);
    }
    .metric-card,
    .metric-card * {
        color: #0f172a !important;
    }
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, .90);
        border: 1px solid rgba(15, 23, 42, .10);
        border-radius: 14px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, .06);
    }
    [data-testid="stChatMessage"] *,
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] strong {
        color: #0f172a !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #f8fafc !important;
    }
    .stAlert,
    .stAlert * {
        color: #0f172a !important;
    }
    code {
        color: #10b981 !important;
        background: #111827 !important;
        border-radius: 6px;
        padding: .12rem .3rem;
    }
    .source-pill {
        display: inline-block;
        padding: .32rem .6rem;
        margin: .15rem;
        border-radius: 999px;
        color: #155e75;
        background: rgba(103, 232, 249, .25);
        border: 1px solid rgba(8, 145, 178, .20);
        font-size: .82rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: .75rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, .82);
        border-radius: 999px;
        padding: .5rem 1rem;
        border: 1px solid rgba(15, 23, 42, .10);
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

st.markdown(
    """
    <div class="hero">
        <h1>Chatbot documental en la nube</h1>
        <p>Consulta PDFs, Word, archivos de texto y repositorios. La app usa busqueda por contexto y un modelo en la nube para responder con base en tus documentos.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Modelo")
    provider = st.radio("Proveedor", ["Gemini gratis", "Ollama local"])
    cloud_model = st.selectbox(
        "Modelo Gemini",
        ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"],
        index=0,
    )
    local_model = st.text_input("Modelo Ollama", value="llama3.1")
    top_k = st.slider("Contexto usado", min_value=3, max_value=10, value=6)

    st.divider()
    st.header("Documentos")
    uploaded_files = st.file_uploader(
        "Sube PDF, Word o archivos",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt", "md", "py", "js", "ts", "html", "css", "json", "csv", "sql"],
    )
    repo_path = st.text_input(
        "Repositorio local opcional",
        placeholder="Dejalo vacio si solo vas a subir PDF o Word",
        help="Este campo es solo para carpetas de codigo. Para PDF o Word usa el boton de subir archivos.",
    )

    if st.button("Procesar documentos", type="primary", use_container_width=True):
        try:
            with st.spinner("Leyendo y preparando la base de conocimiento..."):
                st.session_state.chunks, st.session_state.source_names = build_knowledge_base(uploaded_files, repo_path)
            st.success(f"Listo: {len(st.session_state.chunks)} fragmentos procesados.")
        except Exception as exc:
            st.error(f"No se pudo procesar la informacion: {exc}")

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
