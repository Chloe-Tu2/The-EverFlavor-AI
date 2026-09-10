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
