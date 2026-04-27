# 🎙️ Podcast Studio Pro

Transform any PDF into a full podcast script and audio using **free AI models** and offline text-to-speech.
Choose your speakers, pick a style, and listen to your podcast — all from your own computer.

---

## ✨ Features

* 📄 **PDF extraction** – upload any text-based PDF and edit the content inline
* 🔍 **Keyword highlighting** – important words are bolded automatically
* 📌 **Topic selector** – pick from extracted sentences or type your own
* 🤖 **Multiple free LLMs** – DeepSeek, Gemini, Llama, Qwen, and more
* 🎭 **Script styles** – Casual, Funny, Formal, Beginner, Technical
* ✏️ **Script modification** – tweak the generated script with a plain-English instruction
* 🔊 **Offline audio generation** – separate voices with adjustable speed, no internet needed
* 🎨 **Animated speaker indicator** – a glowing dot shows who is speaking
* 🔒 **100% free** – no API costs, no hidden limits

---

## 🛠️ Installation

### Prerequisites

* Python **3.9 or newer** (3.10+ recommended)
* `pip` (usually included with Python)
* Git (optional, for cloning)

---

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/podcast-studio.git
cd podcast-studio
```

---

### 2. Create a virtual environment

**Windows**

```bash
python -m venv venv
venv\\Scripts\\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies:

```
streamlit
PyMuPDF
requests
pyttsx3
```

---

### 4. (Optional) Verify TTS voices

```python
import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for v in voices:
    print(v.name)
```

---

## 🚀 Running the App

```bash
streamlit run app.py
```

Open: [http://localhost:8501](http://localhost:8501)

---

## 📖 Usage

1. Setup host/guest, voices, style, and model
2. Upload a PDF
3. Edit extracted text
4. Select topics
5. Generate script
6. Modify if needed
7. Generate audio
8. Download podcast

---

## 🎤 Voice Settings

* Choose different voices for Host and Guest
* Adjust speaking speed independently

If no voices appear:

* Windows: Install speech voices in settings
* Linux: `sudo apt install espeak libespeak1`

---

## 🤖 AI Models

* deepseek/deepseek-chat (recommended)
* openrouter/free
* gemini (free)
* llama (free)
* qwen (free)
* nemotron (free)

---

## 🔊 Audio Details

* Line-by-line speech generation
* Requires speaker labels (Host:/Guest:)
* Removes formatting automatically
* Outputs WAV file

---

## ❗ Troubleshooting

* Empty script → Refresh page
* No dialogue → Check speaker labels
* API errors → Verify key/model
* No voices → Install voice packs

---

## ☁️ Deployment

Audio won’t work on Streamlit Cloud (requires local drivers).

---

## 📁 Structure

```
podcast-studio/
├── app.py
├── requirements.txt
├── README.md
```

---

## 📝 License

MIT License

---

## 🙋‍♂️ Credits

Built with Streamlit, PyMuPDF, and pyttsx3.
AI powered via OpenRouter.
Rahul Bhati
