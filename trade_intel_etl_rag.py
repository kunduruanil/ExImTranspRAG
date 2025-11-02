"""
Component 2: ETL & Vectorization Pipeline
Converts raw trade data into natural language chunks, generates embeddings,
and stores them in a vector database for RAG retrieval.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import configparser
from pathlib import Path
import glob

# Vector DB clients
from pinecone import Pinecone, ServerlessSpec
# Alternative: from weaviate import Client as WeaviateClient

# Embedding models
import openai
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl_vectorization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates embeddings using OpenAI or local models"""
    
    def __init__(self, config: configparser.ConfigParser):
        self.provider = config.get('EMBEDDINGS', 'provider', fallback='openai')
        
        if self.provider == 'openai':
            self.api_key = config.get('EMBEDDINGS', 'openai_api_key')
            openai.api_key = self.api_key
            self.model = config.get('EMBEDDINGS', 'openai_model', fallback='text-embedding-3-small')
            self.dimension = 1536  # Default for text-embedding-3-small
        elif self.provider == 'huggingface':
            model_name = config.get('EMBEDDINGS', 'hf_model', fallback='all-MiniLM-L6-v2')
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
        
        logger.info(f"Initialized {self.provider} embedding generator (dimension: {self.dimension})")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        try:
            if self.provider == 'openai':
                response = openai.embeddings.create(
                    input=text,
                    model=self.model
                )
                return response.data[0].embedding
            
            elif self.provider == 'huggingface':
                embedding = self.model.encode(text)
                return embedding.tolist()
                
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing embedding batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            try:
                if self.provider == 'openai':
                    response = openai.embeddings.create(
                        input=batch,
                        model=self.model
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    embeddings.extend(batch_embeddings)
                
                elif self.provider == 'huggingface':
                    batch_embeddings = self.model.encode(batch)
                    embeddings.extend([emb.tolist() for emb in batch_embeddings])
                    
            except Exception as e:
                logger.error(f"Error in batch embedding generation: {str(e)}")
                # Generate individually as fallback
                for text in batch:
                    embeddings.append(self.generate_embedding(text))
        
        return embeddings

class TextChunkFormatter:
    """Converts raw trade data into natural language chunks"""
    
    @staticmethod
    def format_comtrade_record(record: Dict) -> Tuple[str, Dict]:
        """
        Convert Comtrade JSON record to natural language text
        
        Returns:
            Tuple of (text_chunk, metadata)
        """
        try:
            period = record.get('period', 'Unknown')
            year = period[:4] if len(period) >= 4 else 'Unknown'
            month = period[4:] if len(period) >= 6 else 'Unknown'
            
            reporter = record.get('reporterDesc', 'Unknown Country')
            partner = record.get('partnerDesc', 'World')
            hs_code = record.get('cmdCode', 'Unknown')
            hs_desc = record.get('cmdDesc', 'Unknown Product')
            
            # Primary trade value (in USD)
            trade_value = record.get('primaryValue', 0)
            trade_value_formatted = f"${trade_value:,.0f}" if trade_value else "$0"
            
            # Quantity
            qty = record.get('qty', 0)
            qty_unit = record.get('qtyUnitAbbr', 'units')
            
            # Flow (Import/Export)
            flow = record.get('flowDesc', 'Import')
            
            # Create natural language chunk
            text = (
                f"Trade Statistics Update: In {month}/{year}, {reporter}'s {flow.lower()}s "
                f"of {hs_desc} (HS Code: {hs_code}) from {partner} totaled {trade_value_formatted}. "
                f"The quantity was {qty:,.0f} {qty_unit}."
            )
            
            # Metadata for filtering
            metadata = {
                'source': 'comtrade',
                'date': f"{year}-{month}-01",
                'hs_code': str(hs_code),
                'reporter_country': reporter,
                'partner_country': partner,
                'trade_value_usd': float(trade_value) if trade_value else 0.0,
                'quantity': float(qty) if qty else 0.0,
                'flow': flow,
                'period': period
            }
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error formatting Comtrade record: {str(e)}")
            return None, None
    
    @staticmethod
    def format_bl_record(record: Dict) -> Tuple[str, Dict]:
        """
        Convert Bill of Lading record to natural language text
        
        Returns:
            Tuple of (text_chunk, metadata)
        """
        try:
            # Extract fields (field names may vary by provider)
            shipment_date = record.get('shipment_date', record.get('date', 'Unknown Date'))
            buyer = record.get('buyer', record.get('consignee', 'Unknown Buyer'))
            supplier = record.get('supplier', record.get('shipper', 'Unknown Supplier'))
            
            hs_code = record.get('hs_code', record.get('hscode', 'Unknown'))
            product_desc = record.get('product_description', record.get('description', 'Unknown Product'))
            
            quantity = record.get('quantity', record.get('qty', 0))
            weight_kg = record.get('weight_kg', record.get('weight', 0))
            
            origin_country = record.get('origin_country', record.get('country_of_origin', 'Unknown'))
            dest_country = record.get('destination_country', record.get('country_of_destination', 'Unknown'))
            
            port_of_loading = record.get('port_of_loading', 'Unknown Port')
            port_of_discharge = record.get('port_of_discharge', 'Unknown Port')
            
            # Create natural language chunk
            text = (
                f"New Shipment: On {shipment_date}, '{buyer}' (in {dest_country}) "
                f"received a shipment of {product_desc} (HS Code: {hs_code}) "
                f"from '{supplier}' (in {origin_country}). "
                f"The shipment contained {quantity} units weighing {weight_kg}kg, "
                f"shipped from {port_of_loading} to {port_of_discharge}."
            )
            
            # Metadata for filtering
            metadata = {
                'source': 'bill_of_lading',
                'date': shipment_date,
                'hs_code': str(hs_code),
                'buyer': buyer,
                'supplier': supplier,
                'origin_country': origin_country,
                'destination_country': dest_country,
                'quantity': float(quantity) if quantity else 0.0,
                'weight_kg': float(weight_kg) if weight_kg else 0.0,
                'port_of_loading': port_of_loading,
                'port_of_discharge': port_of_discharge
            }
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error formatting B/L record: {str(e)}")
            return None, None

class VectorDBManager:
    """Manages vector database operations (Pinecone)"""
    
    def __init__(self, config: configparser.ConfigParser, embedding_dimension: int):
        self.provider = config.get('VECTOR_DB', 'provider', fallback='pinecone')
        
        if self.provider == 'pinecone':
            api_key = config.get('VECTOR_DB', 'pinecone_api_key')
            self.index_name = config.get('VECTOR_DB', 'pinecone_index_name', fallback='trade-intelligence')
            
            # Initialize Pinecone
            self.pc = Pinecone(api_key=api_key)
            
            # Create index if it doesn't exist
            if self.index_name not in [idx.name for idx in self.pc.list_indexes()]:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=embedding_dimension,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=config.get('VECTOR_DB', 'pinecone_region', fallback='us-east-1')
                    )
                )
            
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
        
        else:
            raise ValueError(f"Unsupported vector DB provider: {self.provider}")
    
    def upsert_vectors(self, vectors: List[Tuple[str, List[float], str, Dict]]):
        """
        Insert or update vectors in the database
        
        Args:
            vectors: List of (id, embedding, text, metadata) tuples
        """
        try:
            if self.provider == 'pinecone':
                # Prepare data for Pinecone format
                upsert_data = []
                for vec_id, embedding, text, metadata in vectors:
                    # Add text to metadata for retrieval
                    full_metadata = {**metadata, 'text': text}
                    upsert_data.append((vec_id, embedding, full_metadata))
                
                # Upsert in batches
                batch_size = 100
                for i in range(0, len(upsert_data), batch_size):
                    batch = upsert_data[i:i + batch_size]
                    self.index.upsert(vectors=batch)
                    logger.info(f"Upserted batch {i//batch_size + 1}/{(len(upsert_data)-1)//batch_size + 1}")
                
                logger.info(f"Successfully upserted {len(vectors)} vectors")
                
        except Exception as e:
            logger.error(f"Error upserting vectors: {str(e)}")
            raise
    
    def query_vectors(self, query_embedding: List[float], top_k: int = 10, 
                     filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Query the vector database
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_dict: Metadata filters
        
        Returns:
            List of matching results with text and metadata
        """
        try:
            if self.provider == 'pinecone':
                results = self.index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter_dict
                )
                
                return [
                    {
                        'id': match.id,
                        'score': match.score,
                        'text': match.metadata.get('text', ''),
                        'metadata': {k: v for k, v in match.metadata.items() if k != 'text'}
                    }
                    for match in results.matches
                ]
                
        except Exception as e:
            logger.error(f"Error querying vectors: {str(e)}")
            return []

class ETLPipeline:
    """Main ETL pipeline for processing raw data and loading into vector DB"""
    
    def __init__(self, config_path='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        self.embedding_gen = EmbeddingGenerator(self.config)
        self.formatter = TextChunkFormatter()
        self.vector_db = VectorDBManager(self.config, self.embedding_gen.dimension)
        
        self.raw_data_dir = 'data/raw'
        self.processed_dir = 'data/processed'
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def process_raw_data_files(self):
        """Process all unprocessed raw data files"""
        logger.info("=" * 80)
        logger.info("Starting ETL & Vectorization Pipeline")
        logger.info("=" * 80)
        
        # Find all raw JSON files
        comtrade_files = glob.glob(os.path.join(self.raw_data_dir, 'comtrade_*.json'))
        bl_files = glob.glob(os.path.join(self.raw_data_dir, 'bl_*.json'))
        
        logger.info(f"Found {len(comtrade_files)} Comtrade files and {len(bl_files)} B/L files")
        
        total_records = 0
        
        # Process Comtrade files
        for filepath in comtrade_files:
            records_processed = self._process_comtrade_file(filepath)
            total_records += records_processed
        
        # Process B/L files
        for filepath in bl_files:
            records_processed = self._process_bl_file(filepath)
            total_records += records_processed
        
        logger.info("=" * 80)
        logger.info(f"ETL Pipeline Complete - Processed {total_records} total records")
        logger.info("=" * 80)
    
    def _process_comtrade_file(self, filepath: str) -> int:
        """Process a single Comtrade data file"""
        try:
            logger.info(f"Processing Comtrade file: {filepath}")
            
            with open(filepath, 'r') as f:
                records = json.load(f)
            
            if not records:
                logger.warning(f"No records in file: {filepath}")
                return 0
            
            # Format records into text chunks
            chunks = []
            for record in records:
                text, metadata = self.formatter.format_comtrade_record(record)
                if text and metadata:
                    chunks.append((text, metadata))
            
            # Generate embeddings
            texts = [chunk[0] for chunk in chunks]
            embeddings = self.embedding_gen.generate_batch_embeddings(texts)
            
            # Prepare vectors for insertion
            vectors = []
            for i, (text, metadata) in enumerate(chunks):
                vec_id = f"comtrade_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
                vectors.append((vec_id, embeddings[i], text, metadata))
            
            # Upsert to vector DB
            self.vector_db.upsert_vectors(vectors)
            
            # Move to processed directory
            self._mark_as_processed(filepath)
            
            logger.info(f"Processed {len(chunks)} Comtrade records from {filepath}")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error processing Comtrade file {filepath}: {str(e)}")
            return 0
    
    def _process_bl_file(self, filepath: str) -> int:
        """Process a single B/L data file"""
        try:
            logger.info(f"Processing B/L file: {filepath}")
            
            with open(filepath, 'r') as f:
                records = json.load(f)
            
            if not records:
                logger.warning(f"No records in file: {filepath}")
                return 0
            
            # Format records into text chunks
            chunks = []
            for record in records:
                text, metadata = self.formatter.format_bl_record(record)
                if text and metadata:
                    chunks.append((text, metadata))
            
            # Generate embeddings
            texts = [chunk[0] for chunk in chunks]
            embeddings = self.embedding_gen.generate_batch_embeddings(texts)
            
            # Prepare vectors for insertion
            vectors = []
            for i, (text, metadata) in enumerate(chunks):
                vec_id = f"bl_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
                vectors.append((vec_id, embeddings[i], text, metadata))
            
            # Upsert to vector DB
            self.vector_db.upsert_vectors(vectors)
            
            # Move to processed directory
            self._mark_as_processed(filepath)
            
            logger.info(f"Processed {len(chunks)} B/L records from {filepath}")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error processing B/L file {filepath}: {str(e)}")
            return 0
    
    def _mark_as_processed(self, filepath: str):
        """Move processed file to processed directory"""
        try:
            filename = os.path.basename(filepath)
            processed_path = os.path.join(self.processed_dir, filename)
            os.rename(filepath, processed_path)
            logger.debug(f"Moved {filename} to processed directory")
        except Exception as e:
            logger.error(f"Error moving file to processed: {str(e)}")

def main():
    """Main entry point"""
    try:
        pipeline = ETLPipeline()
        pipeline.process_raw_data_files()
    except Exception as e:
        logger.critical(f"ETL Pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
