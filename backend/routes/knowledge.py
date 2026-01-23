"""
io-Guard v1.5 - Knowledge Ingestion Router
==========================================

Kullanıcının PDF veya TXT yükleyerek AI'ı eğitmesi için endpoint'ler.

Endpoints:
- POST /v1/knowledge/upload - Dosya yükle ve RAG'a ekle
- GET /v1/knowledge/documents - Yüklenen dokümanları listele
- POST /v1/knowledge/search - RAG içinde arama yap
- DELETE /v1/knowledge/{doc_id} - Doküman sil
- GET /v1/knowledge/stats - Veritabanı istatistikleri
"""

import os
import logging
import uuid
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from pydantic import BaseModel

from auth import get_current_user
from services.memory_core import MemoryCore

logger = logging.getLogger("KnowledgeRouter")

router = APIRouter()

# Desteklenen dosya türleri
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".json"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ==========================================
# 📝 Pydantic Models
# ==========================================

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    content: str
    source: str
    score: float
    metadata: dict


class DocumentInfo(BaseModel):
    id: str
    source: str
    created_at: str
    metadata: dict


class UploadResponse(BaseModel):
    success: bool
    message: str
    doc_id: Optional[str] = None
    chunks_added: int = 0
    mode: Optional[str] = None


# ==========================================
# 📄 Text Extraction Functions
# ==========================================

def extract_text_from_pdf(file_content: bytes) -> str:
    """PDF'den metin çıkar."""
    try:
        from pypdf import PdfReader
        from io import BytesIO
        
        reader = PdfReader(BytesIO(file_content))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"PDF parsing failed: {str(e)}")


def extract_text_from_txt(file_content: bytes) -> str:
    """TXT/MD/JSON dosyasından metin çıkar."""
    try:
        # UTF-8 ile decode et, başarısız olursa latin-1 dene
        try:
            return file_content.decode("utf-8")
        except UnicodeDecodeError:
            return file_content.decode("latin-1")
    except Exception as e:
        logger.error(f"Text extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"Text parsing failed: {str(e)}")


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Metni parçalara böler.
    
    Args:
        text: Bölünecek metin
        chunk_size: Her parçanın karakter uzunluğu
        chunk_overlap: Parçalar arası örtüşme
    
    Returns:
        List[str]: Metin parçaları
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = splitter.split_text(text)
        return chunks
    except ImportError:
        # langchain yoksa basit bir bölme yap
        logger.warning("langchain-text-splitters not found, using simple chunking")
        chunks = []
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        return chunks


# ==========================================
# 🔌 API Endpoints
# ==========================================

@router.post("/upload", response_model=UploadResponse, summary="Dosya Yükle")
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(default=500),
    current_user: dict = Depends(get_current_user)
):
    """
    PDF veya TXT dosyası yükleyerek RAG hafızasına ekler.
    
    - **file**: Yüklenecek dosya (PDF, TXT, MD, JSON)
    - **chunk_size**: Metin parça boyutu (varsayılan: 500 karakter)
    """
    try:
        # Dosya uzantısı kontrolü
        filename = file.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}"
            )
        
        # Dosya boyutu kontrolü
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Max size: {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Metin çıkar
        if ext == ".pdf":
            text = extract_text_from_pdf(content)
        else:
            text = extract_text_from_txt(content)
        
        if not text or len(text.strip()) < 10:
            raise HTTPException(
                status_code=400, 
                detail="Could not extract meaningful text from file"
            )
        
        logger.info(f"Extracted {len(text)} chars from {filename}")
        
        # Metni parçalara böl
        chunks = chunk_text(text, chunk_size=chunk_size)
        logger.info(f"Split into {len(chunks)} chunks")
        
        # Her parçayı RAG'a ekle
        added_count = 0
        doc_ids = []
        
        # Kullanıcı ID'sini al
        user_id = current_user.get("id") or current_user.get("sub", "anonymous")
        
        for i, chunk in enumerate(chunks):
            result = await MemoryCore.add_document(
                text=chunk,
                source=filename,
                user_id=user_id,  # Doküman sahibi
                metadata={
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "original_filename": filename,
                    "file_type": ext
                }
            )
            
            if result.get("success"):
                added_count += 1
                doc_ids.append(result.get("doc_id"))
        
        return UploadResponse(
            success=True,
            message=f"Successfully added {added_count}/{len(chunks)} chunks from '{filename}'",
            doc_id=doc_ids[0] if doc_ids else None,
            chunks_added=added_count,
            mode=MemoryCore.get_mode()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=List[DocumentInfo], summary="Doküman Listesi")
async def list_documents(
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Yüklenmiş tüm dokümanları listeler.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        documents = await MemoryCore.get_all_documents(limit=limit, user_id=user_id)
        
        # DocumentInfo formatına çevir
        result = []
        for doc in documents:
            result.append(DocumentInfo(
                id=doc.get("id", "unknown"),
                source=doc.get("source", "unknown"),
                created_at=doc.get("created_at", "unknown"),
                metadata=doc.get("metadata", {})
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[SearchResult], summary="RAG Arama")
async def search_documents(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    RAG hafızasında arama yapar.
    
    - **query**: Arama sorgusu
    - **top_k**: Maksimum sonuç sayısı (varsayılan: 5)
    """
    try:
        # Kullanıcının kendi dokümanlarında ara
        user_id = current_user.get("id") or current_user.get("sub")
        
        results = await MemoryCore.search(
            query=request.query,
            top_k=request.top_k,
            user_id=user_id  # Sadece bu kullanıcının dokümanları
        )
        
        # SearchResult formatına çevir
        return [
            SearchResult(
                content=r.get("content", ""),
                source=r.get("source", "unknown"),
                score=r.get("score", 0.0),
                metadata=r.get("metadata", {})
            )
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}", summary="Doküman Sil")
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Belirtilen dokümanı siler.
    """
    try:
        result = await MemoryCore.delete_document(doc_id)
        
        if result.get("success"):
            return {"success": True, "message": f"Document '{doc_id}' deleted"}
        else:
            raise HTTPException(
                status_code=400, 
                detail=result.get("error", "Delete failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="RAG İstatistikleri")
async def get_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Vektör veritabanı istatistiklerini döndürür.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        stats = await MemoryCore.get_stats(user_id=user_id)
        return stats
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
