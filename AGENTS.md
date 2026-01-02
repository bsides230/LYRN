# LYRN-AI Project Architectural Rules

This file contains critical architectural rules that must be followed during development.


 - Always Version the LYRN_GUI from v*.* to v*.* , or v*.*.* example v6.1 to v6.2 and then save the old version to deprecated/Old/ in the directory

 - Always update the build_notes.md file with detailed notes about the work done in the update. This should include a section on logging.
 
 - All python dependencies should be added to the `dependencies/requirements.txt` file.
 
 - This system was designed after 90s text based game parser scripts and the simplicity of those triggers. We bring that same energy to this system.
 
 - Remember in this design we are building cognition for AI. We are building this with simplicty in mind. For example, no crazy coding to complete a function that just requires a file to be watched and the text pulled from formatted blocks. The llm does most of the heavy lifting. This system just moves files and data around dumbly. The affordances are just going to be simple triggers using the similar logic.

---
## Parser Contract (v1.0)

### Global rules

- **Markers:** Every block begins with `###<BLOCK>_START###` and ends with `###_END###` (exact, uppercase).
- **Enable switch:** The first logical field in each block MAY be `ENABLED=true|false`. If `false`, parsers MUST ignore the remainder of that block until `###_END###`.
- **Key:Value lines:** Fields are `KEY: value` on single lines. Booleans are `true|false`. Integers are base‑10. Times are ISO‑8601 UTC (`YYYY‑MM‑DDTHH:MM:SSZ`).
- **Arrays:** When present inline, arrays MUST be JSON (e.g., `["alpha","beta"]`), not comma lists.
- **Heredoc values:** Use `<<EOF`; the value is the following lines until a lone `EOF` on its own line.
- **No tabs:** Parsers MUST treat TAB as invalid; use spaces only.
- **Whitespace:** Parsers MUST trim trailing spaces but preserve interior whitespace of heredocs.
- **Order:** Block order is stable but not required by parsers. Within a block, field order is not significant.
---

## The LYRN Philosophy and Vision

This section provides insight into the core principles and long-term vision of the LYRN project. It is intended to help future developers and AI agents understand the "why" behind the architecture, not just the "how".

### Core Philosophy

LYRN is built on a philosophy that diverges significantly from mainstream LLM development. Instead of relying on ever-larger models and prompt injection, LYRN emphasizes **structured, live memory** to achieve genuine continuity, identity, and context. The core tenets are:

-   **Efficiency and Accessibility:** The primary goal is to create a powerful AI cognition framework that is lightweight enough to run on mobile, CPU-only hardware, completely offline. This is achieved through a ruthless focus on token efficiency.
-   **Structured Memory over Prompt Injection:** All core context—personality, memory, goals—lives in structured text files and memory tables. The LLM reasons from this stable foundation rather than having it repeatedly injected into a limited context window.
-   **Symbolic Reference:** The system avoids redundant tokenization by design. For example, in the Gamemaster system, a template for a new object is instantiated by passing only a template ID and a pipe-separated string of *values*. The LLM uses a central index to map these values to the correct fields, never needing to re-tokenize the field names.
-   **Simplicity and Robustness:** The architecture is inspired by the simplicity of 1990s text-based game parsers. The framework's job is to be a robust, simple system for moving data; the LLM's job is to do the heavy lifting of reasoning.

### The "Why": The Driving Motivation

The LYRN project was born from a single, driving goal: to solve the context bloat and statelessness problems that make most AI interactions feel repetitive and forgetful. The aim was to create a truly continuous and stateful AI companion that could be run by almost anyone, on readily available hardware, without a constant internet connection. It's an architecture built for persistence, presence, and partnership.

### Key Architectural Concepts

These are the pillars that support the LYRN philosophy:

-   **The Identity Core:** This is the stable, foundational layer that defines the AI's personality, ethical boundaries, and purpose. It is loaded into the LLM's KV cache and referenced, not constantly re-injected, providing a consistent anchor for all reasoning.
-   **The Heartbeat Cycle:** A secondary cognitive loop that runs between user interactions. It analyzes the recent dialogue, updates memory tables, and adapts the AI's internal state autonomously, allowing the system to learn and evolve without interrupting the conversational flow.
-   **The Snapshot & Delta System:** This is the core of LYRN's efficiency. Static "snapshots" of the core context are cached for speed. Any dynamic changes (e.g., a user adjusting the AI's personality) are recorded as "deltas" in a manifest file. The LLM is instructed to treat these deltas as high-priority overrides, enabling real-time adaptability without the cost of rebuilding the entire context.
-   **True Model-Agnosticism:** The framework is designed to be compatible with a wide variety of LLMs. It achieves this by stripping the model's native chat format and using its own standardized structure, allowing for consistent performance across different models and sizes.

### Future Vision

LYRN is not just a framework; it's the foundation for much larger ambitions. The architecture was designed to enable two major future projects:

1.  **A Multi-Agent Dashboard:** A visual interface, imagined as a security camera manager, where each "cam feed" is a containerized LYRN agent. This dashboard will allow for the command and control of multiple agents, both local and remote, leveraging LYRN's simple, text-based nature for communication.
2.  **A Generative World Engine:** A system for creating vast, detailed, and persistent worlds for gaming, simulation, or even real-world mapping. This is not a pre-written world database; it's a true generative engine. The world is created on the fly as the user explores it. When a user interacts with an object, the LLM is triggered to "lazy load" its details by filling out a template based on the rich, hierarchical context of the player's location. The world itself is an emergent property of the LLM's interaction with the template system.