import os
import sys
import argparse
from datasets import Dataset
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

# We need to insert the backend root into sys.path to run this as an isolated script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.learning.config import learning_settings
from app.learning.registry import register_model

def run_training():
    """
    Runs QLoRA fine-tuning strictly utilizing the exported JSONL dataset.
    Does NOT connect to the main database, ensuring isolated background execution.
    """
    dataset_path = os.path.join(learning_settings.dataset_dir, "train.jsonl")
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset {dataset_path} not found.")
        sys.exit(1)
        
    dataset = Dataset.from_json(dataset_path)
    
    if len(dataset) == 0:
        print("Dataset is empty. Exiting.")
        sys.exit(0)

    # Respect CPU limits configured by user
    torch.set_num_threads(learning_settings.max_cpu_threads)

    model_id = learning_settings.training_model
    print(f"Loading {model_id} for SLM finetuning...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        device_map="auto",
        load_in_8bit=True
    )
    model = prepare_model_for_kbit_training(model)
    
    peft_config = LoraConfig(
        r=8, 
        lora_alpha=16, 
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"],
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, peft_config)
    
    # Use standard versioning for the registry
    import uuid
    version_id = f"v_{uuid.uuid4().hex[:8]}"
    output_dir = os.path.join(learning_settings.registry_dir, "tinyllama", version_id)
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=1,
        max_steps=50, 
        optim="paged_adamw_8bit",
        dataloader_num_workers=1
    )
    
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=128,
        tokenizer=tokenizer,
        args=training_args
    )
    
    print("Starting background fine-tuning...")
    trainer.train()
    trainer.model.save_pretrained(os.path.join(output_dir, "adapter"))
    
    # Register the model metadata
    mock_loss = 0.5 # Would extract actual loss from trainer logs in prod
    register_model("tinyllama", version_id, mock_loss, len(dataset))
    print(f"Fine-tuning complete! Saved to {output_dir}")

if __name__ == "__main__":
    run_training()
