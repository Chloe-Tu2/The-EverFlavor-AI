# Food Photos on a Separate PC: Setup Plan

Preparation only: the photo feature has its own plan and will run on a stronger PC. Nothing here changes
the current code. Checked October 2026 on <https://ollama.com/search?c=vision>.

## Two different jobs

| Job | Tool | Status |
|---|---|---|
| **Fresh / aging / spoiled from a photo** (the measured answer) | Notebook 05's trained image models (one per food group), on a GPU | Data ready; training waits for a GPU |
| **Describe or explain a photo in words** ("the banana skin has brown patches") | A vision language model in Ollama | This page |

The trained models stay the source of the freshness verdict: a general vision model has not been measured
on our labels and can be confidently wrong. The vision model explains, or gives a second opinion, and
the same rule as the recipes applies: the code decides, the model explains.

## Which Ollama model

| Model | Download | Reads images | Calls tools | For |
|---|---|---|---|---|
| **`qwen3.8:27b`** (first choice) | 18 GB | Yes (also video, documents) | Yes | Newest Qwen vision model; can be one of the CrewAI agents too |
| `qwen3.6:35b` | 24 GB | Yes | Yes | Alternative; its chart file name suggests a mixture-of-experts model with about 3B active parameters, which would make it fast for its size (not confirmed) |
| `minicpm-v4.5:8b` | about 5-6 GB | Yes | No | If the photo PC has a smaller GPU |
| `gemma3:4b` (already on the laptop) | 3.3 GB | Yes | No | Quick tests only |

**Hardware for the first choice:** a GPU with 24 GB of memory (RTX 3090 / 4090 class), or a Mac with 32 GB
or more of unified memory. Ollama runs the model on the CPU when it does not fit, which is far too slow.
Licenses are not shown on Ollama's pages: read the model card on Hugging Face before the team uses it.

## Setup steps on the photo PC

1. Install Ollama (<https://ollama.com/download>) and the project (`git clone`, then
   `pip install -r config/requirements-app.txt`).
2. `ollama pull qwen3.8:27b`, then check: `ollama run qwen3.8:27b "Describe this photo" ./banana.jpg`.
3. Notebook 05 with `TRAIN = True` trains the freshness models on the same PC's GPU.
4. **Before choosing the model for good, measure it:** on notebook 05's held-out test photos, ask each
   candidate "fresh, aging or spoiled?" and compare with the labels (accuracy per food group, and how often
   it disagrees with the trained model). Pick by those numbers, not by size or popularity.
5. On the laptop, `llm.ollama_url()` can point to the photo PC (`OLLAMA_HOST=<pc address>:11434` in
   `config/.env`) so the same code uses the stronger models over the network.

## Open decisions (for the photo plan)

- Which food groups first (notebook 05 has fruit, meat and fish).
- Whether the vision model only explains, or also votes when the trained model is unsure.
- Privacy: photos stay on the team's own PC (another reason to run Ollama locally).
