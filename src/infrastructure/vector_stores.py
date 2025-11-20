"""
Vector Store Implementations.

Adapters for vector databases (Qdrant, ChromaDB).
Provides semantic search capabilities for RAG.
"""

from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.domain.exceptions import CollectionNotFoundError, VectorStoreError
from src.domain.interfaces import IVectorStore


class QdrantVectorStore(IVectorStore):
    """
    Qdrant vector database implementation.
    
    Qdrant is recommended for production due to:
    - High performance at scale
    - Rich filtering capabilities
    - Distributed deployment support
    
    RISK: Qdrant instance must be properly sized for workload.
    Monitor memory usage and query latency.
    
    TODO: Add connection pooling
    TODO: Add automatic retry on transient failures
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
        https: bool = False,
        timeout: float = 30.0,
    ):
        """
        Initialize Qdrant client.
        
        Args:
            host: Qdrant server host
            port: Qdrant server port
            api_key: Optional API key for authentication
            https: Use HTTPS connection
            timeout: Request timeout in seconds
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError:
            raise ImportError(
                "Qdrant client not installed. Install with: pip install qdrant-client"
            )

        self.client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            https=https,
            timeout=timeout,
        )
        self._VectorParams = VectorParams
        self._Distance = Distance

    async def create_collection(
        self,
        name: str,
        dimension: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a new collection with specified dimension."""
        try:
            from qdrant_client.models import Distance, VectorParams

            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE,  # Cosine similarity is standard
                ),
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to create collection {name}: {str(e)}") from e

    async def insert_vectors(
        self,
        collection: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Insert vectors with metadata.
        
        Uses batch upsert for efficiency.
        """
        try:
            from qdrant_client.models import PointStruct

            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid4()) for _ in vectors]

            # Create points
            points = [
                PointStruct(id=id_, vector=vector, payload=payload)
                for id_, vector, payload in zip(ids, vectors, payloads)
            ]

            # Batch upsert
            self.client.upsert(collection_name=collection, points=points)

            return ids

        except Exception as e:
            raise VectorStoreError(f"Failed to insert vectors: {str(e)}") from e

    async def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using vector similarity.
        
        Returns top-k most similar vectors with scores and payloads.
        """
        try:
            # Convert filter to Qdrant format if provided
            qdrant_filter = None
            if filter:
                from qdrant_client.models import Filter, FieldCondition, MatchValue

                conditions = [
                    FieldCondition(key=key, match=MatchValue(value=value))
                    for key, value in filter.items()
                ]
                qdrant_filter = Filter(must=conditions)

            # Perform search
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                query_filter=qdrant_filter,
            )

            # Format results
            return [
                {
                    "id": str(result.id),
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results
            ]

        except Exception as e:
            if "not found" in str(e).lower():
                raise CollectionNotFoundError(collection)
            raise VectorStoreError(f"Search failed: {str(e)}") from e

    async def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name=name)
        except Exception as e:
            raise VectorStoreError(f"Failed to delete collection {name}: {str(e)}") from e


class ChromaVectorStore(IVectorStore):
    """
    ChromaDB vector store implementation.
    
    ChromaDB is simpler and good for:
    - Development and testing
    - Smaller-scale deployments
    - Embedded use cases
    
    For production at scale, prefer Qdrant.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        """
        Initialize ChromaDB client.
        
        Args:
            persist_directory: Directory to persist data (for persistent client)
            host: ChromaDB server host (for HTTP client)
            port: ChromaDB server port (for HTTP client)
        """
        try:
            import chromadb
        except ImportError:
            raise ImportError(
                "ChromaDB not installed. Install with: pip install chromadb"
            )

        if host and port:
            self.client = chromadb.HttpClient(host=host, port=port)
        else:
            settings = chromadb.config.Settings()
            if persist_directory:
                settings.persist_directory = persist_directory
                settings.is_persistent = True
            self.client = chromadb.Client(settings)

    async def create_collection(
        self,
        name: str,
        dimension: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a new collection."""
        try:
            self.client.create_collection(
                name=name,
                metadata=metadata or {},
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to create collection {name}: {str(e)}") from e

    async def insert_vectors(
        self,
        collection: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Insert vectors with metadata."""
        try:
            coll = self.client.get_collection(name=collection)

            if ids is None:
                ids = [str(uuid4()) for _ in vectors]

            coll.add(
                ids=ids,
                embeddings=vectors,
                metadatas=payloads,
            )

            return ids

        except Exception as e:
            raise VectorStoreError(f"Failed to insert vectors: {str(e)}") from e

    async def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search."""
        try:
            coll = self.client.get_collection(name=collection)

            results = coll.query(
                query_embeddings=[query_vector],
                n_results=limit,
                where=filter,
            )

            # Format results
            formatted = []
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "score": 1.0 - results["distances"][0][i],  # Convert distance to similarity
                    "payload": results["metadatas"][0][i],
                })

            return formatted

        except Exception as e:
            if "does not exist" in str(e).lower():
                raise CollectionNotFoundError(collection)
            raise VectorStoreError(f"Search failed: {str(e)}") from e

    async def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        try:
            self.client.delete_collection(name=name)
        except Exception as e:
            raise VectorStoreError(f"Failed to delete collection {name}: {str(e)}") from e
