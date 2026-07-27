# R16 7B QLoRA Training — Google Colab Guide

**Tijd:** 2-3 uur
**Kosten:** Gratis
**GPU:** NVIDIA T4 (15GB VRAM)

## Stap 1: Upload dataset naar Colab

Optie A — Direct upload:
```
1. Open https://colab.research.google.com
2. Nieuw notebook → Code cell
3. Run:
   from google.colab import files
   uploaded = files.upload()
4. Selecteer: r15-merged-sft.jsonl
```

Optie B — Via GitHub (als repo public is):
```
!wget https://raw.githubusercontent.com/djimitflo/openmythos-benchmark/main/analysis/openmythos-apex-runs/datasets/r15-merged-sft.jsonl
```

## Stap 2: GPU instellen

```
Runtime → Change runtime type → Hardware accelerator: GPU → Save
```

Verifieer:
```python
import torch
print(torch.cuda.is_available())  # True
print(torch.cuda.get_device_name(0))  # Tesla T4
```

## Stap 3: Copy-paste dit in een cell en run

```python
# === Install ===
!pip install -q unsloth transformers datasets trl accelerate bitsandbytes

# === Load model ===
from unsloth import FastLanguageModel
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit",
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=32, lora_alpha=64, lora_dropout=0.05,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    bias="none",
)
print("Model loaded!")

# === Load data ===
from datasets import load_dataset
dataset = load_dataset("json", data_files="/content/r15-merged-sft.jsonl", split="train")
dataset = dataset.map(lambda x: {"text": f"### Instruction:\n{x['instruction']}\n\n### Response:\n{x['output']}"})
print(f"Dataset: {len(dataset)} examples")

# === Train ===
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model=model, tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=2048,
    args=TrainingArguments(
        output_dir="./output",
        num_train_epochs=5,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        warmup_steps=20,
        logging_steps=10,
        save_steps=50,
        fp16=True,
        optim="adamw_8bit",
        report_to="none",
    ),
)

trainer.train()

# === Save & Download ===
model.save_pretrained("/content/openmythos-r16-7b")
tokenizer.save_pretrained("/content/openmythos-r16-7b")

from google.colab import files
import shutil
shutil.make_archive("/content/r16", "zip", "/content/openmythos-r16-7b")
files.download("/content/r16.zip")
```

## Stap 4: Download & Deploy

1. Unzip `r16.zip` op je Mac
2. Convert naar GGUF:
   ```bash
   # Install llama.cpp
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp && make
   
   # Convert
   python convert_hf_to_gguf.py ../openmythos-r16-7b --outtype q4_k_m --outfile openmythos-r16.gguf
   
   # Deploy in Ollama
   cat > Modelfile << EOF
   FROM ./openmythos-r16.gguf
   PARAMETER stop <|im_end|>
   PARAMETER temperature 0.1
   EOF
   
   ollama create openmythos-r16 -f Modelfile
   ollama run openmythos-r16 "Your question here"
   ```

## Verwachte resultaten

| Metric | R12 (3B) | R16 (7B) |
|--------|----------|----------|
| APEX Score | 3.009 | 3.5-3.8 (expected) |
| Pass Rate | 32.5% | 45-55% (expected) |
| Training Time | 7 min | 2-3 hours |
| Model Size | 3.3 GB | ~6 GB |

## Troubleshooting

| Probleem | Oplossing |
|----------|-----------|
| Out of memory | Verlaag batch_size naar 2 |
| CUDA not available | Runtime → Change runtime type → GPU |
| Slow training | Normaal op T4, ~10s/step |
| Download fails | Gebruje `!zip -r r16.zip /content/openmythos-r16-7b` |
