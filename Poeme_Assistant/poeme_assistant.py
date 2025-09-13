#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Poeme Assistant — Tkinter app (RO/EN)
Single-file, no external deps. Features:
- Dual language switch (Română / English)
- Two modes: Generate Poem • Check My Poem
- Generator: bigram language model + prompt/keywords + optional rhyme scheme
- Analyzer: rhyme density, approximate syllable/meter, imagery & sentiment hints, vocabulary variety
- UI: purple/blue/pink palette, save/copy, topic suggestions

Author: Claudiu helper (ChatGPT)
License: MIT
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re, random, datetime

# -----------------------------
# Small seed corpora (public domain fragments / generic lines)
# -----------------------------
CORPUS_EN = (
    "the moon is a lantern over quiet streets\n"
    "the river hums its silver hymn at night\n"
    "in windows sleep the tender city hearts\n"
    "a kind wind gathers petals into light\n"
    "i carry simple rain inside my coat\n"
    "and laughter grows like gardens in the spring\n"
    "we learn the names of shadows by their songs\n"
    "and write soft letters to the dawn we bring\n"
)

CORPUS_RO = (
    "luna plutește blând peste orașul tăcut\n"
    "râul murmură încet cântarea lui de-argint\n"
    "în ferestre doarme inima cetății\n"
    "un vânt cumințește praful rătăcind\n"
    "port o ploaie mică-n buzunarul vechi\n"
    "râsul răsare ca o grădină-n mai\n"
    "învățăm din umbre alfabetul serii\n"
    "și scriem zorilor scrisori de rai\n"
)

STOPWORDS_EN = set("the a an and or of in on at for with by to from into over under is are was were be as that this those these it we you i they them us our your their".split())
STOPWORDS_RO = set("și sau ori de din la pe pentru cu prin sub peste într-un într-o în într înspre este sunt eram ești e suntem sunteți un o niște ce că întru către mai prea iar dar să nu nici ci precum căci ai am au îl îți ți îmi mi ți-l își își-l vă vouă ne nouă lui ei el ea le l".split())

VOWELS_EN = set("aeiouy")
VOWELS_RO = set("aeiouăîâ")  # simplified

# Romanian diphthongs (approx)
DIPHTHONGS_RO = ["ea","oa","ia","ie","io","iu","ua","uo","ui","eu","ei","âi","îi"]

# -----------------------------
# Utility NLP helpers
# -----------------------------
def tokenize(text):
    return [w for w in re.findall(r"[\w'ăâîșțÁÂĂÎȘȚàèéìòùâêîôûäëïöüœç'-]+", text.lower()) if w.strip("-")]

def build_bigrams(corpus_lines):
    tokens = []
    for line in corpus_lines.splitlines():
        line = line.strip()
        if not line:
            continue
        toks = ["<s>"] + tokenize(line) + ["</s>"]
        tokens.extend(toks)
    bigrams = {}
    for a, b in zip(tokens, tokens[1:]):
        bigrams.setdefault(a, []).append(b)
    return bigrams

def generate_line(bigrams, max_len=9, seed_words=None):
    line = []
    kw = [w.lower() for w in (seed_words or []) if w]
    if kw and random.random() < 0.7:
        line.append(random.choice(kw))
    while True:
        prev = "<s>" if not line else line[-1]
        nexts = bigrams.get(prev, bigrams.get("<s>", ["</s>"]))
        nxt = random.choice(nexts)
        if nxt == "</s>" or len(line) >= max_len:
            break
        line.append(nxt)
    s = " ".join(line).strip()
    if s:
        s = s[0].upper() + s[1:]
    return s

def simple_rhyme_key(word, lang="en"):
    w = re.sub(r"[^a-zăâîșț]", "", word.lower())
    if lang == "en":
        m = re.search(r"[aeiouy][^aeiouy]*$", w)
        return m.group(0) if m else w[-3:]
    else:
        for d in sorted(DIPHTHONGS_RO, key=len, reverse=True):
            if w.endswith(d):
                return d
        m = re.search(r"[aeiouăâî][^aeiouăâî]*$", w)
        return m.group(0) if m else w[-3:]

def last_word(line):
    toks = tokenize(line)
    return toks[-1] if toks else ""

def approx_syllables(word, lang="en"):
    w = word.lower()
    if not w:
        return 0
    if lang == "en":
        w = re.sub(r"e$", "", w)
        groups = re.findall(r"[aeiouy]+", w)
        return max(1, len(groups))
    else:
        tmp = w
        for d in DIPHTHONGS_RO:
            tmp = tmp.replace(d, "*")
        groups = re.findall(r"[aeiouăâî*]+", tmp)
        return max(1, len(groups))

def line_syllables(line, lang="en"):
    return sum(approx_syllables(w, lang) for w in tokenize(line))

def rhyme_density(lines, lang="en"):
    keys = [simple_rhyme_key(last_word(l), lang) for l in lines if l.strip()]
    if not keys:
        return 0.0
    counts = {}
    for k in keys:
        counts[k] = counts.get(k, 0) + 1
    paired = sum(c for c in counts.values() if c > 1)
    return paired / max(1, len(keys))

def vocab_variety(text, lang="en"):
    toks = tokenize(text)
    stop = STOPWORDS_EN if lang == "en" else STOPWORDS_RO
    content = [t for t in toks if t not in stop]
    if not content:
        return 0
    return len(set(content)) / len(content)

def sentiment_hint(text, lang="en"):
    pos_en = {"love","light","tender","kind","bright","soft","spring","dawn","smile","hope","song","calm"}
    neg_en = {"dark","cold","lonely","broken","empty","tears","storm","fall","fade","ache"}
    pos_ro = {"iubire","lumină","blând","bun","strălucit","moale","primăvară","zori","zâmbet","speranță","cântec","liniște"}
    neg_ro = {"întunecat","rece","singur","frânt","gol","lacrimi","furtună","toamnă","stinge","durere"}
    toks = set(tokenize(text))
    if lang == "en":
        score = (len(toks & pos_en) - len(toks & neg_en))
    else:
        score = (len(toks & pos_ro) - len(toks & neg_ro))
    return "positive" if score > 0 else ("negative" if score < 0 else "neutral")

# -----------------------------
# Poem generation
# -----------------------------
def generate_poem(n_stanzas=2, lines_per_stanza=4, lang="en", keywords=None, scheme="AABB"):
    corpus = CORPUS_EN if lang == "en" else CORPUS_RO
    bigrams = build_bigrams(corpus)
    kw = [k.lower() for k in (keywords or []) if k]

    def make_stanza(rhyme_targets=None):
        lines = []
        for _ in range(lines_per_stanza):
            base = generate_line(bigrams, max_len=random.randint(6,10), seed_words=kw)
            if kw and random.random() < 0.5 and base:
                base += " " + random.choice(kw)
            lines.append(base)
        if rhyme_targets:
            for idx_group in rhyme_targets.values():
                last = last_word(lines[idx_group[0]])
                key = simple_rhyme_key(last, lang)
                for j in idx_group[1:]:
                    w = last_word(lines[j])
                    if simple_rhyme_key(w, lang) != key:
                        candidates = kw + tokenize(corpus)
                        random.shuffle(candidates)
                        for c in candidates:
                            if simple_rhyme_key(c, lang) == key and c != w:
                                lines[j] = re.sub(r"\W*$", "", lines[j])
                                lines[j] = re.sub(r"\w+$", c, lines[j])
                                break
        return lines

    def scheme_groups(scheme_str, n_lines):
        scheme_str = (scheme_str or "").upper()
        scheme_str = (scheme_str * ((n_lines // max(1,len(scheme_str)))+1))[:n_lines]
        groups = {}
        for i, ch in enumerate(scheme_str):
            groups.setdefault(ch, []).append(i)
        return {k: v for k, v in groups.items() if len(v) > 1}

    stanzas = []
    for _ in range(max(1, n_stanzas)):
        groups = scheme_groups(scheme, lines_per_stanza)
        stanzas.append(make_stanza(groups))
    return stanzas

# -----------------------------
# Poem analysis & feedback
# -----------------------------
def analyze_poem(text, lang="en", target_syllables=(8,10)):
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return {"error":"No lines to analyze."}
    sylls = [line_syllables(l, lang) for l in lines]
    avg = sum(sylls)/len(sylls)
    dev = (sum((s-avg)**2 for s in sylls)/len(sylls))**0.5
    rden = rhyme_density(lines, lang)
    vv = vocab_variety(text, lang)
    senti = sentiment_hint(text, lang)

    lo, hi = target_syllables
    meter_fit = sum(1 for s in sylls if lo <= s <= hi)/len(sylls)

    score = (
        40 * meter_fit +
        25 * rden +
        20 * vv +
        15 * (1 - min(1, dev/6))
    )
    score = round(score, 1)

    notes = []
    if meter_fit < 0.5:
        notes.append("Multe versuri ies din intervalul de silabe țintă / Many lines fall outside target syllable range.")
    if rden < 0.3:
        notes.append("Rima e rară; poți adăuga rime la final de vers / Rhyme density is low; consider rhymed endings.")
    if vv < 0.35:
        notes.append("Vocabular repetitiv; încearcă metafore sau verbe mai precise / Repetitive vocabulary; try fresh images.")

    suggestions = []
    idx_worst = max(range(len(lines)), key=lambda i: abs(((lo+hi)//2) - sylls[i]))
    lw = lines[idx_worst]
    if lang == "en":
        suggestions.append(f"Try shortening line {idx_worst+1} by removing a filler word, e.g., '{lw}' → '{' '.join(tokenize(lw)[:-1])}'.")
    else:
        suggestions.append(f"Încearcă să scurtezi versul {idx_worst+1} eliminând un cuvânt de umplutură, ex.: '{lw}' → '{' '.join(tokenize(lw)[:-1])}'.")

    return {
        "lines": lines,
        "syllables": sylls,
        "avg": round(avg,2),
        "stdev": round(dev,2),
        "rhyme_density": round(rden,2),
        "vocab_variety": round(vv,2),
        "sentiment": senti,
        "meter_fit": round(meter_fit,2),
        "score": score,
        "notes": notes,
        "suggestions": suggestions,
    }

# -----------------------------
# Tkinter UI
# -----------------------------
APP_TITLE = "Poeme Assistant — Asistent de poezii"

PALETTE = {
    "bg": "#0f1020",
    "fg": "#e9e7ff",
    "accent1": "#7c3aed",
    "accent2": "#2563eb",
    "accent3": "#ec4899",
    "muted": "#94a3b8",
}

class PoemeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1080x720")
        self.minsize(980, 640)
        self.configure(bg=PALETTE["bg"])

        self.lang = tk.StringVar(value="ro")  # 'ro' or 'en'
        self.mode = tk.StringVar(value="generate")  # 'generate' or 'analyze'
        self.scheme = tk.StringVar(value="AABB")

        self._build_styles()
        self._build_layout()

    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=PALETTE["bg"])
        style.configure("TLabel", background=PALETTE["bg"], foreground=PALETTE["fg"], font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground=PALETTE["fg"])
        style.configure("Hint.TLabel", foreground=PALETTE["muted"], font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.map("TButton",
                  background=[("active", PALETTE["accent2"])],
                  foreground=[("active", "white")])
        style.configure("Accent.TButton", background=PALETTE["accent1"], foreground="white", borderwidth=0)
        style.configure("Pink.TButton", background=PALETTE["accent3"], foreground="white", borderwidth=0)
        style.configure("Switch.TCheckbutton", background=PALETTE["bg"], foreground=PALETTE["fg"])
        style.configure("Card.TLabelframe", background="#14162b", foreground=PALETTE["fg"], borderwidth=0)
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 12, "bold"))

    def _build_layout(self):
        topbar = ttk.Frame(self)
        topbar.pack(fill="x", padx=16, pady=12)
        ttk.Label(topbar, text="Poeme Assistant", style="Header.TLabel").pack(side="left")

        # Language switch
        lang_frame = ttk.Frame(topbar)
        lang_frame.pack(side="right")
        ttk.Label(lang_frame, text="Română").pack(side="left")
        lang_switch = ttk.Checkbutton(lang_frame, style="Switch.TCheckbutton", command=self._toggle_lang)
        lang_switch.state(["!alternate"])
        lang_switch.pack(side="left", padx=6)
        ttk.Label(lang_frame, text="English").pack(side="left")
        lang_switch.bind("<Button-1>", self._lang_click)

        # Mode toggle
        modebar = ttk.Frame(self)
        modebar.pack(fill="x", padx=16)
        self.btn_generate = ttk.Button(modebar, text="✍️ Generează / Generate", style="Accent.TButton", command=lambda: self._set_mode("generate"))
        self.btn_analyze = ttk.Button(modebar, text="🧪 Verifică poezia / Analyze", style="Pink.TButton", command=lambda: self._set_mode("analyze"))
        self.btn_generate.pack(side="left")
        self.btn_analyze.pack(side="left", padx=8)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        left = ttk.Labelframe(body, text="Controls / Control", style="Card.TLabelframe")
        left.pack(side="left", fill="y", padx=(0,12))

        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        self.n_stanzas = tk.IntVar(value=2)
        self.lines_per = tk.IntVar(value=4)
        self.target_lo = tk.IntVar(value=8)
        self.target_hi = tk.IntVar(value=10)

        row = 0
        ttk.Label(left, text="Strofe / Stanzas").grid(row=row, column=0, sticky="w", padx=10, pady=(10,2))
        tk.Spinbox(left, from_=1, to=12, width=6, textvariable=self.n_stanzas).grid(row=row, column=1, padx=10, pady=(10,2)); row+=1
        ttk.Label(left, text="Versuri/strofă / Lines per stanza").grid(row=row, column=0, sticky="w", padx=10, pady=2)
        tk.Spinbox(left, from_=2, to=12, width=6, textvariable=self.lines_per).grid(row=row, column=1, padx=10, pady=2); row+=1
        ttk.Label(left, text="Rhyme scheme (e.g., AABB/ABAB)").grid(row=row, column=0, sticky="w", padx=10, pady=2)
        tk.Entry(left, width=8, textvariable=self.scheme).grid(row=row, column=1, padx=10, pady=2); row+=1
        ttk.Label(left, text="Cuvinte-cheie / Keywords (comma)").grid(row=row, column=0, sticky="w", padx=10, pady=2)
        self.ent_keywords = tk.Entry(left, width=22); self.ent_keywords.grid(row=row, column=1, padx=10, pady=2); row+=1
        ttk.Button(left, text="🎲 Sugerează temă / Suggest theme", command=self.suggest_theme).grid(row=row, column=0, columnspan=2, padx=10, pady=(6,10)); row+=1

        ttk.Separator(left, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=8); row+=1
        ttk.Label(left, text="Țintă silabe / Target syllables (lo-hi)").grid(row=row, column=0, sticky="w", padx=10, pady=2)
        tk.Spinbox(left, from_=4, to=14, width=6, textvariable=self.target_lo).grid(row=row, column=1, padx=10, pady=2); row+=1
        tk.Spinbox(left, from_=6, to=16, width=6, textvariable=self.target_hi).grid(row=row, column=1, padx=10, pady=2, sticky="e"); row+=1

        ttk.Button(left, text="💾 Save .txt", command=self.save_txt).grid(row=row, column=0, padx=10, pady=(12,6), sticky="ew")
        ttk.Button(left, text="📋 Copy", command=self.copy_text).grid(row=row, column=1, padx=10, pady=(12,6), sticky="ew")

        self.in_frame = ttk.Labelframe(right, text="Input / Intrare", style="Card.TLabelframe")
        self.in_frame.pack(fill="both", expand=True)
        self.txt_in = tk.Text(self.in_frame, wrap="word", height=10, bg="#0d0f24", fg=PALETTE["fg"], insertbackground=PALETTE["fg"], relief="flat")
        self.txt_in.pack(fill="both", expand=True, padx=10, pady=8)
        ttk.Label(self.in_frame, text="Scrie aici promptul sau poezia ta / Write your prompt or poem here", style="Hint.TLabel").pack(anchor="w", padx=10, pady=(0,8))

        self.out_frame = ttk.Labelframe(right, text="Output / Rezultat", style="Card.TLabelframe")
        self.out_frame.pack(fill="both", expand=True, pady=(12,0))
        self.txt_out = tk.Text(self.out_frame, wrap="word", height=14, bg="#0d0f24", fg=PALETTE["fg"], insertbackground=PALETTE["fg"], relief="flat")
        self.txt_out.pack(fill="both", expand=True, padx=10, pady=8)

        action = ttk.Frame(self)
        action.pack(fill="x", padx=16, pady=(6,16))
        ttk.Button(action, text="✨ Generate Poem / Generează", style="Accent.TButton", command=self.on_generate).pack(side="left")
        ttk.Button(action, text="🔍 Analyze / Verifică", style="Pink.TButton", command=self.on_analyze).pack(side="left", padx=8)

        self._refresh_mode()

    def _lang_click(self, event):
        self.lang.set("en" if self.lang.get()=="ro" else "ro")
        self._toggle_lang()

    def _toggle_lang(self):
        pass

    def _set_mode(self, m):
        self.mode.set(m)
        self._refresh_mode()

    def _refresh_mode(self):
        if self.mode.get() == "generate":
            self.in_frame.configure(text="Prompt / Prompt")
        else:
            self.in_frame.configure(text="Poezia ta / Your poem")

    def suggest_theme(self):
        themes_en = [
            "dawn over a sleeping city","letters carried by the wind","a pocket full of rain",
            "memory of a summer train","stars above a quiet river","the color of forgiveness"
        ]
        themes_ro = [
            "zori peste orașul adormit","scrisori purtate de vânt","un buzunar plin de ploaie",
            "amintirea unui tren de vară","stele deasupra unui râu liniștit","culoarea iertării"
        ]
        theme = random.choice(themes_en if self.lang.get()=="en" else themes_ro)
        self.ent_keywords.delete(0, tk.END)
        # simple keyword suggestion from theme
        kw = [w for w in tokenize(theme) if len(w) > 3]
        self.ent_keywords.insert(0, ", ".join(kw[:3]))
        self.txt_in.delete("1.0", tk.END)
        self.txt_in.insert("1.0", theme)

    def on_generate(self):
        lang = self.lang.get()
        prompt = self.txt_in.get("1.0", tk.END).strip()
        kw = [k.strip() for k in self.ent_keywords.get().split(',') if k.strip()]
        n = max(1, int(self.n_stanzas.get()))
        lp = max(2, int(self.lines_per.get()))
        scheme = self.scheme.get().strip().upper() or "AABB"

        stanzas = generate_poem(n_stanzas=n, lines_per_stanza=lp, lang=("en" if lang=="en" else "ro"), keywords=kw or tokenize(prompt), scheme=scheme)
        lo, hi = int(self.target_lo.get()), int(self.target_hi.get())
        out_lines = []
        for stanza in stanzas:
            for line in stanza:
                s = line
                syl = line_syllables(s, lang)
                if syl < lo and (kw or prompt):
                    append_word = (random.choice(kw) if kw else random.choice(tokenize(prompt)) if tokenize(prompt) else "")
                    if append_word:
                        s = s + " " + append_word
                elif syl > hi:
                    toks = tokenize(s)
                    if len(toks) > 3:
                        s = " ".join(toks[:-1]).capitalize()
                out_lines.append(s)
            out_lines.append("")
        text = "\n".join(out_lines).strip()
        header = ("— Poezie generată (RO) —" if lang=="ro" else "— Generated Poem (EN) —")
        self.txt_out.delete("1.0", tk.END)
        self.txt_out.insert("1.0", header+"\n\n"+text)

    def on_analyze(self):
        lang = self.lang.get()
        poem = self.txt_in.get("1.0", tk.END).strip()
        if not poem:
            messagebox.showinfo("Info", "Scrie mai întâi poezia / Write your poem first.")
            return
        lo, hi = int(self.target_lo.get()), int(self.target_hi.get())
        report = analyze_poem(poem, lang=("en" if lang=="en" else "ro"), target_syllables=(lo,hi))
        if "error" in report:
            self.txt_out.delete("1.0", tk.END)
            self.txt_out.insert("1.0", report["error"])
            return
        lbl = "Evaluare (RO)" if lang=="ro" else "Analysis (EN)"
        lines = report["lines"]
        syls = report["syllables"]
        table = [f"{i+1:>2}. [{syls[i]}] {lines[i]}" for i in range(len(lines))]
        stats = (
            f"Score: {report['score']}/100\n"
            f"Avg syllables: {report['avg']} | σ={report['stdev']} | meter_fit={report['meter_fit']}\n"
            f"Rhyme density: {report['rhyme_density']} | Vocab variety: {report['vocab_variety']} | Sentiment: {report['sentiment']}\n"
        )
        notes = "\n".join("- "+n for n in report["notes"]) or ("Bine echilibrată / Well balanced.")
        sugg = "\n".join("• "+s for s in report["suggestions"])

        self.txt_out.delete("1.0", tk.END)
        self.txt_out.insert("1.0", f"— {lbl} —\n\n"+"\n".join(table)+"\n\n"+stats+"\n"+notes+"\n\nSugestii / Suggestions:\n"+sugg)

    def save_txt(self):
        content = self.txt_out.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("Info", "Nu este nimic de salvat / Nothing to save.")
            return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"poeme_assistant_{ts}.txt", filetypes=[("Text","*.txt")])
        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Saved to {fname}")

    def copy_text(self):
        content = self.txt_out.get("1.0", tk.END).strip()
        if not content:
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "Rezultatul a fost copiat / Output copied.")

if __name__ == "__main__":
    app = PoemeApp()
    app.mainloop()
