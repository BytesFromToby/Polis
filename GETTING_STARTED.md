# Getting Started with Polis

This guide covers installation, configuration, and how to run the simulation.

## Prerequisites

- **Python:** 3.13+ required (the engine uses features exclusive to this version).
- **Node.js:** 18+ (only needed if you want to build/run the browser UI).
- **(Optional) API Keys:** If you want live LLM negotiations. The game runs fully offline with the built-in stub.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/BytesFromToby/Polis
    cd polis
    ```

2.  **Install Backend Dependencies:**
    We use `pip` for Python packages.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Frontend Dependencies:**
    ```bash
    cd frontend
    npm install
    cd ..
    ```
4. **Start the backend Server:** (Use this to start the game every time)
    ```bash
    cd backend 
    py -m uvicorn api.server:app --reload
    ```
5. **Play in browser:**
    In browser, Open **http://localhost:8000**
    Click **New Game**
    Name yourself and your city, and **Start**.

## Configuration the Live LLMs

1. Once in game, click **Settings**
2. Click **Add Profile**
3. Choose a provider and fill out model and API information
4. Click **Add Profile**
    - Suggest using the **Test** feature
5. Choose your profile for the active city and click **Apply**
    - Recommend setting a default profile for new games. 

* 🎮 **[How to Play](./HOW_TO_PLAY.md)** — Learn the rules of negotiation, faction dynamics, and the cycle loop.