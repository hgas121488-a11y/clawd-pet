# clawd-pet
Интерактивный пиксельный питомец для рабочего стола Windows (PyQt6). Ест пиксели, летает и общается через нейросети (Claude, Gemini, OpenAI). Две версии: Original и Macrosink (2000+ фраз).

# 🤖 Clawd Desktop Pet

An interactive pixel-art pet for the Windows desktop built with **Python + PyQt6**. 
Clawd is not just a simple tamagotchi: he eats your pixels, poops, flies around, dances, and most importantly — he can communicate via AI (Claude, Gemini, OpenAI) and remember facts about you.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-UI-green?style=for-the-badge&logo=qt" alt="PyQt6">
  <img src="https://img.shields.io/badge/Windows-10/11-lightgrey?style=for-the-badge&logo=windows" alt="Windows">
</p>

---

## ⚠️ DISCLAIMER (READ BEFORE USE)

**AI Functionality is NOT Guaranteed:**
The AI chat and memory features rely on third-party APIs (Anthropic, Google, OpenAI, etc.). 
* We do **not** guarantee that the AI will always work perfectly. 
* The AI responses depend on your API key balance, regional restrictions, network connection, and provider rate limits (e.g., 429 Too Many Requests errors).
* If you use a cheap or restricted API proxy, the AI might fail to respond or crash. The pet will fall back to default pre-written phrases in case of an API failure, but we are not responsible for any API costs or bans.

---

## 📦 Two Independent Versions

The repository contains two independent packs. You can run them simultaneously — they do not conflict (each creates its own save files).

1. **🟢 Original Pack (`original-pack.py`)**
   * **Vocabulary:** ~50 phrases.
   * **Behavior:** Basic reactions to clicks, dragging, feeding.
   * **For whom:** For those who want a lightweight, unobtrusive pet that just says basic phrases.

2. **🔴 Macrosink Pack (`macrosink-pack.py`)**
   * **Vocabulary:** ~2000 phrases! (Including memes, programmer humor, and unique reactions).
   * **Behavior:** Highly talkative. Every action has 40 to 90 unique phrases.
   * **For whom:** For those who want maximum interaction and a pet that constantly says something new and funny.

---

## 🚀 How to Run (From Source Code)

Since `.exe` files are not provided in the repository, you need to run the Python source code directly.

### 1. Prerequisites
* Install [Python 3.10+](https://www.python.org/downloads/) (Make sure to check **"Add Python to PATH"** during installation).
* Install the required library. Open Command Prompt (cmd) and run:
  ```bash
  pip install PyQt6
2. Running the Pet
Download or clone this repository to your PC.

Open Command Prompt and navigate to the folder with the scripts:

bash
cd path/to/your/folder
Run the desired script:

bash
python original-pack.py
# OR
python macrosink-pack.py
🛠 How to Build a Standalone .exe (Optional)
If you don't want to run the Python script every time, you can compile it into a standalone .exe file using PyInstaller.

Install PyInstaller:

bash
pip install pyinstaller
Compile the script (replace script_name.py with your chosen pack):

For Original Pack:

bash
python -m PyInstaller --noconsole --onefile --name="OriginalPet" original-pack.py
For Macrosink Pack:

bash
python -m PyInstaller --noconsole --onefile --name="MacrosinkPet" macrosink-pack.py
After the process finishes, look for the dist folder. Your .exe file will be inside it.

(Note: The code is already optimized to save cfg.json and brain.json next to the .exe file, so your settings and memory will not be lost when using PyInstaller).

🧠 How to Set Up AI (Neural Network)
Right-click on the pet and select "Настройки" (Settings).

Go to the "ИИ и Память" (AI & Memory) tab.

Check the box "Включить ИИ-реплики" (Enable AI responses).

Choose your provider:

Claude (Anthropic): Enter your Anthropic key. Default model: claude-3-haiku-20240307.

Google Gemini: Enter your Google AI Studio key. Default model: gemini-1.5-flash.

OpenAI-compatible: Enter your key and custom API URL (e.g., https://openrouter.ai/api/v1).

Click "Сохранить" (Save).

The pet has a built-in cooldown (1 request per 10 seconds) to prevent spamming your API and wasting tokens.

📝 How to Edit the Phrase Dictionary
All pet dialogue is stored in the PHRASES dictionary at the top of the .py file.

Dictionary Structure
The dictionary consists of keys (events) and lists of strings (phrases).

python
PHRASES = {
    "hello": [
        "Привет, {user}!", 
        "Я Clawd, твой личный агент!"
    ],
    "tap": [
        "Ой!", 
        "Эй, {user}!", 
        "Чего тыкаешь?"
    ]
}
Step-by-Step Guide
Open macrosink-pack.py (or original-pack.py) in any code editor (VS Code, Notepad++).

Find the line PHRASES = {.

Find the event you want to edit (e.g., "pet" for when the pet is being petted).

Add a new phrase inside the square brackets [ ... ]. Make sure to use quotes and add a comma at the end of each line.

Example:

python
    "pet": [
        "Мрр…", 
        "Ещё!", 
        "New phrase I just came up with!", # <--- Added my own phrase
        "Приятно ♥"
    ],
🏷 Variables
Some phrases use variables that are replaced on the fly:

{user} — Replaced with the username from settings (e.g., "Привет, Administrator!").

{fact} — Replaced with a Wikipedia fact (only used in "wiki").

💡 List of Available Events (Keys):
hello — On startup

idle — Idle behavior

tap — Single click

annoyed — Spamming clicks

pet — Petting with mouse

drag — Dragging

throw — Throwing

dizzy — Dizzy after hitting the wall

wake — Waking up

jump — Double click

eat — Eating the screen

spit — Returning eaten pixels

poop — Pooping

clean — Cleaning up poop

drop — Landing

disco — Rainbow disco

wiki — Wikipedia fact

cursor — Following the cursor

📂 Save Files
The pet creates two files next to the script/executable:

xxx_cfg.json — Settings (name, color, AI enabled/disabled).

xxx_brain.json — Pet's memory (facts learned about you).

If you want to reset the memory, simply delete brain.json or click "Забыть всё" (Forget Everything) in the settings.
