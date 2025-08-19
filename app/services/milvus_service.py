import logging
import os
from typing import Optional, List, Dict, Any

import pandas as pd
from sentence_transformers import SentenceTransformer
from pymilvus import (
    connections, Collection, CollectionSchema, FieldSchema,
    DataType, utility, MilvusException, db
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class MilvusService:
    def __init__(self):
        self.host = os.getenv("MILVUS_HOST", "localhost")
        self.port = os.getenv("MILVUS_PORT", "19530")
        self.db_name = os.getenv("MILVUS_DB_NAME", "disease_db")
        self.collection_name = os.getenv("MILVUS_COLLECTION_NAME", "symptom_vectors")
        self.csv_path = os.getenv("SYMPTOM_CSV_PATH", "data/disease_symptoms.csv")
        self.embedding_dim = 384
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        self._ensure_connection()
        self._ensure_database()
        self._ensure_collection()
        self._insert_csv_if_needed()

    def _ensure_connection(self):
        """Establish connection to Milvus if not already connected"""
        try:
            if not connections.has_connection("default"):
                connections.connect(alias="default", host=self.host, port=self.port)
                logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            else:
                logger.info("Reusing existing Milvus connection")
        except MilvusException as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def _ensure_database(self):
        """Ensure the custom database exists"""
        try:
            if self.db_name not in db.list_database():
                db.create_database(self.db_name)
                logger.info(f"Created database: {self.db_name}")
            else:
                logger.info(f"Using existing database: {self.db_name}")
            db.using_database(self.db_name)
        except MilvusException as e:
            logger.error(f"Failed to create or verify database: {e}")
            raise

    def _ensure_collection(self):
        """Ensure symptom vector collection exists with proper schema"""
        try:
            if not utility.has_collection(self.collection_name):
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                    FieldSchema(name="disease", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="symptoms", dtype=DataType.VARCHAR, max_length=2048),
                    FieldSchema(name="specialist", dtype=DataType.VARCHAR, max_length=400),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                ]
                schema = CollectionSchema(fields, description="Disease symptom vector embeddings")
                self.collection = Collection(self.collection_name, schema)

                # Index for fast search
                self.collection.create_index(
                    "embedding",
                    {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}}
                )
                logger.info(f"Created new collection: {self.collection_name}")
            else:
                self.collection = Collection(self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")
        except MilvusException as e:
            logger.error(f"Failed to create or verify collection: {e}")
            raise

    def _is_collection_empty(self) -> bool:
        self.collection.load()
        return self.collection.num_entities == 0

    def _generate_embedding(self, text: str) -> List[float]:
        return self.embedder.encode(text).tolist()

    def _insert_csv_if_needed(self):
        """Insert CSV data into Milvus only if the collection is empty"""
        try:
            if self._is_collection_empty():
                logger.info("Collection is empty. Inserting CSV data.")
                self._insert_from_csv(self.csv_path)
            else:
                logger.info("Collection already has data. Skipping CSV insertion.")
        except Exception as e:
            logger.error(f"Failed during conditional CSV insert: {e}")
            raise

    def _insert_from_csv(self, file_path: str):
        """Read CSV and insert vector embeddings"""
        try:
            df = pd.read_csv(file_path)
            data_to_insert = []

            for idx, row in df.iterrows():
                symptoms = ", ".join(
                    str(value) for col, value in row.items()
                    if col.lower().startswith("symptom") and pd.notna(value)
                )
                disease_name = str(row["Disease"])
                specialist = str(row["specialist"])
                emb = self._generate_embedding(symptoms)

                data_to_insert.append({
                    "id": f"{disease_name}_{idx}",
                    "disease": disease_name,
                    "symptoms": symptoms,
                    "specialist": specialist,
                    "embedding": emb
                })

            self.collection.insert(data_to_insert)
            self.collection.flush()
            logger.info(f"Inserted {len(data_to_insert)} records into Milvus.")
        except Exception as e:
            logger.error(f"Failed to insert CSV data: {e}")
            raise

    def search_similar_diseases(self, symptoms: List[str], top_k: int = 5) -> List[Dict]:
        """Search for diseases based on symptom similarity"""
        try:
            self.collection.load()
            query_text = ", ".join(symptoms)
            emb = self._generate_embedding(query_text)

            results = self.collection.search(
                data=[emb],
                anns_field="embedding",
                param={"metric_type": "L2", "params": {"nlist": 10}},
                limit=top_k,
                output_fields=["disease", "symptoms","specialist"]
            )

            response = []
            for hits in results:
                for hit in hits:
                    response.append({
                        "disease": hit.entity.get("disease"),
                        "symptoms": hit.entity.get("symptoms"),
                        "specialist": hit.entity.get("specialist"),
                        "score": hit.score
                    })
            return response
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

# Initialize the service when module is imported
milvus_service = MilvusService()
