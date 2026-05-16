# Chatbot documental web

Aplicacion web para consultar PDFs, documentos Word, archivos de texto y repositorios usando RAG.

## Modelo recomendado sin cobro

Para evitar respuestas incoherentes de `openrouter/free`, este proyecto usa **Gemini API** con la capa gratuita de Google AI Studio.

Modelo sugerido:

```text
gemini-2.5-flash
```

## Ejecutar local

```powershell
cd "C:\Users\USER\Desktop\INTELIGENCIA COMPUTACIONAL\Ultima entrega"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GEMINI_API_KEY="tu_api_key"
streamlit run app.py
```

## Ejecutar chatbot local con Ollama

```powershell
ollama pull llama3.1
streamlit run app_local_ollama.py
```

Esta versión usa una interfaz web local y consulta Ollama en `http://localhost:11434`.

## Desplegar en Streamlit Community Cloud

1. Sube `app.py`, `rag_utils.py`, `requirements.txt` y `README.md` a GitHub.
2. Entra a Streamlit Community Cloud.
3. Crea una app desde tu repositorio.
4. En `Advanced settings`, agrega:

```toml
GEMINI_API_KEY = "tu_api_key"
```

5. Selecciona `app.py` como archivo principal y despliega.

## Funciones

- Interfaz web.
- Lectura de PDF.
- Lectura de Word `.docx`.
- Lectura de archivos de texto y codigo.
- Consulta de repositorio local.
- Respuestas con fuentes.
- Modelo en nube gratuito con Gemini.
- Opcion local con Ollama para comparar enfoques.
