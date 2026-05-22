# Chatbot documental: nube y local

Este proyecto implementa dos chatbots documentales con interfaz web:

- **Chatbot en la nube:** usa Streamlit Cloud y Gemini API.
- **Chatbot local:** usa Streamlit local y Ollama.

Ambas versiones permiten consultar documentos con RAG. Antes de preguntar se debe cargar y procesar un archivo; el chatbot no se usa como asistente de preguntas libres.

## Archivos principales

```text
app.py               -> chatbot en la nube con Gemini
app_local_ollama.py  -> chatbot local con Ollama
rag_utils.py         -> logica compartida: lectura de documentos, RAG y llamadas a modelos
requirements.txt     -> dependencias del proyecto
README.md            -> documentacion del proyecto
```

## Donde esta el front

El front, es decir la interfaz que ve el usuario, esta en:

```text
app.py
app_local_ollama.py
```

Como el proyecto usa Streamlit, el front no esta separado en HTML, CSS y JavaScript como en React o Angular. En Streamlit, la interfaz se construye directamente desde Python con instrucciones como:

```python
st.set_page_config(...)
st.sidebar
st.file_uploader(...)
st.chat_input(...)
st.chat_message(...)
st.tabs(...)
st.markdown(...)
```

El CSS visual tambien esta dentro de esos archivos, principalmente en bloques:

```python
st.markdown(
    """
    <style>
    ...
    </style>
    """,
    unsafe_allow_html=True,
)
```

Resumen:

```text
Front de la nube  -> app.py
Front local       -> app_local_ollama.py
Backend/logica    -> rag_utils.py
```

## Chatbot en la nube

Archivo:

```text
app.py
```

Usa:

```text
Streamlit Cloud
Gemini API
GEMINI_API_KEY
```

URL publica:

```text
https://chatbot-documental-ia-8yu7sdm8pncnvcvc6jcxrr.streamlit.app
```

Esta version se despliega desde GitHub y permite que cualquier usuario acceda desde navegador sin ejecutar nada en su computador.

## Chatbot local

Archivo:

```text
app_local_ollama.py
```

Usa:

```text
Streamlit local
Ollama
Modelos instalados en el computador
```

Modelos usados/probados:

```text
llama3.2:1b  -> rapido, menor calidad
llama3.1     -> mejor calidad, mas lento
```

Esta version funciona en `localhost` y no envia documentos a la nube.

## Logica compartida

Archivo:

```text
rag_utils.py
```

Este archivo contiene el funcionamiento interno:

- Lectura de PDF.
- Lectura de Word `.docx`.
- Lectura de archivos de texto y codigo.
- Lectura opcional de carpetas/repositorios.
- Division del texto en fragmentos.
- Busqueda de fragmentos relacionados con la pregunta.
- Creacion del prompt.
- Consulta a Gemini.
- Consulta a Ollama.
- Bloqueo de preguntas libres cuando no hay documentos procesados.

## Como funciona RAG

RAG significa Retrieval-Augmented Generation.

Flujo:

1. El usuario carga un documento.
2. El sistema lee el contenido.
3. El texto se divide en fragmentos.
4. El usuario hace una pregunta.
5. El sistema busca los fragmentos mas relacionados.
6. Esos fragmentos se envian al modelo como contexto.
7. El modelo responde usando esa informacion.

Si no hay documentos cargados, el chatbot solicita subir y procesar un archivo. Si la pregunta no se relaciona con el documento, muestra un mensaje para preguntar por el contenido cargado.

## Por que se cambio OpenRouter/free

Primero se hizo una prueba con:

```text
Telegram + n8n + OpenRouter/free
```

La prueba funciono como automatizacion, pero los modelos gratuitos disponibles en OpenRouter generaban respuestas basicas, incoherentes o poco utiles para consulta documental.

Por eso se opto por una nueva version:

```text
Streamlit Cloud + Gemini API
```

Ventajas de la nueva version:

- Mejor interfaz para el usuario.
- URL publica para presentar al docente.
- Mejor calidad de respuesta.
- Carga directa de PDF, Word y archivos.
- Respuestas sobre documentos usando RAG.
- Respuestas restringidas al documento procesado.
- Uso de Secrets para no subir la API key al repositorio.

## Ejecutar chatbot en la nube localmente

Esta version usa Gemini. Sirve para probar en el computador antes de subir a Streamlit Cloud.

```powershell
cd "C:\Users\USER\Desktop\INTELIGENCIA COMPUTACIONAL\Ultima entrega"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GEMINI_API_KEY="tu_api_key"
streamlit run app.py
```

Luego abrir:

```text
http://localhost:8501
```

## Desplegar en Streamlit Community Cloud

1. Subir estos archivos a GitHub:

```text
app.py
rag_utils.py
requirements.txt
README.md
.gitignore
```

2. Entrar a Streamlit Community Cloud.
3. Crear una app desde el repositorio:

```text
gabicar502/chatbot-documental-ia
```

4. Seleccionar:

```text
Branch: main
Main file path: app.py
```

5. En Advanced settings / Secrets agregar:

```toml
GEMINI_API_KEY = "tu_api_key"
```

6. Hacer deploy.

## Ejecutar chatbot local con Ollama

1. Instalar Ollama.
2. Ver modelos instalados:

```powershell
ollama list
```

3. Descargar un modelo si hace falta:

```powershell
ollama pull llama3.2:1b
```

o:

```powershell
ollama pull llama3.1
```

4. Ejecutar la interfaz local:

```powershell
cd "C:\Users\USER\Desktop\INTELIGENCIA COMPUTACIONAL\Ultima entrega"
.\.venv\Scripts\Activate.ps1
streamlit run app_local_ollama.py
```

5. En la app escribir el modelo:

```text
llama3.2:1b
```

o:

```text
llama3.1
```

## Recomendaciones para Ollama

Si `llama3.1` se demora mucho, usar:

```text
llama3.2:1b
```

Si aparece error de timeout, puede ser porque el modelo esta respondiendo lento o porque se dejo abierto `ollama run` en PowerShell. Para salir de `ollama run`:

```text
/bye
```

La app local consulta Ollama por API en:

```text
http://localhost:11434
```

## Funciones implementadas

- Interfaz web para nube.
- Interfaz web para local.
- Lectura de PDF.
- Lectura de Word `.docx`.
- Lectura de archivos de texto y codigo.
- Consulta opcional de repositorios/carpetas.
- RAG para responder con contexto documental.
- Restriccion a preguntas relacionadas con el documento procesado.
- Vista de fuentes consultadas.
- Boton para limpiar documentos.
- Fallback de modelos Gemini cuando hay alta demanda.
- Separacion clara entre version nube y version local.

## Resumen rapido

```text
Nube:
app.py
Streamlit Cloud
Gemini API

Local:
app_local_ollama.py
Streamlit local
Ollama

Compartido:
rag_utils.py
lectura documental + RAG + conexion a modelos
```
