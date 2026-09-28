import os
import chromadb
from chromadb.config import Settings
import logging

logger = logging.getLogger(__name__)

# Ensure data directory exists
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma"))
os.makedirs(DATA_DIR, exist_ok=True)

class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        try:
            self.client = chromadb.PersistentClient(path=DATA_DIR)
            # Default embedding model is automatically used by Chroma
            self.memory_collection = self.client.get_or_create_collection(name="memories")
            self.entity_collection = self.client.get_or_create_collection(name="entities")
            self.agent_collection = self.client.get_or_create_collection(name="agents")
            self.skill_collection = self.client.get_or_create_collection(name="skills")
            logger.info(f"ChromaDB initialized at {DATA_DIR}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.memory_collection = None
            self.entity_collection = None
            self.agent_collection = None
            self.skill_collection = None

    def add_memory(self, memory_id: int, text: str, metadata: dict = None):
        if not self.memory_collection:
            return
            
        meta = {"memory_id": memory_id}
        if metadata:
            meta.update(metadata)
            
        try:
            self.memory_collection.upsert(
                documents=[text],
                metadatas=[meta],
                ids=[f"mem_{memory_id}"]
            )
        except Exception as e:
            logger.error(f"Failed to add memory to ChromaDB: {e}")

    def add_entity(self, entity_id: int, text: str, metadata: dict = None):
        if not self.entity_collection:
            return
            
        meta = {"entity_id": entity_id}
        if metadata:
            meta.update(metadata)
            
        try:
            self.entity_collection.upsert(
                documents=[text],
                metadatas=[meta],
                ids=[f"ent_{entity_id}"]
            )
        except Exception as e:
            logger.error(f"Failed to add entity to ChromaDB: {e}")

    def delete_memory(self, memory_id: int):
        if not self.memory_collection:
            return
            
        try:
            self.memory_collection.delete(ids=[f"mem_{memory_id}"])
        except Exception as e:
            logger.error(f"Failed to delete memory from ChromaDB: {e}")

    def search_memories(self, query: str, n_results: int = 5) -> list[dict]:
        if not self.memory_collection:
            return []
            
        try:
            results = self.memory_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            matches = []
            if results and results["documents"] and len(results["documents"]) > 0:
                for i in range(len(results["documents"][0])):
                    doc = results["documents"][0][i]
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0
                    
                    matches.append({
                        "document": doc,
                        "metadata": meta,
                        "distance": distance
                    })
            return matches
        except Exception as e:
            logger.error(f"Failed to search memories in ChromaDB: {e}")
            return []

    def search_entities(self, query: str, n_results: int = 5) -> list[dict]:
        if not self.entity_collection:
            return []
            
        try:
            results = self.entity_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            matches = []
            if results and results["documents"] and len(results["documents"]) > 0:
                for i in range(len(results["documents"][0])):
                    doc = results["documents"][0][i]
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0
                    
                    matches.append({
                        "document": doc,
                        "metadata": meta,
                        "distance": distance
                    })
            return matches
        except Exception as e:
            logger.error(f"Failed to search entities in ChromaDB: {e}")
            return []
    def add_agent(self, agent_id: int, text: str, metadata: dict = None):
        if not self.agent_collection:
            return
            
        meta = {"agent_id": agent_id}
        if metadata:
            meta.update(metadata)
            
        try:
            self.agent_collection.upsert(
                documents=[text],
                metadatas=[meta],
                ids=[f"agent_{agent_id}"]
            )
        except Exception as e:
            logger.error(f"Failed to add agent to ChromaDB: {e}")

    def search_agents(self, query: str, n_results: int = 1) -> list[dict]:
        if not self.agent_collection:
            return []
            
        try:
            results = self.agent_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            matches = []
            if results and results["documents"] and len(results["documents"]) > 0:
                for i in range(len(results["documents"][0])):
                    doc = results["documents"][0][i]
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0
                    
                    matches.append({
                        "document": doc,
                        "metadata": meta,
                        "distance": distance
                    })
            return matches
        except Exception as e:
            logger.error(f"Failed to search agents in ChromaDB: {e}")
            return []

    def add_skill(self, skill_id: int, text: str, metadata: dict = None):
        if not self.skill_collection:
            return
            
        meta = {"skill_id": skill_id}
        if metadata:
            meta.update(metadata)
            
        try:
            self.skill_collection.upsert(
                documents=[text],
                metadatas=[meta],
                ids=[f"skill_{skill_id}"]
            )
        except Exception as e:
            logger.error(f"Failed to add skill to ChromaDB: {e}")

    def search_skills(self, query: str, n_results: int = 5) -> list[dict]:
        if not self.skill_collection:
            return []
            
        try:
            results = self.skill_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            matches = []
            if results and results["documents"] and len(results["documents"]) > 0:
                for i in range(len(results["documents"][0])):
                    doc = results["documents"][0][i]
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0
                    
                    matches.append({
                        "document": doc,
                        "metadata": meta,
                        "distance": distance
                    })
            return matches
        except Exception as e:
            logger.error(f"Failed to search skills in ChromaDB: {e}")
            return []

# Singleton instance
vector_store = VectorStore()
