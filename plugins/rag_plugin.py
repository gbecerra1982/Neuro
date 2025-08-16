"""
RAG Plugin - Retrieval Augmented Generation plugin for knowledge base integration
"""

import logging
from typing import Dict, Optional, List, Any
import json
import os
from datetime import datetime

from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class RAGPlugin(BasePlugin):
    """
    RAG (Retrieval Augmented Generation) plugin for integrating knowledge bases.
    Supports multiple vector store backends and embedding models.
    """
    
    def __init__(self):
        """Initialize RAG plugin"""
        super().__init__()
        self.name = "RAGPlugin"
        self.metadata = {
            'version': '1.0.0',
            'author': 'Avatar Factory',
            'description': 'Retrieval Augmented Generation for knowledge base integration'
        }
        
        # RAG components
        self.vector_store = None
        self.embeddings = None
        self.retriever = None
        self.knowledge_base_path = None
        
        # Configuration
        self.vector_store_type = None
        self.embedding_model = None
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.top_k = 5
        
        # In-memory store for simplicity
        self.documents = []
        self.embeddings_cache = {}
        
    def initialize(self, config: Dict) -> bool:
        """
        Initialize RAG plugin with configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if initialization successful
        """
        try:
            self.config = config
            
            # Get configuration values
            self.vector_store_type = config.get('vector_store_type', 'in_memory')
            self.embedding_model = config.get('embedding_model', 'text-embedding-3-small')
            self.chunk_size = config.get('chunk_size', 1000)
            self.chunk_overlap = config.get('chunk_overlap', 200)
            self.top_k = config.get('top_k', 5)
            self.knowledge_base_path = config.get('knowledge_base_path')
            
            # Initialize vector store
            self._initialize_vector_store()
            
            # Initialize embeddings
            self._initialize_embeddings()
            
            # Load knowledge base if path provided
            if self.knowledge_base_path:
                self._load_knowledge_base()
            
            logger.info(f"RAG plugin initialized with {self.vector_store_type} vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG plugin: {e}")
            return False
    
    def _initialize_vector_store(self):
        """Initialize the vector store based on configuration"""
        if self.vector_store_type == 'azure_search':
            self._setup_azure_search()
        elif self.vector_store_type == 'pinecone':
            self._setup_pinecone()
        elif self.vector_store_type == 'chroma':
            self._setup_chroma()
        else:
            self._setup_in_memory()
    
    def _setup_azure_search(self):
        """Setup Azure Cognitive Search as vector store"""
        try:
            # This would use Azure Search SDK in production
            logger.info("Azure Search vector store initialized (mock)")
            self.vector_store = {'type': 'azure_search', 'documents': []}
            
        except Exception as e:
            logger.error(f"Failed to setup Azure Search: {e}")
            self._setup_in_memory()
    
    def _setup_pinecone(self):
        """Setup Pinecone as vector store"""
        try:
            # This would use Pinecone SDK in production
            logger.info("Pinecone vector store initialized (mock)")
            self.vector_store = {'type': 'pinecone', 'documents': []}
            
        except Exception as e:
            logger.error(f"Failed to setup Pinecone: {e}")
            self._setup_in_memory()
    
    def _setup_chroma(self):
        """Setup Chroma as vector store"""
        try:
            # This would use Chroma SDK in production
            logger.info("Chroma vector store initialized (mock)")
            self.vector_store = {'type': 'chroma', 'documents': []}
            
        except Exception as e:
            logger.error(f"Failed to setup Chroma: {e}")
            self._setup_in_memory()
    
    def _setup_in_memory(self):
        """Setup in-memory vector store"""
        self.vector_store = {
            'type': 'in_memory',
            'documents': [],
            'embeddings': []
        }
        logger.info("In-memory vector store initialized")
    
    def _initialize_embeddings(self):
        """Initialize embedding model"""
        # In production, this would initialize the actual embedding model
        self.embeddings = {
            'model': self.embedding_model,
            'dimension': 1536  # Default for OpenAI embeddings
        }
        logger.info(f"Embeddings initialized with model: {self.embedding_model}")
    
    def _load_knowledge_base(self):
        """Load documents from knowledge base path"""
        if not self.knowledge_base_path or not os.path.exists(self.knowledge_base_path):
            logger.warning(f"Knowledge base path not found: {self.knowledge_base_path}")
            return
        
        try:
            # Load all documents from the knowledge base directory
            loaded_count = 0
            
            for root, dirs, files in os.walk(self.knowledge_base_path):
                for file in files:
                    if file.endswith(('.txt', '.md', '.json')):
                        file_path = os.path.join(root, file)
                        self._load_document(file_path)
                        loaded_count += 1
            
            logger.info(f"Loaded {loaded_count} documents from knowledge base")
            
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
    
    def _load_document(self, file_path: str):
        """Load a single document"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create document metadata
            doc = {
                'id': os.path.basename(file_path),
                'path': file_path,
                'content': content,
                'metadata': {
                    'source': file_path,
                    'loaded_at': datetime.now().isoformat()
                }
            }
            
            # Add to documents
            self.documents.append(doc)
            
            # In production, this would also create embeddings and add to vector store
            
        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {e}")
    
    async def process(self, input_data: Dict) -> Optional[Dict]:
        """
        Process input through RAG pipeline.
        
        Args:
            input_data: Input data with query
            
        Returns:
            Response with retrieved context
        """
        if not self.enabled:
            return None
        
        try:
            query = input_data.get('content', '')
            if not query:
                return None
            
            # Retrieve relevant documents
            relevant_docs = await self._retrieve(query)
            
            if not relevant_docs:
                return None
            
            # Format context from retrieved documents
            context = self._format_context(relevant_docs)
            
            # Return enhanced response with context
            return {
                'content': context,
                'metadata': {
                    'plugin': self.name,
                    'retrieved_docs': len(relevant_docs),
                    'sources': [doc.get('metadata', {}).get('source', 'unknown') for doc in relevant_docs]
                },
                'context': context,
                'final': False  # Allow other plugins to process
            }
            
        except Exception as e:
            return self.handle_error(e, "processing query")
    
    async def _retrieve(self, query: str) -> List[Dict]:
        """
        Retrieve relevant documents for query.
        
        Args:
            query: Search query
            
        Returns:
            List of relevant documents
        """
        # Simple retrieval for in-memory store
        # In production, this would use vector similarity search
        
        relevant_docs = []
        query_lower = query.lower()
        
        for doc in self.documents:
            content_lower = doc['content'].lower()
            
            # Simple keyword matching (replace with vector search in production)
            if any(word in content_lower for word in query_lower.split()):
                relevance_score = sum(1 for word in query_lower.split() if word in content_lower)
                doc['score'] = relevance_score
                relevant_docs.append(doc)
        
        # Sort by relevance and return top k
        relevant_docs.sort(key=lambda x: x.get('score', 0), reverse=True)
        return relevant_docs[:self.top_k]
    
    def _format_context(self, documents: List[Dict]) -> str:
        """
        Format retrieved documents into context string.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.get('metadata', {}).get('source', 'Document')
            content = doc.get('content', '')
            
            # Truncate if too long
            if len(content) > self.chunk_size:
                content = content[:self.chunk_size] + "..."
            
            context_parts.append(f"[Source {i}: {source}]\n{content}\n")
        
        return "\n".join(context_parts)
    
    async def add_document(self, document: Dict) -> bool:
        """
        Add a document to the knowledge base.
        
        Args:
            document: Document dictionary with content and metadata
            
        Returns:
            True if document added successfully
        """
        try:
            # Add document ID if not present
            if 'id' not in document:
                document['id'] = f"doc_{len(self.documents)}"
            
            # Add timestamp
            if 'metadata' not in document:
                document['metadata'] = {}
            document['metadata']['added_at'] = datetime.now().isoformat()
            
            # Add to documents
            self.documents.append(document)
            
            # In production, would also create embeddings and update vector store
            
            logger.info(f"Document added: {document['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    async def search(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """
        Search for documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of matching documents
        """
        top_k = top_k or self.top_k
        return await self._retrieve(query)
    
    async def cleanup(self):
        """Clean up RAG plugin resources"""
        try:
            # Clear documents and caches
            self.documents.clear()
            self.embeddings_cache.clear()
            
            # Close vector store connections if needed
            if self.vector_store and isinstance(self.vector_store, dict):
                self.vector_store['documents'].clear()
            
            logger.info("RAG plugin cleaned up")
            
        except Exception as e:
            logger.error(f"Error during RAG plugin cleanup: {e}")
    
    def get_statistics(self) -> Dict:
        """Get RAG plugin statistics"""
        return {
            'total_documents': len(self.documents),
            'vector_store_type': self.vector_store_type,
            'embedding_model': self.embedding_model,
            'chunk_size': self.chunk_size,
            'top_k': self.top_k
        }
