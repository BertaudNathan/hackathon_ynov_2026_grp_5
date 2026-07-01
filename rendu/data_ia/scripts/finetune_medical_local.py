#!/usr/bin/env python3
"""
Fine-tuning LoRA du modèle médical expérimental, en local (équivalent de
medical_project/finetune_medical_colab.ipynb, adapté pour tourner sur un
GPU local de 8 Go de VRAM plutôt que sur Colab).
"""

import json
import os
from pathlib import Path

import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig,
    TrainingArguments, Trainer, DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from datasets import Dataset

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "datasets" / "cleaned" / "medical_dataset_sample.json"
OUTPUT_DIR = BASE_DIR / "medical_project" / "phi35_medical_lora"
METRICS_PATH = BASE_DIR / "medical_project" / "training_metrics.json"

BASE_MODEL = "microsoft/Phi-3.5-mini-instruct"

TEST_QUESTIONS = [
    "I have had a headache and mild fever for two days, what could it be?",
    "What are common side effects of ibuprofen?",
    "How much water should I drink daily?",
]


def load_data():
    with open(DATASET_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    max_examples = os.environ.get("MAX_EXAMPLES")
    if max_examples:
        raw = raw[: int(max_examples)]
    print(f"{len(raw)} exemples chargés depuis {DATASET_PATH}")
    texts = [
        {"text": f"<|user|>\n{x['instruction']}<|end|>\n<|assistant|>\n{x['output']}<|end|>"}
        for x in raw
    ]
    return Dataset.from_list(texts)


def load_model_and_tokenizer():
    print(f"Chargement du modèle de base : {BASE_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )
    model = prepare_model_for_kbit_training(model)
    model.gradient_checkpointing_enable()

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["qkv_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.1,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return tokenizer, model


def main():
    dataset = load_data()
    tokenizer, model = load_model_and_tokenizer()

    def tokenize_function(examples):
        tokenized = tokenizer(
            examples["text"], truncation=True, padding="max_length", max_length=512
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=["text"])

    # Budget mémoire adapté à un GPU 8 Go (batch réel effectif = 1 x 8 = 8)
    training_args = TrainingArguments(
        output_dir=str(BASE_DIR / "medical_project" / "checkpoints"),
        num_train_epochs=float(os.environ.get("NUM_EPOCHS", 3)),
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        warmup_steps=50,
        logging_steps=25,
        save_steps=1000,
        save_total_limit=1,
        remove_unused_columns=False,
        fp16=True,
        report_to="none",
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        processing_class=tokenizer,
        data_collator=data_collator,
    )

    trainer.train()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    log_history = trainer.state.log_history
    with open(METRICS_PATH, "w") as f:
        json.dump(log_history, f, indent=2)

    losses = [(e["epoch"], e["loss"]) for e in log_history if "loss" in e]
    if losses:
        print(f"Loss initiale: {losses[0][1]:.4f} -> Loss finale: {losses[-1][1]:.4f}")
        print(f"Epochs: {losses[-1][0]:.2f}")

    print("\n=== Test rapide ===")
    model.eval()
    for q in TEST_QUESTIONS:
        formatted = f"<|user|>\n{q}<|end|>\n<|assistant|>\n"
        inputs = tokenizer(formatted, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=150,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
            )
        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )
        print(f"\nQ: {q}\nR: {response}")

    print(f"\n✅ Adaptateur sauvegardé dans {OUTPUT_DIR}")
    print(f"✅ Métriques sauvegardées dans {METRICS_PATH}")


if __name__ == "__main__":
    main()
