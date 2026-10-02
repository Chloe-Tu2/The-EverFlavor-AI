# The-EverFlavor-AI

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-FF6B35)
![Gradio](https://img.shields.io/badge/Gradio-Chat%20Interface-F97316)
![LLM](https://img.shields.io/badge/LLM-Groq%20%7C%20LLaMA%203.1-00A67E?logo=meta&logoColor=white)
![Multi-Agent](https://img.shields.io/badge/Architecture-Multi--Agent%20System-crimson)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![ITAI2277](https://img.shields.io/badge/ITAI%202277-Capstone%20Project-blueviolet)
![Project](https://img.shields.io/badge/Project%20Tier-Advanced%20%7C%20Agentic%20AI-gold)

**Multi-Agent Diet & Discovery System**

> A conversational multi-agent AI that helps users create authentic global recipes while respecting calorie limits, dietary restrictions, and ingredient availability — then finds the nearest specialty supermarket.

---

## Overview

**EverFlavor AI** solves everyday decision fatigue around food. Users simply talk to the system in natural language, for example:

> “I have 550 calories left, no pork, I’m tired after work, and I want something bold from Middle Eastern or Latin American cuisine. I can drive 15 minutes.”

The system returns:
- A complete step-by-step recipe from one of five major cuisine families
- Smart ingredient substitutions
- Accurate calorie & nutrition information
- The nearest specialty supermarket for that cuisine
- Full respect for religious, medical, and ethical restrictions

---

## Key Features

- **Multi-Agent Architecture** with three specialized agents
- Support for **5 major global cuisine families**:
  - Asian
  - European
  - Latin American
  - African
  - Middle Eastern
- Smart ingredient substitutions
- Hard-coded safety filter for dietary restrictions (cannot be overridden by the LLM)
- Real specialty store search via Google Places API
- Nutrition grounded in Open Food Facts + USDA FoodData Central
- Human-in-the-Loop safety gates
- Gradio chat interface for easy demonstration

---

## Architecture

### Three Specialized Agents

| Agent                        | Responsibility                                      |
|-----------------------------|-----------------------------------------------------|
| **Nutritionist & Preference Agent** | Extracts calories, restrictions, cuisine preference, and driving radius |
| **Chef Agent**                   | Generates authentic recipes + practical substitutions |
| **Sourcing Agent**               | Finds the nearest specialty supermarket             |

**Orchestration:** Sequential workflow using CrewAI with shared context and an independent safety filter that runs after recipe generation.

---

## Tech Stack

- **Language:** Python 3.10+
- **Multi-Agent Framework:** CrewAI
- **Interface:** Gradio
- **LLM:** Groq (LLaMA 3.1) or compatible tool-calling model
- **APIs:**
  - Open Food Facts
  - USDA FoodData Central
  - Google Places API
- **Safety:** Hard-coded post-generation restriction filter

---

## Project Scope (Prototype)

- Five major cuisine families only
- One metro area for store search (e.g., Houston)
- Session-based user profiles
- Clear substitution logic
- Full restriction handling (religious, medical, ethical)

---

## Project Structure

```
The-EverFlavor-AI/
├── notebooks/
│   └── 01_data_acquisition_EverFlavor_V3.ipynb   # Weeks 4-6: data acquisition, preprocessing, EDA, baseline
├── data/
│   ├── raw/          # Original downloads and samples (generated, not committed)
│   ├── interim/      # Partially cleaned data (generated, not committed)
│   └── processed/    # Train/val/test splits and plots (generated, not committed)
├── src/              # Agent code (to come)
├── docs/
│   └── proposal/     # Capstone proposal slides and Phase 1 document (PDF)
├── config/
│   ├── requirements.txt  # Python libraries for the notebook
│   └── .env.example      # Template for API keys (copy to config/.env, which git ignores)
├── .gitignore
├── LICENSE
└── README.md
```

---

## Current Status

**Done (Weeks 4-6):** data collected from USDA FoodData Central, Open Food Facts, Food.com (Kaggle), and Hugging Face; cleaning and feature engineering (cuisine family, dietary flags, calories per serving, ingredient lists, complexity); stratified train/validation/test split; exploratory analysis; and a rule-based baseline recommender.

**Known data gaps:**
- The Hugging Face dataset has no African cuisine label, so the African family has no recipes yet. CulinaryDB or RecipeDB are planned to fill this.
- Food.com has no cuisine column; cuisine still needs to be inferred from its tags.
- Food.com reports fat, protein, and carbs only as percent of daily value, not grams.
- Food.com dietary flags come from ingredient keywords, so they are approximate.

**Next:** Week 7 model development, then the CrewAI agents, Google Places integration, and the Gradio interface.

---

## Running the Notebook

`notebooks/01_data_acquisition_EverFlavor_V3.ipynb` runs in Google Colab, VS Code, and Antigravity. Its setup cell (section 2.3) detects the environment, moves to the project folder, and loads API keys from the right place.

### Google Colab

1. Open the notebook in Colab.
2. Click the key icon in the left sidebar and add a secret named `USDA_API_KEY` ([get a free key](https://fdc.nal.usda.gov/api-guide.html)). Switch on **Notebook access**.
3. Run all cells.

### VS Code or Antigravity

1. Install the **Python** and **Jupyter** extensions.
2. In a terminal in the project folder, run `pip install -r config/requirements.txt`.
3. Copy `config/.env.example` to `config/.env` and fill in `USDA_API_KEY`. Git ignores `.env`, so your keys are never pushed.
4. Open the notebook, pick the Python interpreter you installed into as the kernel, and run all cells.

After a kernel restart, run the cells in sections 2.2 and 2.3 again before any later section.

Generated data files in `data/` are not committed; the notebook recreates them.

---
