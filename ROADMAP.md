# Development Roadmap

This document outlines the future trajectory of the OSRS Smart Bot Framework, moving from a single-purpose script to a fully-fledged, community-driven automation client.

## Phase 1: Modern GUI & UX (Upcoming)
Currently, the bot relies on a PowerShell terminal and keyboard interrupts. 
*   **Target:** Build a sleek, dark-mode desktop app using `CustomTkinter` or `PyQt6`.
*   **Features:**
    *   Start/Stop/Pause buttons.
    *   Live video feed of the bot's vision processing (bounding boxes drawn over the game in real-time).
    *   Configuration toggles (Auto-eat, Runtime limits, Break frequency) built into a settings panel rather than console prompts.
    *   Live integration of the Telemetry Dashboard directly into the main app.

## Phase 2: The Community API
The goal is to allow anyone to write a script for this bot without needing to understand OpenCV or vector math.
*   **Target:** Decouple the "Vision Engine" from the "Logic Scripts".
*   **Features:**
    *   Provide simple commands like `bot.walk_to_color("cyan")` or `bot.wait_until_idle()`.
    *   Create a `scripts/` folder where users can drop in community-made Python files (e.g., `motherlode_mine.py`, `agility_rooftops.py`).
    *   Standardize the JSON Telemetry so community scripts automatically populate the dashboard with XP/hr and efficiency metrics.

## Phase 3: Advanced Machine Learning & OCR
As the framework matures, we will push past simple color detection into actual machine learning.
*   **Target:** Make the bot "aware" of its surroundings.
*   **Features:**
    *   **Chat Reading:** Use Tesseract to monitor the chat box for player messages (to auto-reply or hop worlds if crashed) and level-up messages (to calculate XP/hr).
    *   **YOLO Object Detection:** Train a lightweight YOLO model to detect specific NPCs, Bank Booths, or obstacles, completely eliminating the need for manually placed RuneLite tile markers.
    *   **Random Event Solver:** Use OCR and image classification to recognize when a random event NPC appears and either interact with it or safely ignore/dismiss it.

## Phase 4: Cloud Supervisor
For lower-end machines that cannot run heavy ML models locally.
*   **Target:** A lightweight API connector.
*   **Features:** 
    *   When the bot encounters an unknown state, it uploads a screenshot to a cloud LLM (like GPT-4o or Gemini).
    *   The LLM acts as a remote supervisor, telling the bot exactly how to recover.
