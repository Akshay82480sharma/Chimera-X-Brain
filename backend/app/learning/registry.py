import os
import json
from datetime import datetime, timezone, timedelta
from app.learning.config import learning_settings

def register_model(model_name: str, version: str, loss: float, samples: int):
    """
    Saves metadata about a trained model version into the local registry.
    """
    version_dir = os.path.join(learning_settings.registry_dir, model_name, version)
    os.makedirs(version_dir, exist_ok=True)
    
    IST = timezone(timedelta(hours=5, minutes=30))
    metadata = {
        "model_name": model_name,
        "version": version,
        "training_date": datetime.now(IST).isoformat(),
        "loss": loss,
        "samples_trained": samples
    }
    
    meta_path = os.path.join(version_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
        
    # Also update 'latest' symlink/copy conceptually
    latest_dir = os.path.join(learning_settings.registry_dir, model_name, "latest")
    os.makedirs(latest_dir, exist_ok=True)
    with open(os.path.join(latest_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
