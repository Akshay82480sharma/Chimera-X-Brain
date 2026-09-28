import asyncio
from typing import List, Dict, Any
from app.retrieval.vector_store import vector_store

class RetrievalService:
    @staticmethod
    async def get_relevant_memories(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Queries the vector store for semantic matches to the user's input.
        Returns a list of dictionaries with 'document' (the memory string) and 'metadata'.
        """
        # Execute the synchronous chroma query in a thread to avoid blocking the event loop
        results = await asyncio.to_thread(
            vector_store.search_memories,
            query=query,
            n_results=max_results
        )
        
        # Filter out low-confidence matches (ChromaDB uses L2 distance by default, lower is closer)
        # Assuming a basic threshold, this can be tuned based on the embedding model
        # For all-MiniLM-L6-v2, distances > 1.5 might be irrelevant
        filtered_results = []
        for match in results:
            if match["distance"] < 1.5:
                filtered_results.append(match)
                
        return filtered_results

    @staticmethod
    async def get_relevant_graph_context(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Queries the vector store for semantic matches to the user's input in the entities collection.
        """
        results = await asyncio.to_thread(
            vector_store.search_entities,
            query=query,
            n_results=max_results
        )
        
        filtered_results = []
        for match in results:
            if match["distance"] < 1.5:
                filtered_results.append(match)
                
        return filtered_results

    @staticmethod
    async def get_relevant_agent(query: str) -> Dict[str, Any]:
        """
        Queries the vector store for the single most relevant agent.
        """
        results = await asyncio.to_thread(
            vector_store.search_agents,
            query=query,
            n_results=1
        )
        
        # Stricter threshold for agents to avoid false positives
        if results and results[0]["distance"] < 1.4:
            return results[0]
                
        return None

    @staticmethod
    async def get_relevant_skills(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Queries the vector store for semantic matches to the user's input in the skills collection.
        """
        results = await asyncio.to_thread(
            vector_store.search_skills,
            query=query,
            n_results=max_results
        )
        
        filtered_results = []
        for match in results:
            if match["distance"] < 1.4:  # Slightly strict threshold for skills
                filtered_results.append(match)
                
        return filtered_results
