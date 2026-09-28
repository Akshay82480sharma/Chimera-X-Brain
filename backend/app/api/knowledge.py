"""Knowledge API — Minimal RAG implementation (Phase 2)."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Document, DocumentChunk, Project
import litellm
import json
import math

def cosine_similarity(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

async def generate_embedding(text: str, db: AsyncSession) -> list[float]:
    """Dynamically find a local embedding model and generate embeddings."""
    from app.db.models import Provider, AIModel
    
    # Find local provider
    result = await db.execute(select(Provider).where(Provider.type == "local", Provider.is_active == True))
    local_p = result.scalars().first()
    
    if not local_p:
        raise Exception("No active local provider found for embeddings.")
        
    # Find a local embedding model
    result = await db.execute(select(AIModel).where(AIModel.provider_id == local_p.id, AIModel.is_active == True))
    lms = result.scalars().all()
    
    embed_model = None
    for m in lms:
        if "embed" in m.model_name.lower():
            embed_model = m
            break
            
    if not embed_model:
        raise Exception("No local embedding model found (name must contain 'embed').")
        
    provider_prefix = "openai/" if local_p.slug in ["lm-studio", "ollama"] else f"{local_p.slug}/"
    litellm_model = f"{provider_prefix}{embed_model.model_name}"
    
    try:
        res = await litellm.aembedding(
            model=litellm_model, 
            input=text, 
            api_base=local_p.base_url, 
            api_key="dummy-key"
        )
        return res.data[0]["embedding"]
    except Exception as e:
        print(f"Local embedding failed: {e}")
        raise Exception(f"Local embedding failed: {e}")

router = APIRouter(prefix="/v1/knowledge", tags=["Knowledge"])


def simple_chunker(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """Naive sliding window chunker."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


@router.post("/upload")
async def upload_document(
    project_id: int = 1,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload a TXT file, extract text, chunk it, and save."""
    # Ensure project exists, auto-create if not
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        project = Project(id=project_id, name="Default Project")
        db.add(project)
        await db.flush()

    content = await file.read()
    
    # For now, only handle raw text
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Only UTF-8 text files are supported in this version.")

    # Save Document
    doc = Document(
        project_id=project_id,
        filename=file.filename or "uploaded_file.txt",
        content=text
    )
    db.add(doc)
    await db.flush()  # Get doc.id

    # Chunk and save chunks
    chunks_text = simple_chunker(text)
    for text_chunk in chunks_text:
        # Generate embedding
        embedding_data = None
        try:
            embedding_data = await generate_embedding(text_chunk, db)
        except Exception as e:
            print(f"Embedding failed for chunk: {e}")
            
        chunk_model = DocumentChunk(
            document_id=doc.id,
            content=text_chunk,
            embedding=embedding_data
        )
        db.add(chunk_model)

    await db.commit()
    
    return {
        "status": "success",
        "document_id": doc.id,
        "chunks_extracted": len(chunks_text)
    }


@router.get("/documents")
async def list_documents(project_id: int = None, db: AsyncSession = Depends(get_db)):
    """List documents, optionally filtered by project."""
    query = select(Document)
    if project_id:
        query = query.where(Document.project_id == project_id)
        
    result = await db.execute(query)
    docs = result.scalars().all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "project_id": doc.project_id,
            "created_at": doc.created_at
        }
        for doc in docs
    ]


async def retrieve_relevant_chunks(query: str, project_id: int, top_k: int, db: AsyncSession):
    try:
        query_embedding = await generate_embedding(query, db)
    except Exception as e:
        print(f"Failed to embed query: {e}")
        return []
        
    # Fetch all chunks for the project
    result = await db.execute(
        select(DocumentChunk)
        .join(Document)
        .where(Document.project_id == project_id)
    )
    chunks = result.scalars().all()
    
    # Calculate similarities
    scored_chunks = []
    for chunk in chunks:
        if chunk.embedding:
            # Ensure it's a list (SQLite JSON might return lists or strings)
            emb = json.loads(chunk.embedding) if isinstance(chunk.embedding, str) else chunk.embedding
            score = cosine_similarity(query_embedding, emb)
            scored_chunks.append((score, chunk.content))
            
    # Sort by score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    return [content for score, content in scored_chunks[:top_k] if score > 0.3]

@router.post("/search")
async def search_knowledge(
    query: str,
    project_id: int = 1,
    top_k: int = 3,
    db: AsyncSession = Depends(get_db)
):
    """Search for relevant chunks using vector embeddings."""
    results = await retrieve_relevant_chunks(query, project_id, top_k, db)
    return {"results": results}
