"""
io-Guard v1.5 - Memory Core (Hibrit RAG Hafızası)
================================================

Sistemin uzun süreli hafızası. Vektör veritabanı kullanarak dokümanları saklar ve arar.

MODE DETECTION:
- SUPABASE_URL varsa → Supabase pgvector (Cloud)
- SUPABASE_URL yoksa → ChromaDB (Local, Docker gerektirmez)

Embedding: sentence-transformers (all-MiniLM-L6-v2) - Ücretsiz, OpenAI gerektirmez
"""

import os
import logging
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger("MemoryCore")

# Lazy imports - yükleme süresini azaltır
_embedder = None
_chroma_client = None
_chroma_collection = None


def _get_embedder():
    """Lazy load sentence-transformers model."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        _embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedder


def _get_chroma_collection():
    """Lazy load ChromaDB collection."""
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        import chromadb
        from chromadb.config import Settings
        
        # ChromaDB verileri backend/chroma_db/ klasöründe saklanır
        persist_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
        os.makedirs(persist_dir, exist_ok=True)
        
        logger.info(f"Initializing ChromaDB at: {persist_dir}")
        _chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        _chroma_collection = _chroma_client.get_or_create_collection(
            name="io_guard_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
    return _chroma_collection


def _is_cloud_mode() -> bool:
    """Check if Supabase is configured (Cloud mode)."""
    supabase_url = os.getenv("SUPABASE_URL", "")
    # Eğer SUPABASE_URL varsa ve boş değilse cloud modunda çalış
    return bool(supabase_url and supabase_url.strip() and "supabase" in supabase_url.lower())


class MemoryCore:
    """
    Hybrid RAG Memory System.
    
    Otomatik olarak LOCAL (ChromaDB) veya CLOUD (Supabase) modunu seçer.
    """
    
    @staticmethod
    def get_mode() -> str:
        """Return current mode: LOCAL or CLOUD."""
        return "CLOUD" if _is_cloud_mode() else "LOCAL"
    
    @staticmethod
    async def add_document(
        text: str, 
        source: str, 
        user_id: str = None,  # v1.5: Kullanıcı bazlı doküman
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Dokümanı vektör veritabanına ekler.
        
        Args:
            text: Doküman içeriği
            source: Kaynak dosya adı veya URL
            user_id: Doküman sahibi kullanıcı ID'si
            metadata: Ekstra bilgiler (opsiyonel)
        
        Returns:
            {"success": bool, "doc_id": str, "chunks_added": int}
        """
        try:
            if not text or not text.strip():
                return {"success": False, "error": "Empty text"}
            
            # Unique doc_id oluştur
            doc_id = hashlib.md5(f"{source}:{text[:100]}".encode()).hexdigest()[:12]
            
            # Metadata hazırla
            doc_metadata = {
                "source": source,
                "user_id": user_id or "anonymous",
                "created_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            if _is_cloud_mode():
                return await MemoryCore._add_document_cloud(doc_id, text, user_id, doc_metadata)
            else:
                return await MemoryCore._add_document_local(doc_id, text, doc_metadata)
                
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def _add_document_local(doc_id: str, text: str, metadata: dict) -> dict:
        """ChromaDB'ye doküman ekle."""
        try:
            collection = _get_chroma_collection()
            embedder = _get_embedder()
            
            # Embedding oluştur
            embedding = embedder.encode(text).tolist()
            
            # ChromaDB'ye ekle
            collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            
            logger.info(f"Document added to ChromaDB: {doc_id} ({len(text)} chars)")
            return {"success": True, "doc_id": doc_id, "chunks_added": 1, "mode": "LOCAL"}
            
        except Exception as e:
            logger.error(f"ChromaDB add error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def _add_document_cloud(doc_id: str, text: str, user_id: str, metadata: dict) -> dict:
        """Supabase pgvector'a doküman ekle."""
        try:
            from supabase import create_client
            from dotenv import load_dotenv
            load_dotenv()
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Supabase credentials missing")
            
            client = create_client(supabase_url, supabase_key)
            embedder = _get_embedder()
            
            # Embedding oluştur
            embedding = embedder.encode(text).tolist()
            
            # Supabase'e ekle (user_id ile)
            result = client.table("documents").insert({
                "id": doc_id,
                "user_id": user_id,  # Kullanıcı sahipliği
                "content": text,
                "embedding": embedding,
                "metadata": metadata,
                "source": metadata.get("source", "unknown")
            }).execute()
            
            logger.info(f"Document added to Supabase: {doc_id} (user: {user_id})")
            return {"success": True, "doc_id": doc_id, "chunks_added": 1, "mode": "CLOUD"}
            
        except Exception as e:
            logger.error(f"Supabase add error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def search(query: str, top_k: int = 5, user_id: str = None) -> List[Dict[str, Any]]:
        """
        RAG araması yapar.
        
        Args:
            query: Arama sorgusu
            top_k: Döndürülecek maksimum sonuç sayısı
            user_id: Sadece bu kullanıcının dokümanlarında ara (opsiyonel)
        
        Returns:
            List[{"content": str, "source": str, "score": float, "metadata": dict}]
        """
        try:
            if not query or not query.strip():
                return []
            
            if _is_cloud_mode():
                return await MemoryCore._search_cloud(query, top_k, user_id)
            else:
                return await MemoryCore._search_local(query, top_k, user_id)
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    @staticmethod
    async def _search_local(query: str, top_k: int, user_id: str = None) -> List[dict]:
        """ChromaDB'de arama yap."""
        try:
            collection = _get_chroma_collection()
            embedder = _get_embedder()
            
            # Query embedding
            query_embedding = embedder.encode(query).tolist()
            
            # ChromaDB arama (user_id filtresi ile)
            where_filter = {"user_id": user_id} if user_id else None
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # Sonuçları formatla
            formatted = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    distance = results["distances"][0][i] if results.get("distances") else 0
                    score = 1 - distance  # Cosine similarity
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                    
                    formatted.append({
                        "content": doc,
                        "source": metadata.get("source", "unknown"),
                        "score": round(score, 4),
                        "metadata": metadata
                    })
            
            logger.info(f"ChromaDB search returned {len(formatted)} results for: {query[:50]}...")
            return formatted
            
        except Exception as e:
            logger.error(f"ChromaDB search error: {e}")
            return []
    
    @staticmethod
    async def _search_cloud(query: str, top_k: int, user_id: str = None) -> List[dict]:
        """Supabase pgvector'da arama yap."""
        try:
            from supabase import create_client
            from dotenv import load_dotenv
            load_dotenv()
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Supabase credentials missing")
            
            client = create_client(supabase_url, supabase_key)
            embedder = _get_embedder()
            
            # Query embedding
            query_embedding = embedder.encode(query).tolist()
            
            # Supabase RPC call (user_id filtresi ile)
            rpc_params = {
                "query_embedding": query_embedding,
                "match_count": top_k
            }
            if user_id:
                rpc_params["filter_user_id"] = user_id
            
            result = client.rpc("match_documents", rpc_params).execute()
            
            # Sonuçları formatla
            formatted = []
            if result.data:
                for row in result.data:
                    formatted.append({
                        "content": row.get("content", ""),
                        "source": row.get("source", "unknown"),
                        "score": round(row.get("similarity", 0), 4),
                        "metadata": row.get("metadata", {})
                    })
            
            logger.info(f"Supabase search returned {len(formatted)} results")
            return formatted
            
        except Exception as e:
            logger.error(f"Supabase search error: {e}")
            return []
    
    @staticmethod
    async def delete_document(doc_id: str) -> Dict[str, Any]:
        """Dokümanı sil."""
        try:
            if _is_cloud_mode():
                from supabase import create_client
                from dotenv import load_dotenv
                load_dotenv()
                
                client = create_client(
                    os.getenv("SUPABASE_URL"),
                    os.getenv("SUPABASE_KEY")
                )
                client.table("documents").delete().eq("id", doc_id).execute()
            else:
                collection = _get_chroma_collection()
                collection.delete(ids=[doc_id])
            
            logger.info(f"Document deleted: {doc_id}")
            return {"success": True, "doc_id": doc_id}
            
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_stats() -> Dict[str, Any]:
        """Vektör veritabanı istatistiklerini döndür."""
        try:
            mode = MemoryCore.get_mode()
            
            if mode == "LOCAL":
                collection = _get_chroma_collection()
                count = collection.count()
                return {
                    "mode": mode,
                    "document_count": count,
                    "storage": "ChromaDB (Local)"
                }
            else:
                from supabase import create_client
                from dotenv import load_dotenv
                load_dotenv()
                
                client = create_client(
                    os.getenv("SUPABASE_URL"),
                    os.getenv("SUPABASE_KEY")
                )
                result = client.table("documents").select("id", count="exact").execute()
                
                return {
                    "mode": mode,
                    "document_count": result.count if result.count else 0,
                    "storage": "Supabase pgvector (Cloud)"
                }
                
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"mode": MemoryCore.get_mode(), "error": str(e)}
    
    @staticmethod
    async def get_all_documents(limit: int = 100) -> List[Dict[str, Any]]:
        """Tüm dokümanları listele (sayfalama ile)."""
        try:
            if _is_cloud_mode():
                from supabase import create_client
                from dotenv import load_dotenv
                load_dotenv()
                
                client = create_client(
                    os.getenv("SUPABASE_URL"),
                    os.getenv("SUPABASE_KEY")
                )
                result = client.table("documents")\
                    .select("id, source, metadata, created_at")\
                    .limit(limit)\
                    .execute()
                
                return result.data if result.data else []
            else:
                collection = _get_chroma_collection()
                results = collection.get(limit=limit, include=["metadatas"])
                
                documents = []
                if results and results.get("ids"):
                    for i, doc_id in enumerate(results["ids"]):
                        metadata = results["metadatas"][i] if results.get("metadatas") else {}
                        documents.append({
                            "id": doc_id,
                            "source": metadata.get("source", "unknown"),
                            "metadata": metadata,
                            "created_at": metadata.get("created_at", "unknown")
                        })
                
                return documents
                
        except Exception as e:
            logger.error(f"Get all documents error: {e}")
            return []
