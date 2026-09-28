import os
from pydantic_settings import BaseSettings

class LearningSettings(BaseSettings):
    # Paths
    base_data_dir: str = os.path.join(os.getcwd(), "data")
    dataset_dir: str = os.path.join(base_data_dir, "datasets")
    registry_dir: str = os.path.join(base_data_dir, "models")
    
    # Thresholds
    confidence_threshold: int = 80
    
    # Training Config
    training_model: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    max_cpu_threads: int = 4
    max_memory_mb: int = 4096
    
    # Future extension points (e.g., GraphRAG toggles)
    enable_graph_rag: bool = False
    
learning_settings = LearningSettings()
