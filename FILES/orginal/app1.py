import streamlit as st
import faiss
import numpy as np
import nltk
from pypdf import PdfReader                      
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize

nltk.download("punkt_tab", quiet=True)

# ══════════════════════════════════════════════════════════════════════════════
# 1. TEXT EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def extract_text(file) -> str:
    
    # fitz reads PDFs page by page
    pdf = PdfReader(file)
    text = ""
    for page in pdf.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text



# ══════════════════════════════════════════════════════════════════════════════
# 2. CHUNKING — Sentence-aware chunking (no mid-sentence cuts)
# ══════════════════════════════════════════════════════════════════════════════

def chunk_text(text: str, chunk_size: int = 400) -> list[dict]:
    """
    Split text into sentence-aware chunks.
    - Adds sentences until chunk_size is reached
    - Never cuts mid-sentence
    - If a single sentence exceeds chunk_size, it becomes its own chunk
    """
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(current_chunk) + len(sentence) + 1 <= chunk_size:
            current_chunk += (" " if current_chunk else "") + sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Single sentence > chunk_size → its own chunk (at least 1 sentence rule)
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    # Attach metadata to each chunk
    return [
        {
            "chunk_id": f"chunk_{i}",
            "chunk_index": i,
            "total_chunks": len(chunks),
            "text": chunk,
            "char_count": len(chunk),
        }
        for i, chunk in enumerate(chunks)
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 3. EMBEDDING — HuggingFace all-MiniLM-L6-v2 (free, local)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner="Loading embedding model...")
def load_embedding_model():
    """Load once and cache — no reload on every interaction."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_chunks(chunks: list[dict], model) -> list[dict]:
    """Embed all chunks and add 'embedding' field to each chunk dict."""
    texts = [c["text"] for c in chunks]
    vectors = model.encode(texts, convert_to_numpy=True)   # shape: (n_chunks, 384)

    for i, chunk in enumerate(chunks):
        chunk["embedding"] = vectors[i].tolist()

    return chunks


def embed_query(query: str, model) -> np.ndarray:
    """Embed a single query string — returns float32 numpy array."""
    return model.encode([query], convert_to_numpy=True).astype(np.float32)


# ══════════════════════════════════════════════════════════════════════════════
# 4. INDEXING — FAISS IndexFlatL2
# ══════════════════════════════════════════════════════════════════════════════

def build_index(embedded_chunks: list[dict]) -> faiss.IndexFlatL2:
    """
    Store all chunk embeddings in a FAISS IndexFlatL2.
    IndexFlatL2 = exact brute force search using euclidean distance.
    """
    vectors = np.array(
        [c["embedding"] for c in embedded_chunks], dtype=np.float32
    )
    index = faiss.IndexFlatL2(vectors.shape[1])   # 384 dimensions
    index.add(vectors)
    return index


# ══════════════════════════════════════════════════════════════════════════════
# 5. RETRIEVAL — Embed query → search FAISS → filter by threshold
# ══════════════════════════════════════════════════════════════════════════════

def retrieve(
    query: str,
    model,
    index: faiss.IndexFlatL2,
    chunks: list[dict],
    top_k: int = 3,
    score_threshold: float = 1.2,
) -> list[dict]:
    """
    Embed query, search FAISS, return top-k chunks within score threshold.
    Lower L2 distance = more similar.
    """
    query_vector = embed_query(query, model)
    distances, indices = index.search(query_vector, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        if dist <= score_threshold:
            chunk = chunks[idx].copy()
            chunk["score"] = round(float(dist), 4)
            results.append(chunk)

    return results


# ══════════════════════════════════════════════════════════════════════════════
# 6. GENERATION — Build prompt + call Claude API
# ══════════════════════════════════════════════════════════════════════════════
from google import genai

def build_prompt(query: str, chunks: list[dict]) -> str:
    """Combine retrieved chunks + question into a structured prompt."""
    context = "\n\n".join([
        f"[Chunk {c['chunk_index'] + 1}]\n{c['text']}"
        for c in chunks
    ])

    return (
        "You are a helpful assistant that answers questions based on the provided notes.\n"
        "Use the context below to answer the question as accurately as possible.\n"
        "If the answer is genuinely not present in the notes, say \"I couldn't find this in your notes.\"\n\n"
        f"Notes Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )

def generate_answer(query: str, chunks: list[dict], api_key: str) -> str:
    """Send the prompt to Gemini and return the answer."""
    if not chunks:
        return "I couldn't find anything relevant in your notes for this question."

    prompt = build_prompt(query, chunks)
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text

# ══════════════════════════════════════════════════════════════════════════════
# 7. STREAMLIT UI
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Chat with Notes", page_icon="📝", layout="centered")
st.title("📝 Chat with Notes")
st.caption("Upload your notes and ask questions — answers come only from your notes.")

# ── Session state init ─────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []       # list of {role, content}
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "index" not in st.session_state:
    st.session_state.index = None
if "notes_loaded" not in st.session_state:
    st.session_state.notes_loaded = False

# ── Sidebar — API key + file upload ───────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Setup")

    api_key = st.text_input(
    "Gemini API Key",
    type="password",
    placeholder="AIza..."
    )

    st.divider()

    uploaded_files = st.file_uploader(
        "Upload Notes (TXT or PDF)",
        type=["txt", "pdf"],
        accept_multiple_files=True
    )

    if uploaded_files and api_key:
        if st.button("📥 Process Notes", use_container_width=True):
            with st.spinner("Processing your notes..."):

                # Load embedding model (cached)
                model = load_embedding_model()

                # Extract + chunk + embed all uploaded files
                all_chunks = []
                for file in uploaded_files:
                    raw_text = extract_text(file)
                    if not raw_text.strip():
                        st.warning(f"Could not extract text from {file.name}")
                        continue
                    file_chunks = chunk_text(raw_text, chunk_size=500)
                    all_chunks.extend(file_chunks)

                if all_chunks:
                    embedded = embed_chunks(all_chunks, model)
                    st.session_state.chunks = embedded
                    st.session_state.index = build_index(embedded)
                    st.session_state.notes_loaded = True
                    st.session_state.chat_history = []   # reset chat on new upload
                    st.success(f"✅ {len(all_chunks)} chunks indexed from {len(uploaded_files)} file(s)!")
                else:
                    st.error("No text could be extracted. Please check your files.")

    elif uploaded_files and not api_key:
        st.warning("Please enter your Gemini API key first.")

    if st.session_state.notes_loaded:
        st.divider()
        st.metric("Chunks indexed", len(st.session_state.chunks))
        if st.button("🗑️ Clear & Reset", use_container_width=True):
            st.session_state.chunks = []
            st.session_state.index = None
            st.session_state.notes_loaded = False
            st.session_state.chat_history = []
            st.rerun()

# ── Main area — Chat interface ─────────────────────────────────────────────────
if not st.session_state.notes_loaded:
    st.info("👈 Upload your notes and enter your API key in the sidebar to get started.")

else:
    # Display full chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Query input
    query = st.chat_input("Ask something about your notes...")

    if query:
        # Show user message
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.chat_history.append({"role": "user", "content": query})

        # Retrieve + generate
        with st.chat_message("assistant"):
            with st.spinner("Searching your notes..."):
                model = load_embedding_model()

                retrieved = retrieve(
                    query=query,
                    model=model,
                    index=st.session_state.index,
                    chunks=st.session_state.chunks,
                    top_k=3,
                    score_threshold=1.2,
                )

                answer = generate_answer(query, retrieved, api_key)
                st.markdown(answer)

                # Show sources used (expander so it doesn't clutter the UI)
                if retrieved:
                    with st.expander(f"📄 {len(retrieved)} source chunk(s) used"):
                        for i, chunk in enumerate(retrieved):
                            st.markdown(f"**Chunk {chunk['chunk_index'] + 1}** — score: `{chunk['score']}`")
                            st.caption(chunk["text"])
                            if i < len(retrieved) - 1:
                                st.divider()

        st.session_state.chat_history.append({"role": "assistant", "content": answer})
