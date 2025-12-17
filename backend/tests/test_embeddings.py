"""
Tests for embedding service and semantic search.
"""
import pytest
import numpy as np
from embeddings.embedding_service import EmbeddingService, EmbeddingConfig
from embeddings.vector_store import VectorStore, SearchResult
from embeddings.product_embedder import ProductEmbedder


class TestEmbeddingService:
    """Test embedding service functionality."""
    
    @pytest.fixture
    def embedding_service(self):
        """Create embedding service for testing."""
        config = EmbeddingConfig(
            model_name='all-MiniLM-L6-v2',
            batch_size=4,
            show_progress_bar=False
        )
        return EmbeddingService(config)
    
    def test_initialization(self, embedding_service):
        """Test embedding service initialization."""
        assert embedding_service is not None
        assert embedding_service.embedding_dimension > 0
        assert embedding_service.model is not None
    
    def test_encode_single_text(self, embedding_service):
        """Test encoding a single text."""
        text = "High quality copper cable for electrical installations"
        embedding = embedding_service.encode_single(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape[0] == embedding_service.embedding_dimension
        assert not np.all(embedding == 0)
    
    def test_encode_multiple_texts(self, embedding_service):
        """Test encoding multiple texts."""
        texts = [
            "Ceiling fan with high air delivery",
            "LED bulb energy efficient lighting",
            "Split AC with cooling capacity"
        ]
        embeddings = embedding_service.encode(texts)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (3, embedding_service.embedding_dimension)
        assert not np.all(embeddings == 0)
    
    def test_similarity_calculation(self, embedding_service):
        """Test similarity calculation."""
        text1 = "Copper electrical cable"
        text2 = "Copper wiring cable"
        text3 = "LED light bulb"
        
        emb1 = embedding_service.encode_single(text1)
        emb2 = embedding_service.encode_single(text2)
        emb3 = embedding_service.encode_single(text3)
        
        # Similar texts should have higher similarity
        sim_12 = embedding_service.similarity(emb1, emb2)
        sim_13 = embedding_service.similarity(emb1, emb3)
        
        assert 0 <= sim_12 <= 1
        assert 0 <= sim_13 <= 1
        assert sim_12 > sim_13  # Cable texts more similar than cable vs bulb
    
    def test_batch_similarity(self, embedding_service):
        """Test batch similarity calculation."""
        query = "electrical cable"
        candidates = [
            "copper wire cable",
            "LED bulb",
            "ceiling fan"
        ]
        
        query_emb = embedding_service.encode_single(query)
        candidate_embs = embedding_service.encode(candidates)
        
        similarities = embedding_service.similarity(query_emb, candidate_embs)
        
        assert len(similarities) == 3
        assert all(0 <= s <= 1 for s in similarities)


class TestVectorStore:
    """Test vector store functionality."""
    
    @pytest.fixture
    def vector_store(self, tmp_path):
        """Create vector store for testing."""
        store = VectorStore(
            collection_name="test_products",
            persist_directory=str(tmp_path / "test_chroma")
        )
        yield store
        # Cleanup
        store.reset()
    
    @pytest.fixture
    def sample_embeddings(self):
        """Create sample embeddings."""
        return np.random.rand(3, 384).astype(np.float32)
    
    def test_initialization(self, vector_store):
        """Test vector store initialization."""
        assert vector_store is not None
        assert vector_store.collection is not None
        assert vector_store.count() >= 0
    
    def test_add_embeddings(self, vector_store, sample_embeddings):
        """Test adding embeddings."""
        ids = ["prod1", "prod2", "prod3"]
        documents = ["Product 1", "Product 2", "Product 3"]
        metadatas = [
            {"name": "Product 1", "brand": "BrandA"},
            {"name": "Product 2", "brand": "BrandB"},
            {"name": "Product 3", "brand": "BrandA"}
        ]
        
        vector_store.add(
            ids=ids,
            embeddings=sample_embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        assert vector_store.count() == 3
    
    def test_search(self, vector_store, sample_embeddings):
        """Test searching embeddings."""
        # Add test data
        ids = ["prod1", "prod2", "prod3"]
        documents = ["Product 1", "Product 2", "Product 3"]
        
        vector_store.add(
            ids=ids,
            embeddings=sample_embeddings,
            documents=documents
        )
        
        # Search with first embedding
        results = vector_store.search(
            query_embedding=sample_embeddings[0],
            n_results=2
        )
        
        assert len(results) <= 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].id == "prod1"  # Should find itself first
    
    def test_get_embeddings(self, vector_store, sample_embeddings):
        """Test retrieving embeddings by ID."""
        ids = ["prod1", "prod2"]
        documents = ["Product 1", "Product 2"]
        
        vector_store.add(
            ids=ids,
            embeddings=sample_embeddings[:2],
            documents=documents
        )
        
        result = vector_store.get(ids=["prod1"])
        
        assert len(result['ids']) == 1
        assert result['ids'][0] == "prod1"
    
    def test_delete_embeddings(self, vector_store, sample_embeddings):
        """Test deleting embeddings."""
        ids = ["prod1", "prod2", "prod3"]
        documents = ["Product 1", "Product 2", "Product 3"]
        
        vector_store.add(
            ids=ids,
            embeddings=sample_embeddings,
            documents=documents
        )
        
        initial_count = vector_store.count()
        vector_store.delete(ids=["prod2"])
        
        assert vector_store.count() == initial_count - 1


class TestProductEmbedder:
    """Test product embedder functionality."""
    
    @pytest.fixture
    def product_embedder(self, tmp_path):
        """Create product embedder for testing."""
        vector_store = VectorStore(
            collection_name="test_products",
            persist_directory=str(tmp_path / "test_chroma")
        )
        embedder = ProductEmbedder(vector_store=vector_store)
        yield embedder
        # Cleanup
        embedder.reset()
    
    @pytest.fixture
    def sample_products(self):
        """Create sample products."""
        return [
            {
                "id": "PROD001",
                "name": "Havells Cable 1.5mm",
                "brand": "Havells",
                "category": "Cables",
                "description": "Copper electrical cable",
                "specifications": {
                    "size": "1.5 sq mm",
                    "material": "Copper"
                },
                "price": 45
            },
            {
                "id": "PROD002",
                "name": "Polycab Fan",
                "brand": "Polycab",
                "category": "Fans",
                "description": "Ceiling fan high speed",
                "specifications": {
                    "size": "1200mm",
                    "speed": "400 RPM"
                },
                "price": 2500
            }
        ]
    
    def test_create_product_text(self, product_embedder, sample_products):
        """Test creating product text representation."""
        text = product_embedder.create_product_text(sample_products[0])
        
        assert "Havells" in text
        assert "Cable" in text
        assert "Copper" in text
        assert len(text) > 0
    
    def test_embed_products(self, product_embedder, sample_products):
        """Test embedding products."""
        count = product_embedder.embed_products(
            products=sample_products,
            show_progress=False
        )
        
        assert count == 2
        assert product_embedder.vector_store.count() == 2
    
    def test_search_products(self, product_embedder, sample_products):
        """Test searching for products."""
        # First embed the products
        product_embedder.embed_products(
            products=sample_products,
            show_progress=False
        )
        
        # Search for cable
        results = product_embedder.search(
            query="copper electrical cable",
            n_results=2
        )
        
        assert len(results) > 0
        assert isinstance(results[0], SearchResult)
        # First result should be the cable (more relevant)
        assert "Cable" in results[0].metadata['name']
    
    def test_search_similar_products(self, product_embedder, sample_products):
        """Test finding similar products."""
        # Embed products
        product_embedder.embed_products(
            products=sample_products,
            show_progress=False
        )
        
        # Find similar to first product
        results = product_embedder.search_similar_products(
            product_id="PROD001",
            n_results=1
        )
        
        assert len(results) > 0
        assert results[0].id != "PROD001"  # Should not include self
    
    def test_get_stats(self, product_embedder, sample_products):
        """Test getting embedder statistics."""
        product_embedder.embed_products(
            products=sample_products,
            show_progress=False
        )
        
        stats = product_embedder.get_stats()
        
        assert 'vector_store' in stats
        assert 'embedding_model' in stats
        assert 'total_products' in stats
        assert stats['total_products'] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
