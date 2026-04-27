"""
Podcast Studio – Model Selector + Animated Speaking Indicator
-------------------------------------------------------------
- Multiple free AI models to choose from
- Dynamic voice selection with all system voices
- Pulsing animation to highlight the current speaker
- Professional UI with custom CSS
"""

import streamlit as st
import fitz
import requests
import re
import tempfile
import os
import wave
import io
import time
from typing import List, Tuple, Optional

try:
    import pyttsx3
except ImportError:
    st.error("Please install pyttsx3: pip install pyttsx3")
    st.stop()

# ------------------------------ PAGE CONFIG ------------------------------
st.set_page_config(page_title="Podcast Studio Pro", layout="wide")

# ------------------------------ CUSTOM CSS ------------------------------
st.markdown("""
<style>
    .speaker-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 50px;
        margin: 20px 0;
    }
    .speaker {
        text-align: center;
        padding: 20px;
        border-radius: 15px;
        transition: all 0.3s ease;
    }
    .speaker.active {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(0,0,0,0.2);
    }
    .dot {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        margin: 10px auto;
        background-color: #ccc;
        transition: background-color 0.3s ease;
    }
    .dot.speaking {
        animation: pulse 0.8s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }
    .host-dot.speaking { background-color: #ff4b4b; }
    .guest-dot.speaking { background-color: #4b8bff; }
    .info-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------ SESSION STATE ----------------------------
if "script" not in st.session_state:
    st.session_state.script = ""
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "current_speaker" not in st.session_state:
    st.session_state.current_speaker = "host"

# ------------------------------ GET ALL VOICES ---------------------------
@st.cache_resource
def get_all_voices():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    return [(v.name, v.id) for v in voices]

all_voices = get_all_voices()
voice_names = [v[0] for v in all_voices]
voice_ids = {v[0]: v[1] for v in all_voices}

# ------------------------------ SIDEBAR -----------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    host_name = st.text_input("Host Name", "Alex")
    guest_name = st.text_input("Guest Name", "Jordan")

    st.subheader("🎤 Voice Settings")
    host_voice_name = st.selectbox("Host Voice", voice_names, index=0 if voice_names else None)
    guest_voice_name = st.selectbox("Guest Voice", voice_names, index=min(1, len(voice_names)-1) if voice_names else None)

    host_speed = st.slider("Host Speed (WPM)", 100, 250, 160)
    guest_speed = st.slider("Guest Speed (WPM)", 100, 250, 160)

    st.subheader("🎭 Script Style")
    script_style = st.selectbox("Select style", [
        "Casual", "Funny / Humorous", "Professional / Formal",
        "Beginner-friendly", "Advanced / Technical"
    ])

    st.subheader("🤖 AI Model")
    model_name = st.selectbox(
        "Choose model",
        [
            "deepseek/deepseek-chat",
            "openrouter/free",
            "google/gemini-2.5-pro-exp-03-25:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "qwen/qwq-32b:free",
            "nvidia/nemotron-3-super:free"
        ],
        index=0,
        help="All models are free (some require data sharing permission in OpenRouter settings)"
    )

    st.subheader("🔑 OpenRouter API Key")
    api_key = st.text_input(
        "API Key",
        type="password",
        help="Free key from https://openrouter.ai/keys. DeepSeek Chat is free with no spending limit."
    )
    st.caption("⚠️ Enable 'Allow free model providers' in your OpenRouter privacy settings.")

# ------------------------------ HELPER: Latin‑1 safe text -----------------
def latin1_safe(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")

# ------------------------------ TTS ---------------------------------------
def text_to_wav(text: str, voice_id: str, speed: int) -> bytes:
    safe_text = latin1_safe(text)
    engine = pyttsx3.init()
    engine.setProperty('voice', voice_id)
    engine.setProperty('rate', speed)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    engine.save_to_file(safe_text, tmp.name)
    engine.runAndWait()
    time.sleep(0.2)

    with open(tmp.name, "rb") as f:
        data = f.read()
    os.unlink(tmp.name)
    return data

# ------------------------------ PDF & TOPICS ------------------------------
def extract_text_from_pdf(file) -> str:
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "\n".join([page.get_text() for page in doc])

def highlight_important(text: str) -> str:
    words = re.findall(r'\b\w{6,}\b', text)
    if not words:
        return text
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_keywords = sorted(freq, key=freq.get, reverse=True)[:5]
    for kw in sorted_keywords:
        text = re.sub(f"\\b({kw})\\b", r"**\1**", text, flags=re.IGNORECASE)
    return text

# ------------------------------ OPENROUTER CALL ---------------------------
def call_openrouter(prompt: str, api_key: str, model: str, max_tokens: int = 2048) -> str:
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": max_tokens
    }
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    if resp.status_code != 200:
        raise Exception(f"API error {resp.status_code}: {resp.text}")
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def generate_ai_script(host, guest, topics, context, style, api_key, model):
    style_map = {
        "Casual": "- Casual language with fillers.",
        "Funny / Humorous": "- Witty, with jokes.",
        "Professional / Formal": "- Formal, no fillers.",
        "Beginner-friendly": "- Simple terms, no jargon.",
        "Advanced / Technical": "- Technical deep dive."
    }
    style_inst = style_map.get(style, "")
    prompt = f"""
Write a podcast conversation between {host} and {guest}.
Topics: {', '.join(topics)}
Context: {context[:1500].replace(chr(10), ' ')}
Use exactly these speaker labels (with a colon):
{host}:
{guest}:
{style_inst}
"""
    return call_openrouter(prompt, api_key, model)

def modify_script(original, instruction, api_key, model, host, guest):
    prompt = f"""
Modify this podcast script according to: "{instruction}"
Keep the exact same speaker labels ({host}: and {guest}:).
Current script:
{original}
Return the full updated script.
"""
    return call_openrouter(prompt, api_key, model)

# ------------------------------ OFFLINE FALLBACK --------------------------
def offline_script(host, guest, topics, style):
    intros = {
        "Casual": f"{host}: Hey everyone, I'm {host}.\n{guest}: Hi, great to be here!\n\n",
        "Funny / Humorous": f"{host}: Hello you beautiful people! I'm {host} and this is {guest}.\n{guest}: (laughs) Let's have fun!\n\n",
        "Professional / Formal": f"{host}: Good day. I'm {host}, with me is {guest}.\n{guest}: Thank you, a pleasure.\n\n",
        "Beginner-friendly": f"{host}: Hey friends! I'm {host}. Today we keep it simple.\n{guest}: Absolutely, no jargon.\n\n",
        "Advanced / Technical": f"{host}: Welcome back. Diving deep with {guest}.\n{guest}: We're not holding back.\n\n"
    }
    script = intros.get(style, intros["Casual"])
    for t in topics:
        script += f"{host}: Let's talk about {t}.\n{guest}: Definitely, {t} is important.\n\n"
    script += f"{host}: That's all for today. Thanks, {guest}.\n{guest}: Thanks, {host}!\n"
    return script

# ------------------------------ ROBUST AUDIO PARSER -----------------------
def extract_dialogue(line: str, host: str, guest: str) -> Tuple[Optional[str], Optional[str]]:
    line = line.strip()
    if not line or ':' not in line:
        return None, None

    colon_idx = line.find(':')
    prefix_raw = line[:colon_idx].strip()
    text = line[colon_idx+1:].strip()

    prefix_clean = re.sub(r'[*_~`]', '', prefix_raw)
    prefix_clean = re.sub(r'\(.*?\)', '', prefix_clean)
    prefix_clean = prefix_clean.strip().lower()

    if prefix_clean == host.lower():
        speaker = "host"
    elif prefix_clean == guest.lower():
        speaker = "guest"
    elif prefix_clean in ("host", "guest"):
        speaker = prefix_clean
    else:
        return None, None

    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\*.*?\*', '', text)
    text = text.strip()

    if not text:
        return None, None
    return speaker, text

def build_audio(script, host, guest, host_vid, guest_vid, host_spd, guest_spd):
    lines = script.split("\n")
    segments = []
    params = None

    for line in lines:
        speaker, text = extract_dialogue(line, host, guest)
        if not speaker or not text:
            continue

        if speaker == "host":
            audio_bytes = text_to_wav(text, host_vid, host_spd)
        else:
            audio_bytes = text_to_wav(text, guest_vid, guest_spd)

        if params is None:
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
                params = wf.getparams()

        with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
            segments.append(wf.readframes(wf.getnframes()))

        silence_frames = int(params.framerate * 0.25)
        segments.append(b'\x00' * (silence_frames * params.sampwidth))

    if not segments or params is None:
        sample_lines = "\n".join(lines[:3])
        raise Exception(
            f"No valid dialogue lines found. "
            f"Make sure the script uses '{host}: ...' or '{guest}: ...' format.\n"
            f"First lines of script:\n{sample_lines}"
        )

    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    with wave.open(output_path, 'wb') as out:
        out.setparams(params)
        for chunk in segments:
            out.writeframes(chunk)
    return output_path

# ------------------------------ MAIN UI -----------------------------------
st.title("🎙️ Podcast Studio Pro")
st.markdown("Create professional podcast scripts with AI and high-quality voices")

uploaded_file = st.file_uploader("📄 Upload PDF", type=["pdf"])

if uploaded_file:
    raw_text = extract_text_from_pdf(uploaded_file)
    st.session_state.pdf_text = raw_text

    st.subheader("📝 Extracted Text (Editable & Highlighted)")
    edited_text = st.text_area("Edit text", value=raw_text, height=200)
    highlighted = highlight_important(edited_text)
    st.markdown(highlighted, unsafe_allow_html=True)

    # Topic selection
    st.subheader("📌 Topics")
    sentences = re.split(r'(?<=[.!?])\s+', edited_text)
    extracted_topics = [s.strip() for s in sentences if 40 < len(s) < 150][:6]

    selected_extracted = []
    if extracted_topics:
        cols = st.columns(2)
        for i, t in enumerate(extracted_topics):
            with cols[i % 2]:
                if st.checkbox(t, key=f"top_{i}"):
                    selected_extracted.append(t)

    manual_topics = st.text_area("Custom topics (one per line)", height=100)
    manual_list = [t.strip() for t in manual_topics.splitlines() if t.strip()]
    final_topics = list(dict.fromkeys(manual_list + selected_extracted))
    st.write("**Final topics:**", final_topics if final_topics else "None")

    if st.button("🚀 Generate Script", type="primary"):
        if not host_name or not guest_name or not final_topics:
            st.error("Please fill all fields and select at least one topic.")
        else:
            with st.spinner("Generating script..."):
                if api_key:
                    try:
                        script = generate_ai_script(
                            host_name, guest_name, final_topics,
                            edited_text, script_style, api_key, model_name
                        )
                        st.session_state.script = script
                        st.success("Script generated!")
                    except Exception as e:
                        st.warning(f"⚠️ {e}\nUsing offline template.")
                        st.session_state.script = offline_script(
                            host_name, guest_name, final_topics, script_style
                        )
                else:
                    st.info("No API key – using offline template.")
                    st.session_state.script = offline_script(
                        host_name, guest_name, final_topics, script_style
                    )
                st.session_state.audio_file = None

# ---------- Script text area (always visible) ----------
st.subheader("✍️ Podcast Script")
script_display = st.text_area(
    "Edit the script directly if needed",
    value=st.session_state.script,
    height=300
)
st.session_state.script = script_display

# ---------- Modify script ----------
if st.session_state.script:
    st.subheader("✏️ Modify Script")
    mod_instruction = st.text_input("Enter an instruction (e.g., 'make it funnier')")
    if st.button("Apply Modification"):
        if not api_key:
            st.warning("API key required for modification.")
        elif not mod_instruction:
            st.warning("Please enter an instruction.")
        else:
            with st.spinner("Modifying..."):
                try:
                    new_script = modify_script(
                        st.session_state.script, mod_instruction,
                        api_key, model_name, host_name, guest_name
                    )
                    st.session_state.script = new_script
                    st.success("Script modified!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Modification failed: {e}")

# ---------- Generate audio ----------
st.subheader("🔊 Generate Audio")
if st.button("Create Audio"):
    if not st.session_state.script.strip():
        st.error("No script available. Generate or paste a script first.")
    else:
        with st.spinner("Rendering voices..."):
            host_vid = voice_ids.get(host_voice_name)
            guest_vid = voice_ids.get(guest_voice_name)
            if not host_vid or not guest_vid:
                st.error("Could not find selected voices. Please choose from the list.")
            else:
                try:
                    audio_path = build_audio(
                        st.session_state.script,
                        host_name, guest_name,
                        host_vid, guest_vid,
                        host_speed, guest_speed
                    )
                    st.session_state.audio_file = audio_path
                    st.success("✅ Audio created!")
                except Exception as e:
                    st.error(f"❌ {e}")

# ---------- Animated Speaking Indicator ----------
st.subheader("🎭 Live Speaking Indicator")
# Determine active speaker styling
host_active = "active" if st.session_state.current_speaker == "host" else ""
guest_active = "active" if st.session_state.current_speaker == "guest" else ""
host_dot = "speaking host-dot" if st.session_state.current_speaker == "host" else ""
guest_dot = "speaking guest-dot" if st.session_state.current_speaker == "guest" else ""

col1, col2, col3 = st.columns([2,1,2])
with col1:
    st.markdown(f"""
    <div class="speaker {host_active}">
        <h3>🎤 {host_name}</h3>
        <div class="dot {host_dot}"></div>
        <p>Host</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.write("")
    if st.button("Swap Speaker", key="swap_btn"):
        st.session_state.current_speaker = "guest" if st.session_state.current_speaker == "host" else "host"
with col3:
    st.markdown(f"""
    <div class="speaker {guest_active}">
        <h3>🎤 {guest_name}</h3>
        <div class="dot {guest_dot}"></div>
        <p>Guest</p>
    </div>
    """, unsafe_allow_html=True)

# ---------- Play audio ----------
if st.session_state.audio_file:
    st.audio(st.session_state.audio_file, format='audio/wav')