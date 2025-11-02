"""
Component 3: Natural Language Search Interface
RAG application using LlamaIndex/LangChain to query trade intelligence data
"""

import os
import logging
from typing import List, Dict, Optional
import configparser

# LLM frameworks
from llama_index.core import VectorStoreIndex, Settings, StorageContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import ResponseMode

from pinecone import Pinecone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rag_query.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradeIntelligenceRAG:
    """
    RAG-based query interface for trade intelligence platform
    Uses LlamaIndex for retrieval and OpenAI for generation
    """
    
    def __init__(self, config_path='config.ini'):
        """Initialize RAG system with configuration"""
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        # Initialize embedding model
        openai_api_key = self.config.get('EMBEDDINGS', 'openai_api_key')
        embedding_model = self.config.get('EMBEDDINGS', 'openai_model', 
                                          fallback='text-embedding-3-small')
        self.embed_model = OpenAIEmbedding(
            model=embedding_model,
            api_key=openai_api_key
        )
        
        # Initialize LLM for generation
        llm_model = self.config.get('LLM', 'model', fallback='gpt-4o-mini')
        self.llm = OpenAI(
            model=llm_model,
            api_key=openai_api_key,
            temperature=0.1  # Low temperature for factual responses
        )
        
        # Set global settings for LlamaIndex
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        # Initialize Pinecone vector store
        pinecone_api_key = self.config.get('VECTOR_DB', 'pinecone_api_key')
        index_name = self.config.get('VECTOR_DB', 'pinecone_index_name')
        
        pc = Pinecone(api_key=pinecone_api_key)
        pinecone_index = pc.Index(index_name)
        
        # Create vector store
        self.vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
        
        # Create storage context
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        # Create index from existing vectors
        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store,
            storage_context=storage_context
        )
        
        # Create query engine
        self.query_engine = self._create_query_engine()
        
        logger.info("Trade Intelligence RAG system initialized successfully")
    
    def _create_query_engine(self, top_k: int = 10):
        """Create a query engine with custom retriever"""
        # Create retriever
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k,
        )
        
        # Create query engine with retriever
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            response_mode=ResponseMode.COMPACT,
            llm=self.llm,
        )
        
        return query_engine
    
    def query(self, question: str, top_k: int = 10) -> Dict:
        """
        Query the RAG system with a natural language question
        
        Args:
            question: Natural language question
            top_k: Number of relevant documents to retrieve
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            logger.info(f"Processing query: {question}")
            
            # Recreate query engine with specified top_k
            query_engine = self._create_query_engine(top_k=top_k)
            
            # Execute query
            response = query_engine.query(question)
            
            # Extract source documents
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    sources.append({
                        'text': node.node.text,
                        'score': node.score,
                        'metadata': node.node.metadata
                    })
            
            result = {
                'question': question,
                'answer': str(response),
                'sources': sources,
                'num_sources': len(sources)
            }
            
            logger.info(f"Query completed with {len(sources)} sources")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'question': question,
                'answer': f"Error processing query: {str(e)}",
                'sources': [],
                'num_sources': 0
            }
    
    def query_with_filters(self, question: str, filters: Dict, top_k: int = 10) -> Dict:
        """
        Query with metadata filters
        
        Args:
            question: Natural language question
            filters: Metadata filters (e.g., {'hs_code': '851712', 'source': 'bill_of_lading'})
            top_k: Number of results
        
        Returns:
            Query results
        """
        try:
            logger.info(f"Processing filtered query: {question} with filters: {filters}")
            
            # Create custom retriever with filters
            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=top_k,
                filters=filters
            )
            
            query_engine = RetrieverQueryEngine.from_args(
                retriever=retriever,
                response_mode=ResponseMode.COMPACT,
                llm=self.llm,
            )
            
            response = query_engine.query(question)
            
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    sources.append({
                        'text': node.node.text,
                        'score': node.score,
                        'metadata': node.node.metadata
                    })
            
            result = {
                'question': question,
                'filters': filters,
                'answer': str(response),
                'sources': sources,
                'num_sources': len(sources)
            }
            
            logger.info(f"Filtered query completed with {len(sources)} sources")
            return result
            
        except Exception as e:
            logger.error(f"Error processing filtered query: {str(e)}")
            return {
                'question': question,
                'filters': filters,
                'answer': f"Error: {str(e)}",
                'sources': [],
                'num_sources': 0
            }
    
    def ask_complex_question(self, question: str) -> str:
        """
        Simple interface for asking questions and getting text answers
        
        Args:
            question: Natural language question
        
        Returns:
            Text answer
        """
        result = self.query(question)
        return result['answer']

class InteractiveCLI:
    """Interactive command-line interface for querying trade intelligence"""
    
    def __init__(self):
        self.rag = TradeIntelligenceRAG()
        logger.info("Interactive CLI initialized")
    
    def run(self):
        """Run interactive query loop"""
        print("=" * 80)
        print("Trade Intelligence RAG System - Interactive Query Interface")
        print("=" * 80)
        print("\nCommands:")
        print("  - Type your question in natural language")
        print("  - Type 'examples' to see example questions")
        print("  - Type 'quit' or 'exit' to exit")
        print("=" * 80)
        
        while True:
            try:
                print("\n")
                question = input("🔍 Your Question: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\nThank you for using Trade Intelligence RAG!")
                    break
                
                if question.lower() == 'examples':
                    self._show_examples()
                    continue
                
                # Process query
                print("\n⏳ Processing your query...\n")
                result = self.rag.query(question, top_k=5)
                
                # Display results
                print("=" * 80)
                print("📊 ANSWER:")
                print("=" * 80)
                print(result['answer'])
                print("\n" + "=" * 80)
                print(f"📚 Based on {result['num_sources']} relevant sources")
                print("=" * 80)
                
                # Show sources if requested
                show_sources = input("\nShow source documents? (y/n): ").strip().lower()
                if show_sources == 'y':
                    self._display_sources(result['sources'])
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error in interactive loop: {str(e)}")
                print(f"\n❌ Error: {str(e)}")
    
    def _show_examples(self):
        """Display example questions"""
        examples = [
            "Who are the top 3 new buyers for HS code 851712 in the last month?",
            "Show me all shipments from 'Supplier Inc.' to any buyers in Germany.",
            "What is the average monthly import value for HS code 950300?",
            "List all new suppliers that shipped to 'MyCompetitor LLC' in the last week.",
            "Which countries imported the most electronics (HS 8517) last month?",
            "Show me recent shipments of medical devices from China to the USA.",
            "What is the trend in import volumes for HS code 851712 over the last 3 months?",
        ]
        
        print("\n" + "=" * 80)
        print("📝 Example Questions:")
        print("=" * 80)
        for i, ex in enumerate(examples, 1):
            print(f"{i}. {ex}")
        print("=" * 80)
    
    def _display_sources(self, sources: List[Dict]):
        """Display source documents"""
        print("\n" + "=" * 80)
        print("📄 SOURCE DOCUMENTS:")
        print("=" * 80)
        
        for i, source in enumerate(sources, 1):
            print(f"\n--- Source {i} (Relevance: {source['score']:.3f}) ---")
            print(source['text'])
            print(f"Metadata: {source['metadata']}")
        
        print("=" * 80)

class ProgrammaticQueryInterface:
    """
    Programmatic interface for automated queries
    Used by monitoring/alerting system
    """
    
    def __init__(self):
        self.rag = TradeIntelligenceRAG()
    
    def execute_query(self, question: str, return_sources: bool = False) -> Dict:
        """
        Execute a query programmatically
        
        Args:
            question: Natural language question
            return_sources: Whether to include source documents
        
        Returns:
            Query result dictionary
        """
        result = self.rag.query(question)
        
        if not return_sources:
            # Remove sources to reduce payload
            result.pop('sources', None)
        
        return result
    
    def execute_batch_queries(self, questions: List[str]) -> List[Dict]:
        """
        Execute multiple queries
        
        Args:
            questions: List of questions
        
        Returns:
            List of results
        """
        results = []
        for question in questions:
            result = self.execute_query(question)
            results.append(result)
        
        return results
    
    def check_condition(self, question: str, keywords: List[str] = None) -> bool:
        """
        Check if query result contains specific keywords (for alerting)
        
        Args:
            question: Natural language question
            keywords: Keywords to check for in answer
        
        Returns:
            True if condition met, False otherwise
        """
        result = self.execute_query(question)
        answer = result['answer'].lower()
        
        # If no keywords specified, check if answer indicates "yes" or contains data
        if not keywords:
            positive_indicators = ['yes', 'found', 'detected', 'identified', 'new', 'increased']
            negative_indicators = ['no', 'none', 'not found', 'no data', 'no records']
            
            # Check for positive indicators
            for indicator in positive_indicators:
                if indicator in answer:
                    return True
            
            # Check if answer is substantial (not just "no data")
            if any(neg in answer for neg in negative_indicators):
                return False
            
            # If answer is substantial (>100 chars), consider it positive
            return len(answer) > 100
        
        # Check for specific keywords
        return any(keyword.lower() in answer for keyword in keywords)

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        # Run interactive CLI
        cli = InteractiveCLI()
        cli.run()
    else:
        # Example programmatic usage
        print("Starting Trade Intelligence RAG Query Interface\n")
        
        rag = TradeIntelligenceRAG()
        
        # Example queries
        questions = [
            "Who are the top buyers for HS code 851712?",
            "Show me recent shipments from China to Germany.",
            "What is the trend in electronics imports?"
        ]
        
        for question in questions:
            print(f"\nQuestion: {question}")
            answer = rag.ask_complex_question(question)
            print(f"Answer: {answer}\n")
            print("-" * 80)

if __name__ == "__main__":
    main()
