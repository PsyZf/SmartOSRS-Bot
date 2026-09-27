# OSRS Smart Bot Framework (Beta)

Welcome to the OSRS Smart Bot Framework! This project has evolved from a simple coordinate-clicking script into a robust, vision-based automation framework designed for stability, human-like behavior, and extensibility.

## 🚀 Core Features & Knowledge Base

### 1. Vision-Based Navigation
*   **Dynamic Minimap Tracking:** The bot no longer relies on hardcoded window offsets. It uses OpenCV to dynamically locate the exact center of the player's white dot on the minimap. You can move the RuneLite window anywhere on your screen.
*   **Color-Coded Routing:** Uses distinct HSV color markers for flawless navigation without complex vector math:
    *   **Magenta (`#FF00FF`):** Home Tile.
    *   **Cyan (`#00FFFF`):** Mid-waypoint (optional).
    *   **Blue (`#0000FF`):** Far turn-around point.
*   **Breadcrumb Recovery:** If the bot gets lost, it will follow a trail of Black markers one-by-one until it safely returns to the main route.

### 2. Intelligent Combat & Survival
*   **Dynamic Auto-Eat (Green Tags):** Instead of relying on hardcoded inventory slots, the bot scans the entire inventory for items highlighted with **Green Inventory Tags**. 
*   **Obstructing Interface Failsafe:** If the bot accidentally opens the World Map or Bank (detecting the massive red 'X' in the corner), it instantly presses `Escape` to close it.
*   **Inventory Tab Verification:** Before sipping a potion or searching for food, the bot verifies the inventory is open by clicking the Bag icon, ensuring it never gets stuck in the wrong tab.

### 3. Human-Like Anti-Ban Engine
*   **Global Cooldowns:** Anti-ban actions (mouse drifting, checking HP, hovering chat) share a global 45-120 second cooldown. It never fires robotic "bursts" of actions.
*   **HP Orb Verification:** When checking the HP orb, it takes a micro-screenshot of the pixels under the mouse. If the pixels aren't red, it realizes the client window moved and triggers an automatic re-calibration.

### 4. Smart Reconnect & OCR Failsafes
*   **70-Second Login Loop:** If disconnected, the bot scans the entire canvas for the Welcome Screen (Red 'Play' button) and the Login Screen (Gold 'Play Now' button).
*   **Debug Snapshots:** Silently saves pictures of what it sees during a disconnect (`debug_welcome_screen.png`) so you can review why a run failed.
*   **OCR Integration (Tesseract):** Reads the text on disconnect popups. If it reads "Account already logged in" or "Error connecting", it safely halts instead of looping forever.

### 5. Telemetry & Analytics
*   **JSON Logging:** All major events (disconnects, aggro resets, failsafes) are logged cleanly to `data/telemetry.jsonl`.
*   **Live Dashboard:** Run `python dashboard.py` alongside the bot for a live, scrolling GUI of the bot's internal state.

---

## 🛠️ Setup Instructions
1. Ensure RuneLite is set to **Fixed - Classic Layout**.
2. Install dependencies: `pip install -r requirements.txt`
3. Install Tesseract OCR using the provided `tesseract-installer.exe`.
4. Run the bot: `python smart_sand_crab_bot.py`
