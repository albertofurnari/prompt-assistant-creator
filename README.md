# Prompt Assistant Creator (PAC)

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python)
![Code Style](https://img.shields.io/badge/Code%20Style-Black%20%7C%20Ruff-black?style=for-the-badge)
![Type Checking](https://img.shields.io/badge/Type%20Checker-Mypy-blueviolet?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
[![Sponsor](https://img.shields.io/badge/Sponsor-GitHub-ea4aaa?style=for-the-badge&logo=github)](https://github.com/sponsors/albertofurnari)

> **Engineering over Guesswork.**
> Un tool CLI per trasformare il Prompt Engineering da arte empirica a processo deterministico, strutturato e tipizzato.

## 📋 Manifesto

La maggior parte dei prompt sono "black box" assemblate frettolosamente. **Prompt Assistant Creator** applica i principi del Software Engineering alla generazione di prompt:

1.  **Atomicità:** Ogni componente del prompt (Ruolo, Intento, Vincoli) è isolato, ottimizzato e validato singolarmente.
2.  **Type Safety:** L'intero flusso è governato da modelli **Pydantic** rigorosi. Nessuna gestione di dizionari non strutturati.
3.  **Coerenza Semantica:** Un `GlobalHarmonizer` finale assicura che le parti assemblate non creino conflitti logici, levigando le transizioni.
4.  **Developer Experience:** Interfaccia CLI basata su **Rich** per iterazioni rapide senza context-switch dal terminale.

---

## 🏗 Architettura

Il sistema non è un semplice template engine. È una **State Machine** che guida l'utente attraverso un ciclo di raffinamento iterativo e misurabile.

```mermaid
graph TD
    User((User)) -->|Input Draft| Engine[PromptOptimizerEngine]
    Engine -->|State Transition| Step{Optimization Step}
    
    subgraph "Core Logic"
    Step -->|Analyze| LLM[LLM Client]
    LLM -->|Feedback| Analysis[AnalysisResult Model]
    Analysis -->|Review| User
    end
    
    User -->|Approve| Session[PromptSession State]
    Session -->|Next Step| Step
    
    Session -->|Finalize| Harmonizer[Global Harmonizer]
    Harmonizer -->|Smoothing| Output[Final Markdown Prompt]
````

### Componenti Chiave

  * **`PromptOptimizerEngine`**: Il cuore del sistema. Gestisce le transizioni di stato e l'orchestrazione dei feedback.
  * **`OptimizationStep` (Enum)**: Definisce la pipeline rigida (Intent → Role → Goal → Context → Audience → Key Points → Constraints → Output).
  * **`GlobalHarmonizer`**: Un agente specializzato che rilegge l'intero contesto della sessione per eliminare ridondanze e migliorare la fluidità sintattica prima dell'output.
  * **Abstraction Layer**: Supporto plug-and-play per `OpenAILLMClient`, `GeminiLLMClient` e `MockLLMClient` (per testing deterministico offline).

-----

## 🚀 Quick Start

### Prerequisiti

  * Python 3.11+
  * API Key (OpenAI o Google Gemini)

### Installazione

```bash
# Clona il repository
git clone [https://github.com/albertofurnari/prompt-assistant-creator.git](https://github.com/albertofurnari/prompt-assistant-creator.git)
cd prompt-assistant-creator

# Crea virtualenv e installa dipendenze
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate su Windows
pip install -r requirements.txt
```

### Configurazione

Crea un file `.env` nella root del progetto:

```ini
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
# Opzionale: Configurazione modello default
DEFAULT_MODEL=gpt-5
```

### Utilizzo

Lancia l'ottimizzatore interattivo:

```bash
python optimizer.py
```

Il tool avvierà la UI testuale. Segui la procedura guidata per definire iterativamente ogni sezione del prompt, ricevendo feedback in tempo reale dall'LLM selezionato.

-----

## 🛠 Stack Tecnologico & Toolchain

Il progetto adotta standard di sviluppo enterprise per garantire manutenibilità e robustezza:

  * **Runtime:** Python 3.11+
  * **UI/UX:** [Rich](https://github.com/Textualize/rich) per il rendering terminale avanzato, [Prompt Toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) per input multiriga.
  * **Data Validation:** [Pydantic](https://www.google.com/search?q=https://docs.pydantic.dev/) per la modellazione di stati, telemetria e configurazione.
  * **Quality Assurance:**
      * `pytest` + `VCRpy` per test di regressione e registrazione/mocking delle chiamate API.
      * `Hypothesis` per il property-based testing.
      * `Ruff` & `Black` per linting e formattazione rigorosa.
      * `Mypy` per static type checking.

-----

## 🤝 Contributing

Il progetto nasce come iniziativa **Code in Public**.
Se sei un System Engineer, un Backend Dev o un AI Engineer interessato a rendere il prompting un processo deterministico:

1.  Forka il repo.
2.  Apri una Issue per discutere un miglioramento architetturale o una feature.
3.  Invia una PR.

*Ogni contributo che aumenta la robustezza o riduce l'entropia del sistema è benvenuto.*

-----

## 👤 Author

**Alberto Furnari**

  * Senior System Engineer | AI Technical Lead
  * [LinkedIn](https://www.linkedin.com/in/alberto-furnari-97695028)

<!-- end list -->

```
