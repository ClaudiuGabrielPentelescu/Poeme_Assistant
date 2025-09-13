# Poeme Assistant — Asistent de Poezii

🎭 **Poeme Assistant** este o aplicație grafică (Tkinter, Python) ce oferă o experiență duală:
- **Generare poezii** (Română și English), cu tematică, cuvinte-cheie și scheme de rimă.
- **Analiză poezii** scrise de utilizator, cu feedback despre silabe, rimă, vocabular și sugestii de îmbunătățire.

## ✨ Funcționalități
- 🌍 **Dual Language**: Română 🇷🇴 & English 🇬🇧
- 🖊️ **Generare poezie**: pe baza cuvintelor-cheie și a unei scheme de rimă (AABB, ABAB, etc.)
- 🔍 **Analiză poezie**: scor (0–100), densitate rime, distribuția silabelor, varietatea vocabularului și sentiment (pozitiv/negativ/neutru)
- 🎨 **Interfață grafică** modernă cu paletă mov-albastru-roz
- 💾 **Export**: salvare poezie/analiză ca fișier `.txt` sau copiere în clipboard
- 🎲 **Sugestii tematice** generate aleator

## 🚀 Instalare
```bash
git clone https://github.com/<username>/poeme-assistant.git
cd poeme-assistant
pip install -r requirements.txt
python poeme_assistant.py
```

## 📂 Fișiere
- `poeme_assistant.py` — aplicația principală
- `requirements.txt` — lista dependențelor (doar standard Python)
- `logo_poeme_assistant.svg` — logo-ul proiectului
- `icon_poeme_assistant.svg` — icon pentru aplicație
- `README.md` — documentația proiectului

## 🛠️ Requirements
- Python 3.8+
- Tkinter (pe Linux: `sudo apt-get install python3-tk`)
