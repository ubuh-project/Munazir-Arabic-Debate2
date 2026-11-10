# -*- coding: utf-8 -*-
"""
MUNĀẒIR (مُنَاظِرٌ) — Panduan & Pedoman Debat Bahasa Arab
Streamlit + Groq AI + basis pengetahuan HANYA dari file materi yang diunggah (tanpa sumber internet).

Cara menjalankan lokal:  streamlit run app.py
API key dibaca dari  st.secrets["GROQ_API_KEY"]  (JANGAN ditulis di kode).
"""
import io
import os
import re
import json
import html
import difflib
import hashlib
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer

# ─────────────────────────────────────────────────────────────
# KONFIGURASI DASAR
# ─────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
EXTS = {".txt", ".md", ".pdf", ".docx"}

# ── ISTILAH POI (dipakai seragam di seluruh website) ──
# Istilah Arab resmi MUNĀẒIR untuk POI. Buku sumber (Al-Murshed, Booklet QD, slide QatarDebate)
# memakai  الْمُدَاخَلَة  untuk konsep yang sama; teks kutipan buku TIDAK diubah, tetapi diberi catatan.
ISTILAH_POI = "نُقْطَةُ الاِسْتِشَارَةِ"
LABEL_POI = f"POI ({ISTILAH_POI})"
CATATAN_POI = (
    f"**Catatan istilah:** di MUNĀẒIR, POI disebut **{ISTILAH_POI}**. "
    "Sumber ini memakai istilah **الْمُدَاخَلَةُ** (jamak: **الْمُدَاخَلَاتُ**) untuk konsep yang sama."
)

CATEGORIES = {
    "sistem_debat": {
        "warna": "#C6A15B",
        "warna_teks": "#6B5526",
        "label": "Kumpulan Sistem Debat",
        "ar": "أَنْظِمَةُ الْمُنَاظَرَةِ",
        "icon": "",
        "desc": f"Teori & format Qatar Debate: posisi tim, peran pembicara, argumen, sanggahan, {LABEL_POI}, gaya, penjurian, latihan.",
    },
    "mosi": {
        "warna": "#4E6B58",
        "warna_teks": "#3E5747",
        "label": "Mosi",
        "ar": "مَوْضُوعَاتُ الْمُنَاظَرَةِ",
        "icon": "",
        "desc": "Jenis & analisis mosi, bank mosi per tema (MIZAN) dan bank qaḍāyā Al-Murshed.",
    },
    "ibarah": {
        "warna": "#9B4E3A",
        "warna_teks": "#7E3E2D",
        "label": "Ibārah",
        "ar": "الْعِبَارَاتُ",
        "icon": "",
        "desc": "Bank ibārah: membuka, berargumen, memberi bukti, menyanggah, bertanya, dan menutup pidato.",
    },
    "kosakata": {
        "warna": "#46606F",
        "warna_teks": "#384E5B",
        "label": "Kamus Debat",
        "ar": "الْمُفْرَدَاتُ",
        "icon": "",
        "desc": "Istilah debat, kata kerja argumentasi, dan mufradat per tema (Indonesia–Arab).",
    },
    "muqaddimah": {
        "warna": "#6B4A62",
        "warna_teks": "#573C50",
        "label": "Muqaddimah",
        "ar": "الْمُقَدِّمَةُ",
        "icon": "",
        "desc": "Bank muqaddimah per pembicara (pro/kontra, reply) dan teori struktur pidato.",
    },
}

# Logo di menu atas (huruf ظ + tulisan MUNĀẒIR)
LOGO_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' width='200' height='40' viewBox='0 0 200 40'>"
    "<rect x='1' y='1' width='38' height='38' rx='9' fill='#102A27' stroke='#C6A15B'/>"
    "<text x='20' y='29' font-size='24' text-anchor='middle' fill='#C6A15B' font-family='Amiri, serif'>ظ</text>"
    "<text x='50' y='26.5' font-size='17' letter-spacing='3.5' fill='#F4F0E7' font-family='Georgia, serif'>MUNĀẒIR</text>"
    "</svg>"
)

# ── ANIMASI LOGO 3D ──
# Taruh file logo di folder  static/  (sejajar dengan app.py):
#   static/logo3d.webp  ← UTAMA: animasi berlatar TRANSPARAN (menyatu dengan warna website,
#                          jalan di semua browser modern termasuk iPhone)
#   static/logo3d.mp4   ← cadangan (video berlatar krem) bila logo3d.webp belum diunggah
# Kalau file belum ada, website tetap jalan seperti biasa tanpa animasi.
STATIC_DIR = APP_DIR / "static"
LOGO_GAMBAR = "logo3d.webp"
LOGO_VIDEO = [("logo3d.webm", "video/webm"), ("logo3d.mp4", "video/mp4")]
SPLASH_DETIK = 4.2  # lama layar pembuka tampil sebelum memudar (detik)


def video_logo(kelas: str, ulang: bool = True) -> str:
    """Logo 3D beranimasi: gambar WebP transparan (utama) atau <video> (cadangan); kosong bila belum ada file."""
    if (STATIC_DIR / LOGO_GAMBAR).exists():
        return f"<img class='{kelas}' src='app/static/{LOGO_GAMBAR}' alt='Logo MUNĀẒIR' decoding='async'>"
    sumber = "".join(
        f"<source src='app/static/{nama}' type='{tipe}'>"
        for nama, tipe in LOGO_VIDEO if (STATIC_DIR / nama).exists()
    )
    if not sumber:
        return ""
    loop = " loop" if ulang else ""
    return (f"<video class='{kelas}' autoplay muted{loop} playsinline preload='auto' "
            f"aria-label='Logo MUNĀẒIR'>{sumber}</video>")

# Ikon menu atas (Material Symbols bawaan Streamlit)
IKON_MENU = {
    "sistem_debat": ":material/balance:",
    "mosi": ":material/description:",
    "ibarah": ":material/format_quote:",
    "kosakata": ":material/menu_book:",
    "muqaddimah": ":material/record_voice_over:",
}

# Link Google Form untuk menu Respon (tempel link form Anda di antara tanda kutip)
FORM_URL = "https://forms.gle/rwseAxjWB6oexi3m9"

# ── PROFIL PENGEMBANG ── (cukup ganti teks di antara tanda kutip)
PROFIL = {
    "nama": "Muhamad Subhi",
    "peran": "Pengembang MUNADZIR Arabic Debate",
    "instansi": "Magister Pendidikan Bahasa Arab · UIN Sunan Kalijaga Yogyakarta",
    "bio": (
        "Muhamad Subhi lahir di Narmada, Lombok Barat pada 10 Oktober 1996. Saat ini, ia tengah menempuh pendidikan "
        "tingkat Magister (S2) dalam program studi Pendidikan Bahasa Arab di Universitas Islam Negeri (UIN) "
        "Sunan Kalijaga Yogyakarta.\n\n"
        "Berangkat dari kecintaan pada dunia kebahasaan dan pedagogi, ia aktif mendalami kajian fonologi, "
        "pengembangan media pembelajaran digital, serta struktur argumentasi formal, termasuk sistem dan metodologi "
        "Qatar Debate. Melalui Website MUNADZIR ARABIC DEBATE ini, ia berdedikasi untuk menghadirkan panduan praktis "
        "yang memudahkan para pelajar, santri, dan mahasiswa (munāẓir) dalam menguasai seni debat bahasa Arab secara "
        "sistematis, komunikatif, dan berbasis AI."
    ),
    # Kontak: isi di antara tanda kutip (yang kosong tidak ditampilkan). Contoh:
    # "Email": "nama@gmail.com",  "Instagram": "@username",  "WhatsApp": "081234567890"
    "kontak": {
        "Email": "cakubuh9@gmail.com",
        "Instagram": "@msubhiii_",
        "WhatsApp": "087767461023",
    },
}

# Urutan model Groq yang dicoba (otomatis lompat jika ada yang sudah tidak tersedia)
PREFERRED_MODELS = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "moonshotai/kimi-k2-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "qwen/qwen3-32b",
    "openai/gpt-oss-20b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
]
BLOCKED_MODEL_WORDS = ("whisper", "guard", "tts", "playai", "orpheus", "compound", "distil", "safeguard")



# ─────────────────────────────────────────────────────────────
# UTILITAS TEKS
# ─────────────────────────────────────────────────────────────
AR_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")
AR_CHARS = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
AR_HURUF_DASAR = re.compile(r"[\u0621-\u063A\u0641-\u064A\u0671-\u06D3]")  # huruf Arab tanpa harakat
AR_TANDA_HARAKAT = re.compile(r"[\u064B-\u0652\u0670]")  # fathah, kasrah, dammah, tanwin, sukun, syaddah


def normalize_text(t: str) -> str:
    """Normalisasi untuk pencarian: hapus harakat & samakan bentuk huruf Arab."""
    t = AR_DIACRITICS.sub("", t.lower())
    t = re.sub("[إأآٱ]", "ا", t)
    return t.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")


STOPWORDS = set("""apa itu yang dan di ke dari untuk dengan bagaimana berapa adalah ini pada dalam atau cara tentang
saya kami kita aku anda bisa tolong jelaskan sebutkan berikan mohon contoh contohnya apakah mengapa kenapa siapa kapan
dimana mana juga akan sudah telah tidak bukan ada saja lebih paling sangat seperti agar supaya jika kalau maka serta
oleh para sebuah suatu bagi hal tersebut the a an of to in is are what how why which for and or
هل ما ماذا كيف لماذا من في على الى إلى عن هذا هذه ذلك التي الذي و أو ثم""".split())


def clean_query(q: str) -> str:
    words = re.findall(r"\w+", q)
    kept = [w for w in words if normalize_text(w) not in STOPWORDS and w.lower() not in STOPWORDS]
    return " ".join(kept) if kept else q


def is_mostly_arabic(t: str) -> bool:
    letters = [c for c in t if c.isalpha()]
    if not letters:
        return False
    return len(AR_CHARS.findall("".join(letters))) / len(letters) > 0.5


def extract_text(name: str, data: bytes) -> str:
    """Ambil teks dari .txt / .md / .pdf / .docx"""
    ext = Path(name).suffix.lower()
    try:
        if ext in (".txt", ".md"):
            if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
                return data.decode("utf-16")
            try:
                return data.decode("utf-8-sig")
            except UnicodeDecodeError:
                return data.decode("cp1256", errors="replace")
        if ext == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            return "\n\n".join((p.extract_text() or "") for p in reader.pages)
        if ext == ".docx":
            import docx

            d = docx.Document(io.BytesIO(data))
            parts = [p.text for p in d.paragraphs]
            for table in d.tables:
                for row in table.rows:
                    cells = [c.text.strip() for c in row.cells]
                    parts.append(" | ".join(c for c in cells if c))
            return "\n".join(parts)
    except Exception:  # file rusak / terenkripsi
        return ""
    return ""


def _units(text: str, size: int):
    units = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if len(para) <= size:
            units.append(para)
            continue
        for line in para.split("\n"):
            line = line.strip()
            while len(line) > size:
                cut = line.rfind(" ", 0, size)
                cut = cut if cut > size // 2 else size
                units.append(line[:cut])
                line = line[cut:].strip()
            if line:
                units.append(line)
    return units


def chunk_text(text: str, size: int = 900):
    chunks, cur, cur_len = [], [], 0
    for u in _units(text, size):
        if cur and cur_len + len(u) > size:
            chunks.append("\n".join(cur))
            # sedikit tumpang tindih agar konteks tidak terputus
            cur = [cur[-1]] if len(cur[-1]) < size // 4 else []
            cur_len = sum(len(x) + 1 for x in cur)
        cur.append(u)
        cur_len += len(u) + 1
    if cur:
        chunks.append("\n".join(cur))
    return chunks


# ─────────────────────────────────────────────────────────────
# BASIS PENGETAHUAN (RAG sederhana dengan TF-IDF karakter)
# ─────────────────────────────────────────────────────────────
def disk_signature():
    """Daftar semua file di data/<menu>/<subtopik>/... (rekursif)."""
    sig = []
    if DATA_DIR.exists():
        for cat in CATEGORIES:
            d = DATA_DIR / cat
            if d.exists():
                for f in sorted(d.rglob("*")):
                    if f.is_file() and f.suffix.lower() in EXTS:
                        s = f.stat()
                        rel = f.relative_to(d)
                        sub = rel.parts[0] if len(rel.parts) > 1 else "Umum"
                        sig.append((cat, sub, rel.as_posix(), s.st_size, int(s.st_mtime)))
    return tuple(sig)


HEADER_SPLIT = re.compile(r"^={10,}\s*$", re.M)


def split_header(text: str):
    """Pisahkan header (JUDUL/MENU/SUMBER) dari isi materi."""
    parts = HEADER_SPLIT.split(text, maxsplit=1)
    if len(parts) == 2 and "JUDUL:" in parts[0]:
        meta = dict(re.findall(r"^(JUDUL|MENU|SUMBER):\s*(.+)$", parts[0], re.M))
        return meta, parts[1].strip()
    return {}, text


# Ejaan transliterasi Latin mengikuti Pedoman SKB Menag 158/1987 yang dipakai
# buku MIZAN. Judul berkas dan baris MENU lama ditulis tanpa tanda panjang;
# di sini diseragamkan saat ditampilkan, tanpa menyunting berkas materinya.
EJAAN_LATIN = {
    "Ibarah": "Ibārah",
    "Mufradat": "Mufradāt",
    "Kosa Kata": "Kosakata",
    "Muqadimah": "Muqaddimah",
    "Qadhiyyah": "Qaḍiyyah",
    "Hujjah": "Ḥujjah",
}
_EJAAN_RE = re.compile(r"\b(" + "|".join(sorted(EJAAN_LATIN, key=len, reverse=True)) + r")\b")


def rapikan_ejaan(t: str) -> str:
    """Seragamkan transliterasi Arab-Latin pada teks yang tampil di layar."""
    return _EJAAN_RE.sub(lambda m: EJAAN_LATIN[m.group(0)], t or "")


def make_doc(cat, sub, source, text, origin):
    meta, _ = split_header(text)
    menu = meta.get("MENU", "")
    if "›" in menu:  # nama subtopik lengkap (dengan bahasa Arab) diambil dari header file
        sub = menu.split("›", 1)[1].strip() or sub
    return {"cat": cat, "sub": rapikan_ejaan(sub), "source": rapikan_ejaan(source),
            "text": text, "origin": origin,
            "title": rapikan_ejaan(meta.get("JUDUL", source))}


@st.cache_data(show_spinner=False)
def load_disk_docs(signature):
    docs = []
    for cat, sub, rel, _, _ in signature:
        path = DATA_DIR / cat / rel
        try:
            text = extract_text(path.name, path.read_bytes())
        except Exception:
            text = ""
        if text.strip():
            docs.append(make_doc(cat, sub, Path(rel).stem, text, "repo"))
    return docs


def build_kb(docs):
    chunks = []
    for d in docs:
        meta, body = split_header(d["text"])
        tag = f"({d['sub']} › {d['title']})\n" if meta else ""
        for c in chunk_text(body):
            chunks.append({"cat": d["cat"], "sub": d["sub"], "source": d["source"], "text": tag + c})
    kb = {"docs": docs, "chunks": chunks, "vec": None, "mat": None}
    if chunks:
        vec = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            preprocessor=normalize_text,
            sublinear_tf=True,
            min_df=1,
            dtype=np.float32,
        )
        texts = [c["text"] for c in chunks]
        kb["mat"] = vec.fit_transform(texts)
        kb["vec"] = vec
        wvec = TfidfVectorizer(
            analyzer="word",
            token_pattern=r"(?u)\b\w\w+\b",
            preprocessor=normalize_text,
            sublinear_tf=True,
            dtype=np.float32,
        )
        kb["wmat"] = wvec.fit_transform(texts)
        kb["wvec"] = wvec
    return kb


@st.cache_resource(show_spinner="Menyiapkan basis pengetahuan MUNĀẒIR…")
def build_disk_kb(signature):
    return build_kb(load_disk_docs(signature))


def get_kb():
    sig = disk_signature()
    uploads = st.session_state.get("uploads", [])
    if not uploads:
        return build_disk_kb(sig)
    key = hashlib.md5(repr((sig, [(d["cat"], d["source"], len(d["text"])) for d in uploads])).encode()).hexdigest()
    if st.session_state.get("kb_sig") != key:
        st.session_state["kb"] = build_kb(list(load_disk_docs(sig)) + list(uploads))
        st.session_state["kb_sig"] = key
    return st.session_state["kb"]


def search(kb, query: str, k: int = 6, cats=None, min_score: float = 0.04):
    if not kb["chunks"] or not query.strip():
        return []
    query = clean_query(query)
    if re.search(r"\bpoi\b|interupsi|interruption|point of information", query, re.I) or "شار" in normalize_text(query) \
            or "مداخل" in normalize_text(query):
        query += " POI نقطة الاستشارة المداخلة المداخلات"
    scores = (kb["mat"] @ kb["vec"].transform([query]).T).toarray().ravel()
    if kb.get("wvec") is not None:  # gabungan pencarian huruf (char) + kata (word)
        scores = 0.5 * scores + 0.5 * (kb["wmat"] @ kb["wvec"].transform([query]).T).toarray().ravel()
    results = []
    for i in np.argsort(-scores):
        if scores[i] < min_score:
            break
        c = kb["chunks"][i]
        if cats and c["cat"] not in cats:
            continue
        results.append({**c, "score": float(scores[i])})
        if len(results) >= k:
            break
    return results


# ─────────────────────────────────────────────────────────────
# GROQ AI
# ─────────────────────────────────────────────────────────────
def _secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default) or default)
    except Exception:
        return default


def get_api_key() -> str:
    return _secret("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY", "") or st.session_state.get("user_api_key", "")


@st.cache_resource(show_spinner=False)
def get_client(api_key: str):
    from groq import Groq

    return Groq(api_key=api_key)


@st.cache_data(ttl=3600, show_spinner=False)
def available_models(api_key: str):
    try:
        return sorted(m.id for m in get_client(api_key).models.list().data)
    except Exception:
        return []


def candidate_models(api_key: str):
    avail = available_models(api_key)
    pref = [m for m in [st.session_state.get("model_choice"), _secret("GROQ_MODEL")] if m and m != "Otomatis"]
    pref += PREFERRED_MODELS
    if avail:
        cands = [m for m in pref if m in avail]
        cands += [m for m in avail if m not in cands and not any(b in m.lower() for b in BLOCKED_MODEL_WORDS)]
    else:
        cands = pref
    seen, out = set(), []
    for m in cands:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def call_llm(messages, temperature: float = 0.3, max_tokens: int = 1800) -> str:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("API key Groq belum diatur. Isi di menu samping atau di Secrets Streamlit (GROQ_API_KEY).")
    client = get_client(api_key)
    last_err = None
    for model in candidate_models(api_key)[:5]:
        try:
            resp = client.chat.completions.create(
                model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
            )
            text = resp.choices[0].message.content or ""
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
            st.session_state["active_model"] = model
            return text
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            if "invalid api key" in msg or "invalid_api_key" in msg or "401" in msg:
                raise RuntimeError("API key Groq tidak valid / sudah dicabut. Buat key baru di console.groq.com.")
            continue  # model tidak tersedia / kena limit → coba model berikutnya
    raise RuntimeError(f"Gagal menghubungi Groq: {last_err}")


SYSTEM_CHAT = """Kamu adalah MUNĀẒIR (مُنَاظِرٌ), asisten AI panduan dan pedoman debat bahasa Arab (munazarah).
Tugasmu membantu pengguna menemukan materi dari BASIS PENGETAHUAN MUNĀẒIR: sistem debat, mosi, ibarah, kosa kata, dan muqaddimah.
KONTEKS berisi potongan [Materi …] dari file materi resmi MUNĀẒIR. Itulah SATU-SATUNYA sumber yang boleh kamu pakai.

ATURAN:
1. Jawab HANYA berdasarkan KONTEKS [Materi …]. Jangan memakai pengetahuanmu sendiri, internet, atau sumber lain,
   dan jangan mengarang materi yang tidak ada di konteks.
2. Jika konteks tidak memuat jawabannya, katakan dengan sopan bahwa materi tersebut belum tersedia di MUNĀẒIR.
   Untuk salam/sapaan, balas singkat dan ramah.
3. Penjelasan ditulis dalam bahasa Indonesia yang jelas dan rapi (boleh memakai poin-poin).
4. Bagian ARAB berisi kutipan teks Arab dari konteks yang relevan dengan jawaban. Jangan mengubah kata-katanya,
   tetapi WAJIB lengkapi dengan harakat (syakal) penuh dan benar pada setiap huruf, termasuk harakat akhir (i'rab).
   Jika konteks tidak memuat teks Arab yang relevan, tulis "-".
5. Bagian SUMBER berisi nama file materi yang benar-benar dipakai, dipisahkan koma. Tulis "-" jika tidak ada.
6. Setiap kata atau istilah Arab yang muncul di bagian JAWABAN juga WAJIB diberi harakat lengkap.
7. ISTILAH POI: di MUNĀẒIR, istilah Arab untuk POI (Point of Information) adalah نُقْطَةُ الاِسْتِشَارَةِ.
   Di bagian JAWABAN selalu gunakan istilah ini. Jika konteks memakai الْمُدَاخَلَةُ / الْمُدَاخَلَاتُ,
   jelaskan bahwa itu sebutan lain untuk POI yang sama. Di bagian ARAB, kutipan dari konteks tetap apa adanya.

FORMAT WAJIB (gunakan penanda persis seperti ini):
[JAWABAN]
...penjelasan bahasa Indonesia...
[ARAB]
...teks Arab dari materi...
[SUMBER]
...nama file..."""

SYSTEM_EXPAND = """Ubah pertanyaan pengguna menjadi kata kunci pencarian dwibahasa.
Tulis dalam SATU baris: kata kunci bahasa Indonesia, lalu terjemahan/istilah bahasa Arab yang setara (istilah debat/munazarah).
Jangan menjawab pertanyaannya. Jangan beri penjelasan."""

SYSTEM_TRANSLATE = """Kamu adalah penerjemah ahli bahasa Indonesia ⇄ bahasa Arab fusha, khusus konteks debat (munazarah).
Jika GLOSARIUM diberikan, utamakan istilah baku dari glosarium tersebut.
Istilah POI (Point of Information/interupsi dalam debat) SELALU diterjemahkan menjadi نُقْطَةُ الاِسْتِشَارَةِ.
Terjemahkan secara akurat, alami, dan sesuai gaya bahasa debat formal.
Setiap teks Arab yang kamu tulis (hasil terjemahan maupun istilah di catatan) WAJIB diberi harakat (syakal) lengkap dan benar.

FORMAT WAJIB:
[TERJEMAHAN]
...hasil terjemahan saja...
[CATATAN]
...maksimal 5 poin singkat (bahasa Indonesia) tentang istilah penting / alternatif kata. Tulis "-" jika tidak perlu."""


@st.cache_data(ttl=3600, show_spinner=False)
def _expand_query_cached(question: str, _key_marker: str) -> str:
    return call_llm(
        [{"role": "system", "content": SYSTEM_EXPAND}, {"role": "user", "content": question}],
        temperature=0.0,
        max_tokens=120,
    )


def expand_query(question: str) -> str:
    """Terjemahkan pertanyaan ke kata kunci Arab agar file berbahasa Arab tetap ketemu."""
    try:
        return _expand_query_cached(question, get_api_key()[-6:])
    except Exception:
        return ""


def build_context(chunks, limit_chars: int = 6000) -> str:
    out, total = [], 0
    for i, c in enumerate(chunks, 1):
        block = f"[Materi {i}: {c['source']} | Menu: {CATEGORIES[c['cat']]['label']}]\n{c['text']}"
        if total + len(block) > limit_chars and out:
            break
        out.append(block)
        total += len(block)
    return "\n\n---\n\n".join(out)


def answer_question(question: str, cats=None, history=None):
    """Jawab pertanyaan HANYA dari materi MUNĀẒIR (tanpa pencarian internet)."""
    kb = get_kb()
    expansion = expand_query(question) if kb["chunks"] else ""
    hits = search(kb, f"{question}\n{expansion}", k=6, cats=cats)
    context = build_context(hits) if hits else "(tidak ada materi yang cocok di basis pengetahuan)"
    messages = [{"role": "system", "content": SYSTEM_CHAT}]
    for h in (history or [])[-4:]:
        if h["role"] == "user":
            messages.append({"role": "user", "content": h["content"]})
        elif h.get("raw"):
            messages.append({"role": "assistant", "content": h["raw"][:1500]})
    messages.append({"role": "user", "content": f"KONTEKS:\n{context}\n\nPERTANYAAN:\n{question}"})
    raw = call_llm(messages)
    parsed = lengkapi_harakat(parse_sections(raw, ("JAWABAN", "ARAB", "SUMBER")))
    return raw, parsed, hits


def parse_sections(raw: str, tags):
    pattern = r"\**\s*\[(" + "|".join(tags) + r")\]\s*\**:?"
    pieces = re.split(pattern, raw)
    out = {t: "" for t in tags}
    if len(pieces) == 1:
        out[tags[0]] = raw.strip()
        return out
    if pieces[0].strip():
        out[tags[0]] = pieces[0].strip()
    for i in range(1, len(pieces) - 1, 2):
        out[pieces[i]] = (out[pieces[i]] + "\n" + pieces[i + 1]).strip()
    return out


# ─────────────────────────────────────────────────────────────
# HARAKAT OTOMATIS (tasykil) untuk SEMUA teks Arab — berjalan di LATAR BELAKANG
# - Pengunjung TIDAK PERNAH menunggu: halaman langsung tampil dengan harakat yang sudah ada.
# - Sebuah "pekerja" di server memberi harakat pada seluruh materi secara otomatis, sedikit demi sedikit,
#   memakai AI Groq. Hasil dicek: kalau AI mengubah kata, hasil ditolak & dicoba lagi.
# - Hasil disimpan di  harakat_cache.json  dan (bila GITHUB_TOKEN diisi di Secrets) otomatis disimpan
#   ke repository GitHub, sehingga harakat permanen walaupun aplikasi di-restart. Tanpa unduh-unggah manual.
#
# PERBAIKAN (versi ini):
# 1. Model yang tidak ditemukan / sudah dihentikan Groq tidak lagi mengunci SEMUA model selama 24 jam.
#    Daftar model dibaca ulang dari Groq setiap 30 menit, dan model cadangan dipakai otomatis.
# 2. Jatah AI tidak lagi dihabiskan oleh Chat: cuplikan materi di chat tidak diberi harakat lewat AI
#    (cukup memakai hasil pekerja), sehingga jatah harian Groq dipakai untuk menyelesaikan materi.
# 3. Hasil disimpan ke GitHub setiap 10 menit (bukan 30 menit), jadi progres tidak hilang saat restart.
# 4. Panel Kelola Materi menampilkan model yang dipakai, galat terakhir, dan tombol "Coba lagi sekarang".
# ─────────────────────────────────────────────────────────────
HARAKAT_CACHE_FILE = APP_DIR / "harakat_cache.json"
HARAKAT_SEGMEN = 320        # panjang maksimal satu potongan teks Arab
HARAKAT_BATCH_CHARS = 700   # jumlah huruf Arab per sekali panggil AI (lebih kecil = lebih jarang kena batas per menit)
HARAKAT_PARALEL = 2         # jumlah panggilan AI yang berjalan bersamaan
HARAKAT_MAKS_GAGAL = 3      # potongan yang gagal 3x dibiarkan apa adanya (sampai tombol "Coba lagi" ditekan)
HARAKAT_SIMPAN_GITHUB = 600  # simpan ke GitHub tiap 10 menit bila ada hasil baru
HARAKAT_SEGARKAN_MODEL = 1800  # baca ulang daftar model Groq tiap 30 menit
# Urutan model untuk harakat (yang tidak tersedia di akun Groq otomatis dilewati)
HARAKAT_MODELS = [
    "moonshotai/kimi-k2-instruct-0905",
    "moonshotai/kimi-k2-instruct",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "allam-2-7b",
]
# Model yang tidak dipakai untuk harakat (bukan model teks, atau terlalu kecil sehingga harakatnya sering salah)
HARAKAT_TOLAK = BLOCKED_MODEL_WORDS + ("8b", "20b", "1b", "3b", "vision", "embed")

SYSTEM_HARAKAT = """Kamu adalah ahli nahwu dan sharaf bahasa Arab. Tugasmu HANYA memberi harakat (tasykil/syakal)
yang lengkap dan benar pada teks Arab.

ATURAN:
1. JANGAN mengubah, menambah, menghapus, menukar, atau menerjemahkan kata apa pun. Urutan kata harus sama persis,
   walaupun ada kata yang tampak salah ketik.
2. Pertahankan tanda baca, angka, simbol, dan kata non-Arab persis seperti aslinya.
3. Beri harakat pada SETIAP huruf: fathah, kasrah, dammah, sukun, syaddah, tanwin, termasuk harakat akhir (i'rab)
   sesuai kedudukannya dalam kalimat.
4. Setiap baris diawali penanda [[nomor]]. Tulis ulang SETIAP baris dengan penanda yang sama, satu baris per penanda.
5. Jangan menulis penjelasan, salam, atau teks lain apa pun."""


@st.cache_resource(show_spinner=False)
def _gudang_harakat() -> dict:
    """Gudang hasil harakat {md5(teks asli): teks berharakat}, dipakai bersama semua pengunjung."""
    try:
        data = json.loads(HARAKAT_CACHE_FILE.read_text("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


@st.cache_resource(show_spinner=False)
def _gagal_harakat() -> dict:
    """Hitungan gagal per potongan (agar potongan bermasalah tidak dicoba terus-menerus)."""
    return {}


def _simpan_gudang(g: dict = None):
    """Simpan gudang ke harakat_cache.json. 'g' dikirim langsung bila dipanggil dari thread pekerja."""
    try:
        data = g if g is not None else _gudang_harakat()
        tmp = HARAKAT_CACHE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(dict(data), ensure_ascii=False), "utf-8")
        tmp.replace(HARAKAT_CACHE_FILE)
    except Exception:
        pass


def _kunci(t: str) -> str:
    return hashlib.md5(t.encode("utf-8")).hexdigest()


def rasio_arab(t: str) -> float:
    letters = [c for c in t if c.isalpha()]
    return len(AR_CHARS.findall("".join(letters))) / len(letters) if letters else 0.0


def _baris_arab_utuh(s: str) -> bool:
    """Baris yang (hampir) seluruhnya Arab diproses utuh; baris header (JUDUL/MENU/SUMBER) dan baris campuran per potongan."""
    return rasio_arab(s) > 0.75 and not re.match(r"^(JUDUL|MENU|SUMBER):", s)


def perlu_harakat(t: str) -> bool:
    """True bila teks berisi kata Arab yang harakatnya masih sedikit / belum ada."""
    huruf = len(AR_HURUF_DASAR.findall(t or ""))
    if huruf < 2:
        return False
    return len(AR_TANDA_HARAKAT.findall(t)) < 0.45 * huruf


def _potong(s: str):
    """Potong teks Arab panjang menjadi bagian ≤ HARAKAT_SEGMEN huruf, di tanda baca atau spasi.
    Selalu berlaku:  "".join(_potong(s)) == s"""
    if len(s) <= HARAKAT_SEGMEN:
        return [s]
    kecil = []
    for k in re.split(r"(?<=[.،؛!?؟:])(?=\s)", s):
        while len(k) > HARAKAT_SEGMEN:
            cut = k.rfind(" ", 1, HARAKAT_SEGMEN)
            cut = cut if cut > 0 else HARAKAT_SEGMEN
            kecil.append(k[:cut])
            k = k[cut:]
        if k:
            kecil.append(k)
    hasil, cur = [], ""
    for k in kecil:
        if cur and len(cur) + len(k) > HARAKAT_SEGMEN:
            hasil.append(cur)
            cur = k
        else:
            cur += k
    if cur:
        hasil.append(cur)
    return hasil


def _bagian_arab(s: str):
    """Bagian Arab di satu baris (sudah di-strip): baris utuh atau potongan-potongan Arab di baris campuran."""
    return [s] if _baris_arab_utuh(s) else [m.group(0) for m in AR_RUN.finditer(s)]


def kumpulkan_arab(text: str):
    """Semua potongan Arab di teks yang perlu harakat (urutan tetap, tanpa dobel)."""
    hasil = []
    for line in (text or "").split("\n"):
        s = line.strip()
        if not s or not AR_CHARS.search(s):
            continue
        for b in _bagian_arab(s):
            for p in _potong(b):
                p = p.strip()
                if p and perlu_harakat(p):
                    hasil.append(p)
    return list(dict.fromkeys(hasil))


def _ganti_bagian(b: str, g: dict) -> str:
    out = []
    for p in _potong(b):
        s = p.strip()
        v = g.get(_kunci(s)) if s else None
        out.append(p.replace(s, v, 1) if v else p)
    return "".join(out)


_H = "[\u064B-\u0652\u0670]*"  # harakat opsional di antara huruf
# "نقطة الاستشار" (tanpa tā' marbūṭah, dengan/tanpa harakat) → kata keduanya diganti bentuk baku الاِسْتِشَارَةِ.
# Kata pertama (نقطة) tidak disentuh, agar harakat akhirnya (i'rab) tetap sesuai kalimat.
POI_SALAH = re.compile(
    "(ن" + _H + "ق" + _H + "ط" + _H + "[ةه]" + _H + "\\s+)"
    + "[اٱإ]" + _H + "ل" + _H + "[اٱإ]" + _H + "س" + _H + "ت" + _H + "ش" + _H + "ا" + _H + "ر" + _H
    + "(?![ةهت\u0621-\u064A])"
)
ADA_MUDAKHALAH = re.compile("م" + _H + "د" + _H + "ا" + _H + "خ" + _H + "ل" + _H + "(?:[ةه]|ات)")


def seragamkan_poi(text: str) -> str:
    """Samakan penulisan istilah POI: نقطة الاستشار → نقطة الاِسْتِشَارَةِ."""
    if not text or "ش" not in text:
        return text or ""
    return POI_SALAH.sub(lambda m: m.group(1) + "الاِسْتِشَارَةِ", text)


def terapkan_harakat(text: str) -> str:
    """Ganti teks Arab dengan versi berharakat yang sudah ada di gudang (tanpa memanggil AI)."""
    return seragamkan_poi(_terapkan_harakat(text))


def _terapkan_harakat(text: str) -> str:
    g = _gudang_harakat()
    if not g or not text:
        return text or ""
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or not AR_CHARS.search(s):
            out.append(line)
        elif _baris_arab_utuh(s):
            out.append(line.replace(s, _ganti_bagian(s, g), 1))
        else:
            out.append(AR_RUN.sub(lambda m: _ganti_bagian(m.group(0), g), line))
    return "\n".join(out)


def _kerangka(t: str) -> str:
    """Huruf Arab saja (tanpa harakat, spasi & tanda baca) untuk membandingkan teks asli dan hasil AI."""
    return re.sub(r"[^ء-ي]", "", normalize_text(t))


def _harakat_sah(asli: str, hasil: str) -> bool:
    if not hasil or perlu_harakat(hasil):
        return False
    a, b = _kerangka(asli), _kerangka(hasil)
    if not a or not b:
        return False
    if a == b:
        return True
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() >= 0.93


def _kelompokkan(items):
    batch, panjang = [], 0
    for t in items:
        if batch and panjang + len(t) > HARAKAT_BATCH_CHARS:
            yield batch
            batch, panjang = [], 0
        batch.append(t)
        panjang += len(t)
    if batch:
        yield batch


def _susun_model_harakat(tersedia) -> list:
    """Urutan model untuk harakat dari daftar model yang BENAR-BENAR tersedia di akun Groq."""
    tersedia = list(tersedia or [])
    if not tersedia:
        return list(HARAKAT_MODELS)
    pilih = [m for m in HARAKAT_MODELS if m in tersedia]
    pilih += sorted(m for m in tersedia if m not in pilih and not any(x in m.lower() for x in HARAKAT_TOLAK))
    return pilih or list(HARAKAT_MODELS)


def _model_harakat(api_key: str):
    return _susun_model_harakat(available_models(api_key))


def _jeda_dari_galat(pesan: str) -> float:
    """Baca 'try again in 1h2m3.5s' / 'try again in 850ms' dari pesan batas Groq → detik (bawaan 5 menit)."""
    m = re.search(r"try again in\s*([\d.]+)\s*ms", pesan)
    if m:
        return float(m.group(1)) / 1000 + 2
    m = re.search(r"try again in\s*(?:(\d+)h)?\s*(?:(\d+)m(?!s))?\s*(?:([\d.]+)s)?", pesan)
    if m and any(m.groups()):
        h, mnt, dt = (float(x) if x else 0.0 for x in m.groups())
        return h * 3600 + mnt * 60 + dt + 2
    return 300.0


def _opsi_model(model: str) -> dict:
    """Pengaturan khusus untuk model 'reasoning' agar langsung menulis jawaban tanpa berpikir panjang."""
    m = model.lower()
    if "gpt-oss" in m:
        return {"reasoning_effort": "low"}
    if "qwen3" in m:
        return {"reasoning_effort": "none"}
    return {}


def _llm_harakat(client, models, batch, jeda=None, catatan=None) -> str:
    """Satu panggilan AI untuk satu kelompok potongan (aman dijalankan di thread terpisah).
    'jeda'    = {model: waktu_boleh_dipakai_lagi}; model yang kena batas dilewati sementara.
    'catatan' = dict untuk mencatat galat terakhir (ditampilkan di panel Kelola Materi)."""
    import time
    isi = "\n".join(f"[[{i}]] {t}" for i, t in enumerate(batch, 1))
    galat = None
    for model in models:
        if jeda is not None and jeda.get(model, 0) > time.time():
            continue
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": SYSTEM_HARAKAT}, {"role": "user", "content": isi}],
                temperature=0.0,
                max_tokens=min(8000, int(sum(len(t) for t in batch) * 3) + 300),
                **_opsi_model(model),
            )
            text = re.sub(r"<think>.*?</think>", "", resp.choices[0].message.content or "", flags=re.S).strip()
            if text:
                if catatan is not None:
                    catatan["model_terakhir"] = model
                return text
        except Exception as e:  # model tidak tersedia / kena limit → coba model berikutnya
            galat = e
            pesan = str(e).lower()
            if catatan is not None:
                catatan["galat"] = f"{model}: {str(e)[:220]}"
            if "invalid api key" in pesan or "invalid_api_key" in pesan or "401" in pesan:
                break
            if jeda is not None:
                if "429" in pesan or "rate limit" in pesan or "rate_limit" in pesan:
                    jeda[model] = time.time() + _jeda_dari_galat(str(e))
                elif "reasoning_effort" in pesan or "unsupported" in pesan:
                    jeda[model] = time.time() + 600  # pengaturan tidak didukung → lewati sebentar
                elif "decommissioned" in pesan or "model_not_found" in pesan or "does not exist" in pesan:
                    jeda[model] = time.time() + 6 * 3600  # model dihentikan → daftar model dibaca ulang nanti
                else:
                    jeda[model] = time.time() + 60
    raise RuntimeError(f"Groq: {galat}")


def beri_harakat(items, progres=None, maks_panggilan=None) -> int:
    """Beri harakat pada potongan-potongan teks Arab yang belum ada di gudang.
    Mengembalikan jumlah potongan yang masih BELUM berharakat (0 = semua selesai)."""
    g, gagal = _gudang_harakat(), _gagal_harakat()

    def masih(t):
        k = _kunci(t)
        return k not in g and gagal.get(k, 0) < HARAKAT_MAKS_GAGAL

    sisa = [t for t in dict.fromkeys(x.strip() for x in items) if t and masih(t)]
    api_key = get_api_key()
    if not sisa or not api_key:
        return len(sisa)
    batches = list(_kelompokkan(sisa))
    if maks_panggilan is not None:
        batches = batches[:maks_panggilan]
    try:
        client = get_client(api_key)
        models = _model_harakat(api_key)
    except Exception as e:
        st.session_state["harakat_galat"] = str(e)
        return len(sisa)

    from concurrent.futures import ThreadPoolExecutor, as_completed

    jeda = pekerja_harakat()["jeda"]  # berbagi catatan batas dengan pekerja latar belakang
    beres = 0
    with ThreadPoolExecutor(max_workers=HARAKAT_PARALEL) as ex:
        tugas = {ex.submit(_llm_harakat, client, models, b, jeda): b for b in batches}
        for f in as_completed(tugas):
            batch = tugas[f]
            beres += 1
            try:
                raw = f.result()
            except Exception as e:  # kena limit / jaringan → sisanya dicoba lain kali
                st.session_state["harakat_galat"] = str(e)
                raw = None
            if raw:
                bagian = re.split(r"\[\[(\d+)\]\]", raw)
                jawab = {int(bagian[i]): bagian[i + 1].strip() for i in range(1, len(bagian) - 1, 2)}
                for i, asli in enumerate(batch, 1):
                    hasil = jawab.get(i, "")
                    k = _kunci(asli)
                    if _harakat_sah(asli, hasil):
                        g[k] = hasil
                    else:
                        gagal[k] = gagal.get(k, 0) + 1
            if progres:
                progres(beres / len(batches))
    _simpan_gudang(g)
    return sum(1 for t in sisa if masih(t))


def harakati(text: str, maks_panggilan: int = 2) -> str:
    """Teks pendek yang diketik pengguna (mis. di Penerjemah): beri harakat langsung, lalu kembalikan hasilnya."""
    if not text:
        return text or ""
    try:
        beri_harakat(kumpulkan_arab(text), maks_panggilan=maks_panggilan)
    except Exception:
        pass
    return terapkan_harakat(text)


# ── PEKERJA LATAR BELAKANG ───────────────────────────────────
def _urutan_kerja(docs):
    """Daftar potongan Arab seluruh materi, berurutan: judul/subtopik dulu, lalu materi pendek ke panjang."""
    items = []
    for d in docs:
        items += kumpulkan_arab(d["sub"]) + kumpulkan_arab(d["source"])
        meta, _ = split_header(d["text"])
        items += kumpulkan_arab("\n".join(meta.values()))
    for d in sorted(docs, key=lambda d: (d["cat"] not in ("mosi", "ibarah", "kosakata", "muqaddimah"), len(d["text"]))):
        items += kumpulkan_arab(d["text"])
    return list(dict.fromkeys(items))


def _gabung_dari_github(cfg: dict, g: dict):
    """Saat pekerja mulai: ambil harakat_cache.json terbaru dari GitHub, agar progres sebelumnya tidak hilang."""
    import base64
    import requests

    url = f"https://api.github.com/repos/{cfg['repo']}/contents/{cfg['path']}"
    kepala = {"Authorization": f"Bearer {cfg['token']}", "Accept": "application/vnd.github.raw+json"}
    try:
        r = requests.get(url, headers=kepala, params={"ref": cfg["branch"]}, timeout=60)
        if r.status_code == 200:
            try:
                data = r.json()
                if isinstance(data, dict) and "content" in data and "sha" in data:  # bukan format mentah
                    data = json.loads(base64.b64decode(data["content"]).decode("utf-8"))
            except Exception:
                data = json.loads(r.text)
            if isinstance(data, dict):
                for k, v in data.items():
                    g.setdefault(k, v)
    except Exception:
        pass


def _simpan_ke_github(cfg: dict, data: dict, status: dict) -> bool:
    """Simpan harakat_cache.json ke repository GitHub (butuh GITHUB_TOKEN & GITHUB_REPO di Secrets)."""
    import base64
    import time
    import requests

    url = f"https://api.github.com/repos/{cfg['repo']}/contents/{cfg['path']}"
    kepala = {"Authorization": f"Bearer {cfg['token']}", "Accept": "application/vnd.github+json"}
    try:
        lama = requests.get(url, headers=kepala, params={"ref": cfg["branch"]}, timeout=30)
        sha = lama.json().get("sha") if lama.status_code == 200 else None
        isi = base64.b64encode(json.dumps(dict(data), ensure_ascii=False).encode("utf-8")).decode("ascii")
        body = {"message": f"Harakat otomatis: {len(data):,} potongan", "content": isi, "branch": cfg["branch"]}
        if sha:
            body["sha"] = sha
        r = requests.put(url, headers=kepala, json=body, timeout=90)
        if r.status_code in (200, 201):
            status["github"] = f"tersimpan ke GitHub ({time.strftime('%d-%m %H:%M')} UTC, {len(data):,} potongan)"
            return True
        status["github"] = f"gagal menyimpan ke GitHub (kode {r.status_code}: {r.text[:120]})"
    except Exception as e:
        status["github"] = f"gagal menyimpan ke GitHub ({e})"
    return False


def _jalankan_pekerja(state: dict, g: dict, gagal: dict, api_key: str, cfg_github: dict):
    """Loop di thread terpisah: beri harakat sedikit demi sedikit sampai semua materi selesai."""
    import time
    from concurrent.futures import ThreadPoolExecutor

    status, jeda = state["status"], state["jeda"]
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
    except Exception as e:
        status["keadaan"] = f"berhenti: {e}"
        return
    if cfg_github:
        status["keadaan"] = "mengambil hasil harakat sebelumnya dari GitHub"
        _gabung_dari_github(cfg_github, g)

    models, waktu_model = [], 0.0
    docs_lama, items = None, []
    terakhir_simpan = time.time()
    perubahan = 0
    while True:
        try:
            if not models or time.time() - waktu_model > HARAKAT_SEGARKAN_MODEL or state.get("segarkan"):
                state["segarkan"] = False
                try:
                    models = _susun_model_harakat(m.id for m in client.models.list().data)
                except Exception:
                    models = models or list(HARAKAT_MODELS)
                waktu_model = time.time()
                status["model"] = ", ".join(models)
            if state["docs"] is not docs_lama:  # ada materi baru → susun ulang antrean
                docs_lama = state["docs"]
                items = _urutan_kerja(docs_lama)
            sisa = [t for t in items if _kunci(t) not in g and gagal.get(_kunci(t), 0) < HARAKAT_MAKS_GAGAL]
            status.update(total=len(items), selesai=len(items) - len(sisa))
            if not sisa:
                status["keadaan"] = "selesai — semua teks Arab sudah berharakat"
                if perubahan and cfg_github and _simpan_ke_github(cfg_github, g, status):
                    perubahan = 0
                time.sleep(120)
                continue
            aktif = [m for m in models if jeda.get(m, 0) <= time.time()]
            if not aktif:
                tunggu = max(5.0, min(jeda.get(m, 0) for m in models) - time.time())
                status["keadaan"] = f"menunggu batas AI Groq pulih (±{int(tunggu // 60)} menit)"
                if perubahan and cfg_github and _simpan_ke_github(cfg_github, g, status):
                    terakhir_simpan, perubahan = time.time(), 0
                # tidur sebentar-sebentar agar tombol "Coba lagi sekarang" langsung berpengaruh
                akhir = time.time() + min(tunggu, 600)
                while time.time() < akhir and not state.get("segarkan"):
                    time.sleep(5)
                continue
            status["keadaan"] = f"sedang memberi harakat ({len(aktif)} model siap)"
            batches = list(_kelompokkan(sisa[: HARAKAT_PARALEL * 10]))[:HARAKAT_PARALEL]
            with ThreadPoolExecutor(max_workers=HARAKAT_PARALEL) as ex:
                hasil_semua = list(ex.map(lambda b: _coba_batch(client, aktif, b, jeda, status), batches))
            for batch, raw in zip(batches, hasil_semua):
                if not raw:
                    continue
                bagian = re.split(r"\[\[(\d+)\]\]", raw)
                jawab = {int(bagian[i]): bagian[i + 1].strip() for i in range(1, len(bagian) - 1, 2)}
                for i, asli in enumerate(batch, 1):
                    k = _kunci(asli)
                    if _harakat_sah(asli, jawab.get(i, "")):
                        g[k] = jawab[i]
                        perubahan += 1
                    else:
                        gagal[k] = gagal.get(k, 0) + 1
            _simpan_gudang(g)
            if cfg_github and perubahan and time.time() - terakhir_simpan > HARAKAT_SIMPAN_GITHUB:
                if _simpan_ke_github(cfg_github, g, status):
                    terakhir_simpan, perubahan = time.time(), 0
            time.sleep(1)
        except Exception as e:  # jangan sampai pekerja mati karena satu galat
            status["keadaan"] = f"galat sementara: {e}"
            time.sleep(60)


def _coba_batch(client, models, batch, jeda, catatan=None):
    try:
        return _llm_harakat(client, models, batch, jeda, catatan)
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def pekerja_harakat():
    """Status & data bersama pekerja latar belakang (dibuat sekali per server)."""
    return {"docs": None, "jeda": {}, "segarkan": False, "thread": None,
            "status": {"keadaan": "belum berjalan", "total": 0, "selesai": 0, "github": "", "model": "",
                       "model_terakhir": "", "galat": ""}}


def mulai_pekerja_harakat(docs):
    """Dipanggil setiap halaman dimuat: perbarui daftar materi & pastikan pekerja berjalan (cepat, tidak menunggu)."""
    import threading

    state = pekerja_harakat()
    state.setdefault("jeda", {})
    state["docs"] = docs
    th = state.get("thread")
    if th is not None and th.is_alive():
        return state
    api_key = get_api_key()
    if not api_key:
        state["status"]["keadaan"] = "belum berjalan: API key Groq belum diatur"
        return state
    cfg = {}
    if _secret("GITHUB_TOKEN") and _secret("GITHUB_REPO"):
        cfg = {"token": _secret("GITHUB_TOKEN"), "repo": _secret("GITHUB_REPO"),
               "branch": _secret("GITHUB_BRANCH", "main"), "path": _secret("GITHUB_PATH", "harakat_cache.json")}
    th = threading.Thread(target=_jalankan_pekerja, daemon=True,
                          args=(state, _gudang_harakat(), _gagal_harakat(), api_key, cfg))
    th.start()
    state["thread"] = th
    return state


def persen_harakat(text: str) -> float:
    """Persentase potongan Arab di teks yang sudah berharakat (0–100)."""
    items = kumpulkan_arab(text)
    if not items:
        return 100.0
    g = _gudang_harakat()
    return 100.0 * sum(1 for t in items if _kunci(t) in g) / len(items)


def lengkapi_harakat(parsed: dict, bagian=("JAWABAN", "ARAB", "SUMBER"), ekstra=(), maks_panggilan: int = 3) -> dict:
    """Pastikan teks Arab di jawaban / terjemahan AI berharakat lengkap.
    'ekstra' (mis. cuplikan materi) TIDAK lagi dikirim ke AI: cuplikan memakai hasil pekerja latar belakang,
    supaya jatah harian AI Groq tidak habis oleh chat."""
    items = []
    for b in bagian:
        if b != "SUMBER":
            items += kumpulkan_arab(parsed.get(b, ""))
    if items:
        try:
            beri_harakat(items, maks_panggilan=maks_panggilan)
        except Exception:
            return parsed
    return {b: (terapkan_harakat(v) if b != "SUMBER" else v) for b, v in parsed.items()}


# ─────────────────────────────────────────────────────────────
# TAMPILAN (sistem desain: kertas, tinta, kuningan)
# ─────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Aref+Ruqaa:wght@400;700&family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,500&family=Noto+Sans:wght@400;500;600&family=Noto+Serif:wght@400;500&display=swap');

/* ───────── Token desain ───────── */
:root{
  /* Tema zamrud & emas. Permukaan baca sengaja tetap terang:
     teks Arab berharakat dibaca lama, jadi tidak ditaruh di atas hijau tua. */
  --paper:#F4F0E7; --paper-2:#FFFFFF; --paper-3:#EAE6DA;
  --ink:#202824; --ink-2:#3C4B44; --muted:#4A5A52;
  --rule:#DCE7DF; --rule-soft:#E6EDE8;
  --umber:#102A27; --umber-2:#163B32; --cream:#F4F0E7;
  --brass:#C6A15B; --brass-ink:#6B5526; --brass-soft:rgba(198,161,91,.16);
  /* Amiri disisipkan sebagai cadangan: huruf Arab di tombol, menu, dan isian ikut memakai Amiri */
  /* 'Noto Serif'/'Noto Sans' dipasang sebagai cadangan karena Newsreader,
     IBM Plex Sans, dan Georgia tidak memuat huruf Ẓ (titik di bawah). */
  --serif:'Newsreader', 'Noto Serif', 'Amiri', Georgia, 'Times New Roman', serif;
  --sans:'IBM Plex Sans', 'Noto Sans', 'Amiri', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --arab:'Amiri', 'Traditional Arabic', 'Times New Roman', serif;
  /* Judul Arab memakai khat ruq'ah; harakatnya dilepas lewat tanpa_harakat() */
  --arab-judul:'Aref Ruqaa', 'Amiri', 'Traditional Arabic', serif;
  --ease:cubic-bezier(.2,.7,.2,1);
  --r:10px;
}

/* ───────── Dasar ───────── */
html, body, .stApp, [data-testid="stAppViewContainer"]{ background:var(--paper) !important; color:var(--ink); font-family:var(--sans); }
.stApp{ -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility; }
[data-testid="stMainBlockContainer"], .block-container{ max-width:1120px; padding-top:3.2rem; padding-bottom:3rem; }
h1, h2, h3, h4{ font-family:var(--serif) !important; color:var(--ink) !important; font-weight:500 !important; letter-spacing:-.01em; }
::selection{ background:rgba(165,122,44,.25); }
[lang="ar"]{ font-family:var(--arab); }
[data-testid="stHeader"]{ background:rgba(16,42,39,.94) !important; backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
  border-bottom:1px solid rgba(198,161,91,.38); }
/* Menu atas berlatar zamrud: tulisan dan ikonnya dibalik jadi gading, halaman aktif ditandai emas. */
[data-testid="stHeader"] a, [data-testid="stHeader"] span, [data-testid="stHeader"] p,
[data-testid="stHeader"] button, [data-testid="stHeader"] label{ color:var(--cream) !important; }
[data-testid="stHeader"] svg{ fill:currentColor !important; color:var(--cream) !important; }
[data-testid="stHeader"] a[aria-current="page"], [data-testid="stHeader"] a[aria-current="page"] span,
[data-testid="stHeader"] [aria-selected="true"], [data-testid="stHeader"] [aria-selected="true"] span{ color:var(--brass) !important; }
[data-testid="stHeader"] a:hover, [data-testid="stHeader"] button:hover{ background:rgba(244,240,231,.09) !important; }
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"]{ background:var(--paper) !important; }
[data-testid="stWidgetLabel"] p{ font-size:.85rem !important; font-weight:500 !important; color:var(--ink-2) !important; }
[data-testid="stCaptionContainer"]{ color:var(--muted) !important; }

/* ───────── Gerak (animasi) ─────────
   Animasi HANYA dipakai di bagian pembuka: layar pembuka (.splash) dan
   bagian atas Beranda saat website pertama kali dibuka (.intro).
   Halaman lain (memilih menu/tema, tab, panel, chat) tampil tanpa animasi. */
@keyframes rise{ from{ opacity:0; transform:translateY(14px); } to{ opacity:1; transform:none; } }
@keyframes draw{ from{ transform:scaleX(0); } to{ transform:scaleX(1); } }
@keyframes inkIn{ from{ clip-path:inset(0 0 0 100%); } to{ clip-path:inset(0 0 0 0); } }
@property --n{ syntax:'<integer>'; inherits:false; initial-value:0; }
@keyframes count{ from{ --n:0; } to{ --n:var(--to); } }
.rule-draw{ height:1px; background:var(--rule); }
.intro .reveal{ animation:rise .7s var(--ease) both; animation-delay:calc(var(--i, 0) * 90ms); }
.intro .rule-draw{ transform-origin:left; animation:draw 1s var(--ease) .2s both; }
.intro .ink-in{ animation:inkIn 1.3s var(--ease) .15s both; }
.count{ counter-reset:n var(--n); animation:count 1.6s var(--ease) .5s both; font-variant-numeric:tabular-nums; }
.count::after{ content:counter(n); }

/* ───────── Teks Arab: jarak & ruang untuk harakat ─────────
   - line-height besar agar harakat atas (fathah, dammah, syaddah) & bawah (kasrah) tidak terpotong / bertabrakan
   - word-spacing agar antarkata berjarak
   - letter-spacing 0 & tanpa huruf kapital: jarak antarhuruf memutus sambungan huruf Arab */
[lang="ar"], [dir="rtl"]{ font-family:var(--arab); line-height:2.3; word-spacing:.12em; letter-spacing:0 !important;
  text-transform:none !important; font-feature-settings:normal; }
.ar-in{ font-family:var(--arab); font-size:1.2em; line-height:2.3; margin:0 .4em; padding:.15em .15em; word-spacing:.12em;
  letter-spacing:0 !important; text-transform:none !important; font-weight:400; unicode-bidi:isolate; }
.stMarkdown p:has(.ar-in), .stMarkdown li:has(.ar-in), .snip div:has(.ar-in), .id-box:has(.ar-in), .subhead:has(.ar-in),
.doc p:has(.ar-in), .mm:has(.ar-in), .mosi-id:has(.ar-in), .q-id:has(.ar-in){ line-height:2.4; }
.subhead .ar-in, .eyebrow .ar-in, .mm .ar-in{ font-size:1.35em; color:inherit; }
/* teks Arab di dalam komponen Streamlit (pilihan, tombol, isian, tab) */
[role="option"], [data-baseweb="select"] [title], [data-baseweb="tab"] p, .stButton button p, [data-testid="stExpander"] summary p,
[data-testid="stWidgetLabel"] p, textarea, input{ line-height:1.9 !important; }
[role="option"]{ padding-top:.45rem !important; padding-bottom:.45rem !important; }
[data-baseweb="select"] > div{ min-height:2.9rem; }
textarea[dir="rtl"], textarea:lang(ar){ font-size:1.25rem !important; line-height:2.3 !important; }
.stCode code{ line-height:2.1 !important; word-spacing:.1em; }

/* ───────── Tipografi kecil ───────── */
.eyebrow{ font-family:var(--sans); font-size:.72rem; font-weight:600; letter-spacing:.14em; text-transform:uppercase; color:var(--brass-ink); }
.subhead{ font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; font-weight:600; color:var(--brass-ink); margin:1.1rem 0 .3rem; }
mark{ background:rgba(165,122,44,.22); color:inherit; padding:0 .1em; border-radius:2px; }

/* ───────── Judul halaman ───────── */
.ph{ margin:0 0 1.8rem; }
.ph-row{ display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:.8rem 2rem; margin:.7rem 0 1rem; }
.ph-t{ font-family:var(--serif); font-size:clamp(2rem, 4vw, 2.85rem); line-height:1.08; color:var(--ink); letter-spacing:-.02em; }
.ph-a{ font-family:var(--arab-judul); font-size:clamp(1.45rem, 3vw, 2rem); color:var(--brass-ink); line-height:2.2; padding:.45rem 0; word-spacing:.12em; }
.ph-d{ color:var(--muted); max-width:64ch; margin:0 0 1.3rem; line-height:1.65; }

/* ───────── Tombol ───────── */
.stButton button, .stFormSubmitButton button, .stDownloadButton button{
  background:var(--umber) !important; color:var(--cream) !important; border:1px solid var(--umber) !important;
  border-radius:8px !important; font-family:var(--sans) !important; min-height:2.6rem; padding:.5rem 1.15rem !important;
  box-shadow:none !important; transition:transform .15s var(--ease), background-color .2s, box-shadow .25s !important; }
.stButton button p, .stFormSubmitButton button p, .stDownloadButton button p{ color:inherit !important; font-weight:500 !important; }
.stButton button:hover, .stFormSubmitButton button:hover, .stDownloadButton button:hover{
  background:var(--umber-2) !important; transform:translateY(-1px); box-shadow:0 10px 20px -12px rgba(43,31,21,.6) !important; }
.stButton button:active, .stFormSubmitButton button:active{ transform:scale(.98); }
.stButton button:focus-visible, .stFormSubmitButton button:focus-visible, a:focus-visible{ outline:2px solid var(--brass) !important; outline-offset:2px; }
/* tombol sekunder (garis tepi) */
.st-key-aksi_sekunder button, [class*="st-key-contoh_chat"] button{
  background:transparent !important; color:var(--ink) !important; border:1px solid var(--rule) !important; }
.st-key-aksi_sekunder button:hover, [class*="st-key-contoh_chat"] button:hover{
  background:var(--paper-2) !important; border-color:var(--brass) !important; box-shadow:none !important; }
[class*="st-key-contoh_chat"] button{ border-radius:999px !important; width:100%; text-align:left; justify-content:flex-start; }
[class*="st-key-contoh_chat"] button p{ font-weight:400 !important; font-size:.9rem !important; }
/* daftar isi: judul seperti tautan */
[class*="st-key-toc_"]{ gap:0 !important; }
[class*="st-key-toc_"] .stButton button{ width:auto !important; min-height:0; padding:.3rem .2rem !important; background:transparent !important;
  border:none !important; color:var(--ink-2) !important; justify-content:flex-start !important; text-align:left !important; }
[class*="st-key-toc_"] .stButton button:hover{ color:var(--brass-ink) !important; transform:translateX(4px); box-shadow:none !important; }
[class*="st-key-toc_"] .stButton button p{ font-weight:400 !important; text-align:left; }
/* tombol tautan (formulir) */
[data-testid="stLinkButton"] a, a[data-testid^="stBaseLinkButton"]{ background:var(--paper-2) !important; border:1px solid var(--rule) !important;
  border-radius:8px !important; color:var(--ink) !important; transition:border-color .2s, transform .15s var(--ease) !important; }
[data-testid="stLinkButton"] a:hover, a[data-testid^="stBaseLinkButton"]:hover{ border-color:var(--brass) !important; transform:translateY(-1px); }
[data-testid="stLinkButton"] a p, a[data-testid^="stBaseLinkButton"] p{ color:var(--ink) !important; font-weight:500 !important; }

/* ───────── Isian ───────── */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div{
  background:var(--paper-2) !important; border:1px solid var(--rule) !important; border-radius:8px !important;
  transition:border-color .2s, box-shadow .2s !important; }
[data-baseweb="base-input"]{ background:transparent !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"] > div:focus-within{
  border-color:var(--brass) !important; box-shadow:0 0 0 3px var(--brass-soft) !important; }
input, textarea{ color:var(--ink) !important; font-family:var(--sans) !important; }
input::placeholder, textarea::placeholder{ color:#7E8E86 !important; }

/* ───────── Tab ───────── */
[data-baseweb="tab-list"]{ gap:1.8rem; border-bottom:1px solid var(--rule); }
[data-baseweb="tab"]{ background:transparent !important; padding:.65rem 0 !important; height:auto !important; }
[data-baseweb="tab"] p{ font-weight:500 !important; color:var(--muted) !important; font-size:.95rem !important; transition:color .2s; }
[data-baseweb="tab"]:hover p, [data-baseweb="tab"][aria-selected="true"] p{ color:var(--ink) !important; }
[data-baseweb="tab-highlight"]{ background:var(--ink) !important; height:2px !important; }
[data-baseweb="tab-border"]{ display:none !important; }
[data-baseweb="tab-panel"]{ padding-top:1.5rem !important; }

/* ───────── Panel lipat, info, unggah ───────── */
[data-testid="stExpander"] details{ background:var(--paper-2) !important; border:1px solid var(--rule) !important; border-radius:var(--r) !important; }
[data-testid="stExpander"] summary p{ font-weight:500 !important; color:var(--ink) !important; font-size:.92rem !important; transition:color .2s; }
[data-testid="stExpander"] summary:hover p{ color:var(--brass-ink) !important; }
[data-testid="stAlert"] > div, [data-testid="stAlertContainer"]{ background:var(--paper-2) !important; border:1px solid var(--rule) !important;
  border-left:3px solid var(--brass) !important; border-radius:8px !important; color:var(--ink) !important; }
[data-testid="stFileUploaderDropzone"]{ background:var(--paper-2) !important; border:1px dashed var(--rule) !important; border-radius:var(--r) !important; transition:border-color .2s; }
[data-testid="stFileUploaderDropzone"]:hover{ border-color:var(--brass) !important; }

/* ───────── Chat ───────── */
[data-testid="stChatMessage"]{ background:transparent !important; border:none !important; border-bottom:1px solid var(--rule-soft) !important;
  border-radius:0 !important; padding:1.1rem 0 !important; gap:.9rem; }
[data-testid="stChatMessage"][aria-label*="user" i]{ flex-direction:row-reverse; border-bottom:none !important; }
[data-testid="stChatMessage"][aria-label*="user" i] [data-testid="stChatMessageContent"]{ flex:0 1 auto; max-width:min(78%, 640px); margin-left:auto;
  background:var(--umber); padding:.7rem 1rem; border-radius:14px 14px 4px 14px; }
[data-testid="stChatMessage"][aria-label*="user" i] [data-testid="stChatMessageContent"] p{ color:var(--cream) !important; margin:0; }
[data-testid="stChatMessage"] [data-testid^="stChatMessageAvatar"]{ border-radius:8px !important; background:var(--paper-3) !important; color:var(--ink) !important; }
[data-testid="stChatMessage"][aria-label*="assistant" i] [data-testid^="stChatMessageAvatar"]{ background:var(--umber) !important; color:var(--cream) !important; }
[data-testid="stChatInput"]{ background:var(--paper-2) !important; border:1px solid var(--rule) !important; border-radius:14px !important;
  box-shadow:0 12px 30px -20px rgba(43,31,21,.45); transition:border-color .2s, box-shadow .2s; }
[data-testid="stChatInput"]:focus-within{ border-color:var(--brass) !important; box-shadow:0 0 0 3px var(--brass-soft), 0 12px 30px -20px rgba(43,31,21,.45); }
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] textarea{ background:transparent !important; border:none !important; }

/* ───────── Jawaban: teks Arab & sumber ───────── */
.arab{ margin:1.4rem 0 1rem; background:var(--paper-2); border:1px solid var(--rule); border-radius:var(--r); overflow:hidden; }
.arab-h{ display:flex; justify-content:space-between; align-items:center; gap:1rem; padding:.55rem 1rem; border-bottom:1px solid var(--rule-soft);
  font-size:.7rem; letter-spacing:.13em; text-transform:uppercase; color:var(--muted); font-weight:600; }
.arab-h [lang="ar"]{ letter-spacing:0; text-transform:none; font-size:1.05rem; line-height:2; color:var(--brass-ink); font-weight:400; }
.arab-t{ padding:1.5rem 1.6rem 1.6rem; font-family:var(--arab); font-size:1.5rem; line-height:2.75; word-spacing:.15em; color:var(--ink); text-align:right; }
.id-box{ background:var(--paper-2); border:1px solid var(--rule); border-radius:var(--r); padding:1rem 1.25rem; line-height:1.75; color:var(--ink); }
.cites{ display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.8rem; }
.cite{ display:inline-flex; align-items:center; gap:.45rem; font-size:.78rem; padding:.28rem .62rem; border:1px solid var(--rule); border-radius:6px;
  background:var(--paper-2); color:var(--ink-2) !important; text-decoration:none !important; transition:border-color .2s, color .2s; }
.cite b{ font-weight:600; color:var(--muted); font-size:.64rem; letter-spacing:.1em; text-transform:uppercase; }
.snip{ padding:.8rem 0; border-bottom:1px solid var(--rule-soft); font-size:.92rem; color:var(--ink-2); line-height:1.65; }
.snip:last-child{ border-bottom:none; }
.snip .h{ font-size:.76rem; color:var(--muted); margin-bottom:.3rem; }
.snip .h b{ color:var(--brass-ink); font-weight:600; }

/* ───────── Pembaca materi ───────── */
.doc{ max-height:72vh; overflow-y:auto; border-radius:var(--r); scrollbar-width:thin; scrollbar-color:var(--rule) transparent; }
.doc p{ margin:.6rem 0; line-height:1.95; color:var(--ink-2); }
.doc p[dir="rtl"]{ font-family:var(--arab); text-align:right; line-height:2.75; word-spacing:.15em; color:var(--ink); margin:1.4rem 0; }
.doc .doc-head{ text-align:center; padding:0 0 1.3rem; margin-bottom:1.3rem; border-bottom:1px solid var(--rule); }
.doc .doc-head .mt{ font-family:var(--serif); font-size:1.6rem; color:var(--ink); line-height:1.25; }
.doc .doc-head .mm{ font-size:.8rem; color:var(--muted); margin-top:.35rem; }
.doc .doc-head .mm b{ font-weight:600; letter-spacing:.12em; text-transform:uppercase; font-size:.64rem; color:var(--brass-ink); margin-right:.45rem; }
.doc .sub{ font-family:var(--serif); font-size:1.2rem; color:var(--ink) !important; margin-top:1.7rem !important; padding-top:1rem; border-top:1px solid var(--rule-soft); }
.doc .tr{ font-style:italic; padding-left:.9rem; border-left:2px solid var(--brass); }
.doc.kitab{ background:#FFFFFF; border:1px solid var(--rule); padding:3rem clamp(1.2rem, 5vw, 4rem);
  box-shadow:0 1px 0 var(--rule), 0 28px 50px -36px rgba(43,31,21,.45); }
.doc.malam{ background:var(--umber); padding:2.5rem clamp(1.2rem, 4vw, 3rem); scrollbar-color:#1D4038 transparent; }
.doc.malam p{ color:#C9D8CE; } .doc.malam p[dir="rtl"]{ color:#F4F0E7; }
.doc.malam .doc-head{ border-color:rgba(244,240,231,.16); } .doc.malam .doc-head .mt{ color:#F4F0E7; }
.doc.malam .doc-head .mm{ color:#9FB3A6; } .doc.malam .doc-head .mm b{ color:#C6A15B; }
.doc.malam .sub{ color:#E2C98F !important; border-color:rgba(244,240,231,.12); }
.doc.malam .tr{ color:#B9CCC1; border-color:#C6A15B; } .doc.malam mark{ background:rgba(198,161,91,.3); }

/* ───────── Pembaca materi + audio (tombol Dengarkan per paragraf) ───────── */
div:has(> [class*="st-key-bacaan_kitab"]){ background:#FFFFFF; border:1px solid var(--rule); border-radius:var(--r);
  box-shadow:0 1px 0 var(--rule), 0 28px 50px -36px rgba(43,31,21,.45); }
div:has(> [class*="st-key-bacaan_malam"]){ background:var(--umber); border-radius:var(--r); }
[class*="st-key-bacaan_"]{ padding:2.2rem clamp(1rem, 4.5vw, 3.5rem) 2.6rem; gap:0 !important; }
.doc.doc-polos{ background:transparent !important; border:none !important; box-shadow:none !important; padding:0 !important;
  max-height:none; overflow:visible; }
.doc.doc-polos p{ margin:.35rem 0; }
.doc.doc-polos p[dir="rtl"]{ margin:1rem 0 .1rem; }
.doc.doc-polos .doc-head{ margin-bottom:.6rem; }
[class*="st-key-ttsrow_"]{ align-items:flex-end; gap:.3rem !important; margin:0 0 .6rem; }
[class*="st-key-ttsrow_"] .stButton button{ min-height:0 !important; padding:.2rem .75rem !important; border-radius:999px !important;
  background:transparent !important; color:var(--brass-ink) !important; border:1px solid var(--rule) !important; box-shadow:none !important; }
[class*="st-key-ttsrow_"] .stButton button p{ font-size:.78rem !important; }
[class*="st-key-ttsrow_"] .stButton button:hover{ border-color:var(--brass) !important; background:var(--paper-2) !important; transform:none; }
[class*="st-key-bacaan_malam"] [class*="st-key-ttsrow_"] .stButton button{ color:#C6A15B !important; border-color:rgba(243,233,210,.2) !important; }
[class*="st-key-bacaan_malam"] [class*="st-key-ttsrow_"] .stButton button:hover{ background:rgba(243,233,210,.06) !important; }
[class*="st-key-ttsrow_"] [data-testid="stAudio"], [class*="st-key-ttsrow_"] audio{ width:100%; max-width:520px; }

/* ───────── Beranda ───────── */
/* Hero berlatar zamrud, seirama dengan pita ajakan di bawah halaman.
   Seluruh tulisan di dalamnya dibalik jadi gading/emas. */
.hero{ position:relative; background:var(--umber); color:var(--cream);
  border-radius:16px; padding:clamp(1.4rem, 3.5vw, 2.4rem) clamp(1.2rem, 4vw, 2.8rem) clamp(1.8rem, 4vw, 2.8rem);
  margin:.2rem 0 0; }
.hero .eyebrow{ color:var(--brass); }
.hero .hero-meta{ color:#9FB3A6; }
.hero .rule-draw{ background:rgba(198,161,91,.5); }
.hero .hero-ar{ color:var(--cream); }
.hero .hero-arti{ color:var(--brass); }
.hero .hero-lead{ color:#DCE7DF; }
.hero .stats{ border-top-color:rgba(244,240,231,.18); }
.hero .stats dt{ color:#9FB3A6; } .hero .stats dd{ color:var(--cream); }
.hero .btn{ background:var(--brass); color:var(--umber) !important; }
.hero .btn:hover{ background:#D7B673; }
.hero .btn-ghost{ color:var(--cream) !important; }
.hero .btn-ghost:hover{ color:var(--brass) !important; }
.hero .mosi{ background:transparent; border-color:rgba(244,240,231,.22); }
.hero .mosi-ar{ color:var(--cream); } .hero .mosi-id{ color:#DCE7DF; }
.hero .mosi-no{ color:#9FB3A6; }
.hero .tag{ color:var(--brass); border-color:rgba(198,161,91,.5); }
/* Logo dibiarkan tanpa bingkai dan tanpa latar: berkas WebP-nya transparan,
   sehingga lambang menyatu langsung dengan panel zamrud. */
.hero .hero-logo{ background:transparent; border:0; }
.hero-top{ display:flex; flex-wrap:wrap; justify-content:space-between; gap:.5rem 1rem; margin-bottom:1.2rem; }
.hero-meta{ font-size:.82rem; color:var(--muted); }
.hero-ar{ font-family:var(--arab-judul); font-weight:700; font-size:clamp(2.3rem, 6.2vw, 4.7rem); line-height:2.05; word-spacing:.1em; color:var(--ink); text-align:right; margin:0 0 1.6rem; padding:.6rem 0; }
.hero-grid{ display:grid; grid-template-columns:minmax(0,1.15fr) minmax(0,1fr); gap:clamp(1.8rem, 5vw, 4.5rem); margin-top:2.2rem; align-items:start; }
.hero-lead{ font-family:var(--serif); font-size:clamp(1.2rem, 2.2vw, 1.45rem); line-height:1.5; color:var(--ink); margin:0 0 1.8rem; max-width:34ch; }
.hero-head{ display:flex; align-items:center; gap:clamp(1rem, 3vw, 2.6rem); margin:0 0 1.2rem; }
.hero-head .hero-teks{ flex:1; min-width:0; }
.hero-head .hero-ar{ margin:0; }
/* Arti baris Arab besar — menempel di bawahnya, rata kanan mengikuti teks Arab */
.hero-arti{ font-family:var(--serif); font-style:italic; font-size:clamp(1rem, 1.7vw, 1.2rem);
  line-height:1.45; color:var(--ink-2); text-align:right; margin:.1rem 0 0; }
.hero-logo{ flex:none; width:clamp(120px, 18vw, 230px); height:auto;
  animation:logo-apung 5.5s ease-in-out infinite; will-change:transform; }
.intro .hero-logo{ animation:logo-in 1s var(--ease) both, logo-apung 5.5s ease-in-out 1s infinite; }
/* Logo melayang pelan — satu-satunya gerak yang berjalan terus di halaman. */
@keyframes logo-apung{ 0%, 100%{ transform:translateY(-5px); } 50%{ transform:translateY(5px); } }
@media (prefers-reduced-motion: reduce){
  .hero-logo, .intro .hero-logo, .splash-logo{ animation:none !important; }
}
/* logo WebP sudah transparan; khusus video cadangan (berlatar krem), tepinya dibuat lembut */
img.hero-logo, img.splash-logo{ display:block; background:transparent; }
video.hero-logo, video.splash-logo{ -webkit-mask-image:radial-gradient(ellipse 66% 66% at 50% 50%, #000 62%, transparent 100%);
  mask-image:radial-gradient(ellipse 72% 72% at 50% 50%, #000 78%, transparent 100%); }
@keyframes logo-in{ from{ opacity:0; transform:scale(.82) rotate(-8deg); } to{ opacity:1; transform:none; } }

/* Layar pembuka (muncul sekali saat website dibuka) */
.splash{ position:fixed; inset:0; z-index:1000001; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:1.1rem;
  background:var(--paper); pointer-events:none; animation:splash-out .8s var(--ease) var(--t, 3.5s) forwards; }
.splash-logo{ width:min(56vw, 340px); height:auto; animation:logo-in 1s var(--ease) both; }
.splash-nama{ font-family:var(--serif); font-size:1.05rem; letter-spacing:.32em; color:var(--ink-2); animation:logo-in 1s var(--ease) .35s both; }
.splash-nama span{ font-family:var(--arab-judul); letter-spacing:0; font-size:1.4rem; line-height:2.2; margin-left:.9rem; }
@keyframes splash-out{ to{ opacity:0; visibility:hidden; } }
.hero-cta{ display:flex; flex-wrap:wrap; align-items:center; gap:.6rem 1.4rem; }
.stats{ display:flex; flex-wrap:wrap; gap:1.2rem 2.6rem; margin:2.4rem 0 0; padding-top:1.3rem; border-top:1px solid var(--rule-soft); }
.stats div{ margin:0; } .stats dt{ font-size:.7rem; font-weight:600; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); }
.stats dd{ margin:.2rem 0 0; font-family:var(--serif); font-size:2.2rem; line-height:1; color:var(--ink); font-variant-numeric:tabular-nums; }
.btn{ display:inline-flex; align-items:center; gap:.5rem; min-height:2.9rem; padding:0 1.4rem; border-radius:8px; background:var(--umber);
  color:var(--cream) !important; text-decoration:none !important; font-weight:500; font-size:.95rem;
  transition:transform .15s var(--ease), background-color .2s, box-shadow .25s; }
.btn:hover{ background:var(--umber-2); transform:translateY(-1px); box-shadow:0 12px 22px -14px rgba(43,31,21,.7); }
.btn:active{ transform:scale(.98); }
.btn-light{ background:var(--cream); color:var(--umber) !important; } .btn-light:hover{ background:#FFFFFF; }
.btn-ghost{ display:inline-flex; align-items:center; gap:.45rem; min-height:2.9rem; color:var(--ink) !important; text-decoration:none !important; font-weight:500; }
.btn-ghost .arr, .idx-go{ display:inline-block; transition:transform .3s var(--ease); }
.btn-ghost:hover{ color:var(--brass-ink) !important; } .btn-ghost:hover .arr{ transform:translateX(5px); }
.mosi{ position:relative; overflow:hidden; background:var(--paper-2); border:1px solid var(--rule); border-radius:14px; padding:1.6rem 1.6rem 1.4rem; }
.mosi-top{ display:flex; justify-content:space-between; align-items:center; gap:1rem; }
.mosi-no{ font-family:var(--serif); font-size:.9rem; color:var(--muted); }
.mosi-ar{ font-family:var(--arab); font-size:1.55rem; line-height:2.65; word-spacing:.12em; color:var(--ink); text-align:right; margin:1.4rem 0 1.1rem; position:relative; }
.mosi-id{ color:var(--ink-2); line-height:1.65; margin:0; position:relative; }
.tag{ display:inline-block; margin-top:1.1rem; font-size:.74rem; color:var(--ink-2); border:1px solid var(--rule); border-radius:999px; padding:.2rem .7rem; }
.khatam{ position:absolute; right:-52px; bottom:-52px; width:180px; height:180px; opacity:.5; pointer-events:none; }
.khatam path, .khatam circle{ fill:none; stroke:var(--brass); stroke-width:.8; }
.sec{ padding:3.4rem 0 .5rem; }
.sec-head{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:flex-end; gap:.6rem 1rem; margin-bottom:1.3rem; }
.sec-t{ font-family:var(--serif); font-size:clamp(1.6rem, 3vw, 2.15rem); color:var(--ink); letter-spacing:-.015em; line-height:1.15; margin-top:.4rem; }
.sec-note{ color:var(--muted); font-size:.9rem; max-width:40ch; }
.idx{ list-style:none; margin:0; padding:0; border-top:1px solid var(--ink); }
.idx li{ margin:0; }
.idx a{ position:relative; display:grid; grid-template-columns:2.8rem minmax(0,1fr) auto 6rem 1.4rem; align-items:center; gap:1.3rem;
  padding:1.2rem .4rem; border-bottom:1px solid var(--rule); text-decoration:none !important; color:var(--ink) !important;
  transition:background-color .3s var(--ease), padding .3s var(--ease); }
.idx a::before{ content:""; position:absolute; left:0; top:-1px; bottom:-1px; width:3px; background:var(--c); transform:scaleY(0);
  transform-origin:bottom; transition:transform .35s var(--ease); }
.idx a:hover{ background:var(--paper-2); padding-left:1.1rem; }
.idx a:hover::before{ transform:scaleY(1); }
.idx-n{ font-family:var(--serif); font-size:.95rem; color:var(--muted); font-variant-numeric:tabular-nums; }
.idx-t{ display:block; font-family:var(--serif); font-size:1.35rem; line-height:1.2; color:var(--ink); }
.idx-d{ display:block; font-size:.86rem; line-height:1.55; color:var(--muted); margin-top:.3rem; max-width:60ch; }
.idx-ar{ font-family:var(--arab-judul); font-size:1.3rem; line-height:2.4; color:var(--brass-ink); white-space:nowrap; padding:0 .8rem; }
.idx-c{ font-size:.8rem; color:var(--muted); text-align:right; font-variant-numeric:tabular-nums; }
.idx a:hover .idx-go{ transform:translateX(5px); color:var(--brass-ink); }
.quote{ margin-top:3.6rem; display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.2fr); gap:clamp(1.4rem, 4vw, 3.5rem); align-items:center;
  padding:clamp(1.6rem, 4vw, 2.8rem); background:var(--paper-2); border:1px solid var(--rule); border-radius:14px; }
.quote .q-ar{ font-family:var(--arab); font-size:clamp(1.6rem, 3vw, 2.2rem); line-height:2.6; word-spacing:.12em; color:var(--ink); text-align:right; padding:.4rem 0; }
.quote .q-id{ font-family:var(--serif); font-style:italic; font-size:1.2rem; line-height:1.55; color:var(--ink-2); margin:.8rem 0 0; }
.steps{ list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:1.8rem; position:relative; }
.steps::before{ content:""; position:absolute; left:0; right:0; top:1.05rem; height:1px; background:var(--rule); }
.steps li{ position:relative; margin:0; }
.st-n{ width:2.1rem; height:2.1rem; border-radius:50%; display:grid; place-items:center; background:var(--paper); border:1px solid var(--ink);
  font-family:var(--serif); font-size:.95rem; color:var(--ink); position:relative; margin-bottom:1.1rem; transition:background-color .25s, color .25s; }
.steps li:hover .st-n{ background:var(--ink); color:var(--paper); }
.st-t{ font-family:var(--serif); font-size:1.18rem; color:var(--ink); }
.st-d{ font-size:.88rem; color:var(--muted); line-height:1.6; margin-top:.35rem; }
.st-a{ font-family:var(--arab); font-size:1.15rem; line-height:2.45; word-spacing:.1em; color:var(--brass-ink); margin-top:.9rem; }
.band{ position:relative; overflow:hidden; margin-top:3.8rem; background:var(--umber); border-radius:16px; padding:clamp(1.7rem, 4vw, 2.7rem);
  display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:1.4rem; }
.band-t{ font-family:var(--serif); font-size:clamp(1.45rem, 3vw, 1.95rem); color:#F4F0E7; line-height:1.2; }
.band-p{ color:#9FB3A6; margin:.4rem 0 0; max-width:50ch; line-height:1.6; }
.band-zha{ position:absolute; right:3%; bottom:-38%; font-family:var(--arab-judul); font-size:15rem; line-height:1; color:rgba(198,161,91,.07); pointer-events:none; }
.band > div, .band > a{ position:relative; }

/* ───────── Profil ───────── */
.pf{ display:grid; grid-template-columns:9.5rem minmax(0,1fr); gap:clamp(1.4rem, 4vw, 3rem); align-items:start; max-width:900px; }
.pf-photo{ position:relative; isolation:isolate; }
.pf-photo img, .pf-photo .kosong{ width:9.5rem; height:9.5rem; object-fit:cover; border-radius:14px; display:block; background:var(--paper-3); }
.pf-photo::after{ content:""; position:absolute; inset:8px -8px -8px 8px; border:1px solid var(--brass); border-radius:14px; z-index:-1; }
.pf-nama{ font-family:var(--serif); font-size:clamp(1.8rem, 3.5vw, 2.4rem); color:var(--ink); line-height:1.15; margin-top:.5rem; }
.pf-peran{ color:var(--brass-ink); font-weight:500; margin-top:.45rem; }
.pf-inst{ color:var(--muted); font-size:.92rem; margin-top:.15rem; }
.pf-bio{ color:var(--ink-2); line-height:1.8; margin:1.5rem 0 1.8rem; max-width:64ch; }
.pf-kontak{ list-style:none; padding:0; margin:0; border-top:1px solid var(--rule); max-width:560px; }
.pf-kontak li{ margin:0; }
.pf-kontak a, .pf-kontak span.row{ display:grid; grid-template-columns:6.5rem minmax(0,1fr) 1.2rem; gap:1rem; align-items:center; padding:.85rem .2rem;
  border-bottom:1px solid var(--rule); text-decoration:none !important; color:var(--ink) !important; transition:padding .3s var(--ease), background-color .3s; }
.pf-kontak a:hover{ padding-left:.8rem; background:var(--paper-2); }
.pf-kontak a:hover .arr{ transform:translate(3px, -3px); color:var(--brass-ink); }
.pf-kontak .k{ font-size:.7rem; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); font-weight:600; }
.pf-kontak .arr{ display:inline-block; transition:transform .3s var(--ease); }

/* ───────── Kaki halaman ───────── */
.foot{ margin-top:4.5rem; padding-top:1.4rem; border-top:1px solid var(--rule); display:flex; flex-wrap:wrap; justify-content:space-between; align-items:baseline;
  gap:.6rem 1.5rem; font-size:.8rem; color:var(--muted); }
.foot b{ font-family:var(--serif); font-weight:500; color:var(--ink); font-size:1rem; letter-spacing:.08em; margin-right:.3rem; }

/* ───────── Layar kecil ───────── */
@media (max-width: 820px){
  .hero-grid, .quote{ grid-template-columns:1fr; }
  .steps{ grid-template-columns:1fr 1fr; } .steps::before{ display:none; }
  .idx a{ grid-template-columns:2.2rem minmax(0,1fr) 1.2rem; gap:.9rem; } .idx-ar, .idx-c{ display:none; }
}
@media (max-width: 520px){
  .steps{ grid-template-columns:1fr; }
  .pf{ grid-template-columns:1fr; }
  .hero-head{ flex-direction:column; align-items:center; }
  .hero-head .hero-teks{ width:100%; } .hero-head .hero-ar{ width:100%; }
  .doc.kitab{ padding:1.8rem 1.1rem; }
  [class*="st-key-bacaan_"]{ padding:1.4rem .9rem 1.8rem; }
}

/* Hormati pengguna yang mematikan animasi */
@media (prefers-reduced-motion: reduce){
  *, *::before, *::after{ animation:none !important; transition:none !important; }
  .count{ --n:var(--to); }
  .splash{ display:none !important; }
}
</style>
"""


def esc(t: str) -> str:
    return html.escape(t or "")


# Rangkaian teks Arab (boleh berisi spasi / tanda baca di antara kata Arab)
_AR_HURUF = r"\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF"
AR_RUN = re.compile(rf"[{_AR_HURUF}]+(?:[\s.,:;!?()«»\-–]+[{_AR_HURUF}]+)*")


def bungkus_arab(t: str) -> str:
    """Bungkus teks Arab di tengah kalimat dengan <span class='ar-in'> agar berjarak & tidak menempel."""
    return AR_RUN.sub(lambda m: f"<span class='ar-in' lang='ar' dir='rtl'>{m.group(0)}</span>", t or "")


def md_arab(t: str) -> str:
    """Untuk teks markdown (jawaban AI): amankan tag HTML, lalu beri jarak pada teks Arab."""
    t = (t or "").replace("&", "&amp;").replace("<", "&lt;")
    return bungkus_arab(t)


def fmt_inline(t: str) -> str:
    """Escape HTML lalu dukung **tebal** dan baris baru."""
    t = esc(t.strip())
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t.replace("\n", "<br>")


def tanpa_harakat(t: str) -> str:
    """Lepas harakat. Dipakai untuk tajuk berfont Aref Ruqaa, yang
    penempatan tanda barisnya tidak serapi Amiri."""
    return AR_DIACRITICS.sub("", t or "")


def fmt_campur(t: str) -> str:
    """Seperti fmt_inline, tetapi teks Arab di tengah kalimat diberi jarak."""
    return bungkus_arab(fmt_inline(t))


def page_header(title: str, arabic: str = "", desc: str = "", eyebrow: str = ""):
    st.markdown(
        f"<div class='ph'><div class='eyebrow reveal'>{esc(eyebrow)}</div>"
        f"<div class='ph-row reveal' style='--i:1'><div class='ph-t'>{esc(title)}</div>"
        f"<div class='ph-a' dir='rtl' lang='ar'>{esc(tanpa_harakat(arabic))}</div></div>"
        f"<p class='ph-d reveal' style='--i:2'>{esc(desc)}</p><div class='rule-draw'></div></div>",
        unsafe_allow_html=True,
    )


def kotak_arab(isi_html: str, label: str = "Teks Arab dari sumber", label_ar: str = "النَّصُّ الْعَرَبِيُّ مِنَ الْمَصْدَرِ"):
    st.markdown(
        f"<div class='arab'><div class='arab-h'><span>{esc(label)}</span><span lang='ar'>{label_ar}</span></div>"
        f"<div class='arab-t' dir='rtl' lang='ar'>{isi_html}</div></div>",
        unsafe_allow_html=True,
    )


def render_answer(parsed: dict, hits=None):
    jawaban = parsed.get("JAWABAN", "").strip()
    arab = parsed.get("ARAB", "").strip()
    sumber = parsed.get("SUMBER", "").strip()
    if jawaban:
        st.markdown(md_arab(jawaban), unsafe_allow_html=True)
    if arab and arab != "-":
        kotak_arab(fmt_inline(arab))
        with st.expander("Salin teks Arab"):
            st.code(arab, language=None)
    if sumber and sumber != "-":
        chips = ""
        for nama in re.split(r"[,;\n]", sumber):
            nama = nama.strip().strip("()[]<>")
            if nama and not nama.startswith("http"):
                chips += f"<span class='cite'><b>Materi</b>{esc(nama)}</span>"
        if chips:
            st.markdown(f"<div class='cites'>{chips}</div>", unsafe_allow_html=True)
    if hits:
        with st.expander(f"Cuplikan materi yang dipakai · {len(hits)}"):
            for h in hits:
                st.markdown(
                    f"<div class='snip'><div class='h'><b>{esc(CATEGORIES[h['cat']]['label'])}</b> › {bungkus_arab(esc(terapkan_harakat(h.get('sub', ''))))} · "
                    f"{esc(h['source'])} · skor {h['score']:.2f}</div><div dir='auto'>{fmt_campur(terapkan_harakat(h['text'])[:700])}</div></div>",
                    unsafe_allow_html=True,
                )


def highlight(text: str, query: str) -> str:
    out = esc(text)
    words = sorted({w for w in re.findall(r"\w{2,}", query)}, key=len, reverse=True)
    for w in words:
        out = re.sub(f"({re.escape(esc(w))})", r"<mark>\1</mark>", out, flags=re.I)
    return out


def _paragraf_html(p: str, query: str = "", ukuran: int = 26) -> str:
    """HTML satu paragraf materi (Arab penuh, judul bagian, terjemah, atau teks biasa)."""
    content = highlight(p, query) if query else esc(p)
    content = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content)
    if rasio_arab(p) > 0.75:
        return f"<p dir='rtl' lang='ar' style='font-size:{ukuran}px'>{content}</p>"
    if re.match(r"^(Muqaddimah \d+|Mosi \d+|Bagian \d+|\d+\.$)", p):
        return f"<p class='sub'>{content}</p>"
    if p.startswith(("“", '"', "Arti:", "Terjemah")):
        return f"<p class='tr' dir='auto'>{bungkus_arab(content)}</p>"
    return f"<p dir='auto'>{bungkus_arab(content)}</p>"


def _kepala_doc(meta: dict) -> str:
    if not meta:
        return ""
    return (
        f"<div class='doc-head'><div class='mt' dir='auto'>{bungkus_arab(esc(rapikan_ejaan(meta.get('JUDUL', ''))))}</div>"
        f"<div class='mm'><b>Menu</b>{bungkus_arab(esc(rapikan_ejaan(meta.get('MENU', ''))))}</div>"
        f"<div class='mm'><b>Sumber</b>{bungkus_arab(esc(meta.get('SUMBER', '')))}</div></div>"
    )


def teks_untuk_audio(p: str) -> str:
    """Bagian Arab yang dibacakan dari satu paragraf ('' bila tidak ada teks Arab)."""
    if rasio_arab(p) > 0.75:
        return p
    bagian = [m.group(0) for m in AR_RUN.finditer(p) if len(AR_HURUF_DASAR.findall(m.group(0))) >= 2]
    return " ، ".join(bagian)


def pilih_tts(kunci: str):
    """Dipanggil saat tombol Dengarkan diklik."""
    st.session_state["tts_putar"] = kunci


# Baris dianggap menutup satu paragraf bila berakhir di titik / tanda tanya / seru.
AKHIR_KALIMAT = re.compile(r"[.؟!…۔][\"'»)\]\s]*$")
MAKS_BARIS_BLOK = 12


def baris_audio(p: str) -> str:
    """Teks Arab yang layak disuarakan dari satu baris (penyaring sama dengan skrip Colab)."""
    ar = teks_untuk_audio(p)
    return ar if ar and len(AR_HURUF_DASAR.findall(ar)) >= 4 else ""


def susun_blok(sumber: list) -> list:
    """Gabungkan baris menjadi paragraf yang berakhir di titik.

    Hasil: daftar (indeks baris terakhir, potongan audio). `potongan` berisi satu
    kunci bila rekaman satu paragraf utuh tersedia — kalau belum, dipakai kunci
    per baris hasil render lama, disambung saat diputar.
    """
    indeks = indeks_audio()
    hasil, grup = [], []
    for i, p in enumerate(sumber):
        ar = baris_audio(p)
        if ar:
            grup.append((i, ar))
        tutup = grup and (not ar or bool(AKHIR_KALIMAT.search(p))
                          or len(grup) >= MAKS_BARIS_BLOK or i == len(sumber) - 1)
        if not tutup:
            continue
        gabung = kunci_audio(" ".join(a for _, a in grup))
        if gabung in indeks:
            potongan = (gabung,)                       # satu rekaman utuh
        else:
            potongan = tuple(k for k in (kunci_audio(a) for _, a in grup) if k in indeks)
        if potongan:
            hasil.append((grup[-1][0], potongan))
        grup = []
    return hasil


def render_doc_audio(text: str, cat: str, kitab: bool = True, ukuran: int = 26,
                     asli: str = ""):
    """Pembaca materi dengan tombol Dengarkan per paragraf utuh.

    Berkas materi memotong kalimat panjang menjadi beberapa baris, jadi baris
    digabung dulu sampai bertemu titik. Rekaman dicari memakai teks ASLI dari
    berkas materi (parameter `asli`), bukan teks yang sudah diberi harakat.
    """
    meta, body = split_header(text)
    mode = "kitab" if kitab else "malam"
    limit = 60000
    paras = [p.strip() for p in re.split(r"\n+", body[:limit]) if p.strip()]

    sumber = paras
    if asli:
        _, body_asli = split_header(asli)
        kasar = [p.strip() for p in re.split(r"\n+", body_asli[:limit]) if p.strip()]
        if len(kasar) == len(paras):
            sumber = kasar

    blok = susun_blok(sumber)
    tombol = {baris: (n, potongan) for n, (baris, potongan) in enumerate(blok)}

    putar = st.session_state.get("tts_putar")
    if blok:
        with st.container(key=f"ttsall_{mode}_{cat}"):
            st.button(f"Dengarkan seluruh materi · {len(blok)} paragraf",
                      key=f"ttsallbtn_{mode}_{cat}", icon=":material/playlist_play:",
                      on_click=pilih_tts, args=(f"SEMUA_{cat}",))
            if putar == f"SEMUA_{cat}":
                putar_blok(tuple(potongan for _, potongan in blok))

    with st.container(height=640, border=False, key=f"bacaan_{mode}_{cat}"):
        if meta:
            st.markdown(f"<div class='doc {mode} doc-polos'>{_kepala_doc(meta)}</div>", unsafe_allow_html=True)
        for i, p in enumerate(paras):
            st.markdown(f"<div class='doc {mode} doc-polos'>{_paragraf_html(p, '', ukuran)}</div>", unsafe_allow_html=True)
            if i not in tombol:
                continue
            nomor, potongan = tombol[i]
            kunci = f"{cat}_{nomor}"
            with st.container(key=f"ttsrow_{mode}_{kunci}"):
                st.button(f"Dengarkan paragraf {nomor + 1}", key=f"ttsbtn_{mode}_{kunci}",
                          icon=":material/volume_up:", on_click=pilih_tts, args=(kunci,))
                if putar == kunci:
                    putar_blok((potongan,))
    if len(body) > limit:
        st.caption(f"… ditampilkan {limit:,} dari {len(body):,} karakter. Gunakan tab Cari / Tanya untuk bagian lainnya.")


def render_doc(text: str, query: str = "", kitab: bool = True, ukuran: int = 26):
    meta, body = split_header(text)
    head = _kepala_doc(meta)
    limit = 60000
    paras = [p.strip() for p in re.split(r"\n+", body[:limit]) if p.strip()]
    html_paras = [_paragraf_html(p, query, ukuran) for p in paras]
    kelas = "doc kitab" if kitab else "doc malam"
    st.markdown(f"<div class='{kelas}'>{head}{''.join(html_paras)}</div>", unsafe_allow_html=True)
    if len(body) > limit:
        st.caption(f"… ditampilkan {limit:,} dari {len(body):,} karakter. Gunakan tab Cari / Tanya untuk bagian lainnya.")


BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]


def tanggal_id() -> str:
    import datetime
    d = datetime.date.today()
    return f"{d.day} {BULAN[d.month - 1]} {d.year}"


KHATAM = (  # bintang delapan (khatam) yang "tergambar" saat halaman dibuka
    "<svg class='khatam' viewBox='0 0 100 100' aria-hidden='true'>"
    "<path d='M50 6 L61 39 L94 50 L61 61 L50 94 L39 61 L6 50 L39 39 Z'/>"
    "<path d='M19 19 L50 32 L81 19 L68 50 L81 81 L50 68 L19 81 L32 50 Z'/>"
    "<circle cx='50' cy='50' r='13'/></svg>"
)


def hari_ini_index(n: int) -> int:
    import datetime
    return datetime.date.today().toordinal() % n if n else 0


def mosi_harian(kb):
    pola = re.compile(r"Tema:\s*([^\n]+)\n\s*الْقَضِيَّةُ:\s*([^\n]+)\n\s*Mosi:\s*([^\n]+)")
    hasil = []
    for d in kb["docs"]:
        if d["cat"] in ("muqaddimah", "mosi"):
            for tema, ar, idn in pola.findall(d["text"]):
                if (ar, idn) not in [(h[1], h[2]) for h in hasil]:
                    hasil.append((tema.strip(), ar.strip(), idn.strip()))
    return hasil[hari_ini_index(len(hasil))] if hasil else None


def ibarah_harian(kb):
    pola = re.compile(r"\n([^\n]*[\u0600-\u06FF][^\n]*)\nArti:\s*([^\n]+)")
    hasil = []
    for d in kb["docs"]:
        if d["cat"] == "ibarah":
            for ar, idn in pola.findall(d["text"]):
                hasil.append((d["title"], ar.strip(), idn.strip()))
    return hasil[hari_ini_index(len(hasil)) * 7 % len(hasil)] if hasil else None


def pilih_materi(key: str, i: int):
    """Dipanggil saat judul di Daftar isi diklik: pilih materi itu di kotak 'Pilih materi'."""
    st.session_state[key] = i


def siapkan_harakat_materi(doc) -> str:
    """Tampilkan materi dengan harakat yang sudah ada — TANPA menunggu (harakat dibuat otomatis di latar belakang)."""
    teks = doc["text"]
    if ADA_MUDAKHALAH.search(teks):
        st.caption(CATATAN_POI)
    persen = persen_harakat(teks)
    if persen < 100:
        st.caption(f"Harakat materi ini sedang dilengkapi otomatis di latar belakang ({persen:.0f}% selesai). "
                   "Muat ulang halaman nanti untuk melihat hasil terbaru.")
    return terapkan_harakat(teks)


# ─────────────────────────────────────────────────────────────
# AUDIO TEKS ARAB (rekaman suara pengembang — kloning XTTS-v2)
# Berkas MP3 dibuat di komputer dengan buat_suara.py lalu diletakkan
# di static/audio/. Website hanya memutar berkas, tidak memanggil AI.
# ─────────────────────────────────────────────────────────────
AUDIO_DIR = STATIC_DIR / "audio"
# Hanya dua kategori ini yang direkam suaranya; halaman lain tidak menampilkan
# pilihan audio sama sekali agar tidak menjanjikan sesuatu yang tidak ada.
KATEGORI_AUDIO = ("ibarah", "kosakata")


@st.cache_resource(show_spinner=False)
def _indeks_audio(tanda: str) -> dict:
    """Peta kunci -> (arsip, nama). Berkas dicari di seluruh folder proyek,
    jadi letaknya boleh di static/audio/, audio/, atau di mana pun."""
    peta = {}
    for berkas in sorted(APP_DIR.rglob("*.mp3")):
        peta[berkas.stem] = (None, str(berkas))
    for arsip in sorted(APP_DIR.rglob("*.zip")):
        try:
            with zipfile.ZipFile(arsip) as z:
                for nama in z.namelist():
                    jalur = PurePosixPath(nama)
                    if jalur.suffix.lower() in (".mp3", ".wav"):
                        peta[jalur.stem] = (str(arsip), nama)
        except Exception:
            continue
    return peta


def indeks_audio() -> dict:
    try:
        tanda = "|".join(f"{p.relative_to(APP_DIR)}:{p.stat().st_size}"
                         for p in sorted(APP_DIR.rglob("*.zip")))
    except OSError:
        tanda = ""
    return _indeks_audio(tanda)


def kunci_audio(ar: str) -> str:
    """Kunci dihitung dari teks TANPA harakat agar perbaikan harakat
    tidak memutus kaitan paragraf dengan berkas rekamannya."""
    polos = re.sub(r"\s+", " ", AR_DIACRITICS.sub("", ar or "")).strip()
    return hashlib.md5(polos.encode("utf-8")).hexdigest()[:16]


def berkas_audio(ar: str):
    """Kunci rekaman untuk teks Arab ini, atau None bila belum ada."""
    k = kunci_audio(ar)
    return k if k in indeks_audio() else None


@st.cache_data(show_spinner=False, max_entries=48)
def baca_audio(kunci: str) -> bytes:
    arsip, nama = indeks_audio()[kunci]
    if arsip is None:
        return Path(nama).read_bytes()
    with zipfile.ZipFile(arsip) as z:
        return z.read(nama)


# Dua potongan sunyi (MP3 mono 24 kHz): 0,22 detik untuk menyambung baris
# di dalam satu kalimat, dan 0,8 detik untuk memisahkan antarparagraf.
_JEDA_PENDEK_B64 = (
    "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjYwLjE2LjEwMAAAAAAAAAAAAAAA//OEwAAAAAAAAAAA"
    "AEluZm8AAAAPAAAADAAABmAAMDAwMDAwMDBDQ0NDQ0NDQ1ZWVlZWVlZWaWlpaWlpaWlpfHx8fHx8"
    "fHyPj4+Pj4+Pj6GhoaGhoaGhobS0tLS0tLS0x8fHx8fHx8fa2tra2tra2trt7e3t7e3t7f//////"
    "////AAAAAExhdmM2MC4zMQAAAAAAAAAAAAAAACQEIAAAAAAAAAZgy50wPwAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAA//NUxAAAAANIAAAAAExBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVV//NUxGsAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEw"
    "MFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxB"
    "TUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAA"
    "AFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQA"
    "AANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
)
_JEDA_PANJANG_B64 = (
    "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjYwLjE2LjEwMAAAAAAAAAAAAAAA//OEwAAAAAAAAAAA"
    "AEluZm8AAAAPAAAAJAAAEaAAEREYGBgfHx8mJiYsLDMzMzo6OkFBQUhITk5OVVVVXFxcY2Njampx"
    "cXF3d3d+fn6FhYyMjJOTk5mZmaCgoKenrq6utbW1u7u7wsLJycnQ0NDX19fd3d3k5Ovr6/Ly8vn5"
    "+f//AAAAAExhdmM2MC4zMQAAAAAAAAAAAAAAACQDwAAAAAAAABGgAgiECAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAA//NUxAAAAANIAAAAAExBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVV//NUxGsAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEw"
    "MFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxB"
    "TUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAA"
    "AFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQA"
    "AANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUz"
    "LjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANI"
    "AAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NU"
    "xJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEw"
    "MFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxB"
    "TUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAA"
    "AFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQA"
    "AANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUz"
    "LjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANIAAAAAFVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NUxJQAAANI"
    "AAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
)


@st.cache_resource(show_spinner=False)
def _jeda_mp3() -> tuple:
    import base64
    return base64.b64decode(_JEDA_PENDEK_B64), base64.b64decode(_JEDA_PANJANG_B64)


@st.cache_data(show_spinner=False, max_entries=12)
def rangkai_blok(blok: tuple) -> bytes:
    """Gabungkan rekaman jadi satu aliran MP3.

    `blok` berisi tuple per paragraf, masing-masing tuple kunci baris.
    Antarbaris dalam satu paragraf diberi jeda pendek, antarparagraf jeda panjang.
    Semua berkas dibuat dengan penyandi, laju, dan bitrate sama, jadi aman disambung.
    """
    pendek, panjang = _jeda_mp3()
    keping = []
    for i, grup in enumerate(blok):
        if i:
            keping.append(panjang)
        for j, kunci in enumerate(grup):
            if j:
                keping.append(pendek)
            keping.append(baca_audio(kunci))
    return b"".join(keping)


def putar_blok(blok: tuple):
    if not blok:
        return
    try:
        st.audio(rangkai_blok(blok), format="audio/mpeg", autoplay=True)
    except Exception:
        st.caption("Rekaman gabungan tidak dapat dibuka.")


def pilihan_suara():
    """Keterangan pemilik suara, atau petunjuk bila rekaman belum terpasang."""
    jumlah = len(indeks_audio())
    if jumlah:
        st.caption(f"Suara: {PROFIL['nama']} · {jumlah} rekaman")
        return
    arsip = sorted(p.relative_to(APP_DIR).as_posix() for p in APP_DIR.rglob("*.zip"))
    st.warning(
        "Berkas rekaman belum ditemukan di repositori. "
        + (f"Arsip yang terbaca: {', '.join(arsip)}" if arsip
           else "Tidak ada satu pun berkas .zip di repositori — "
                "unggah audio_01.zip … audio_08.zip ke folder static/audio/.")
    )


def putar_audio_arab(teks: str, autoplay: bool = True):
    """Putar rekaman untuk teks Arab ini."""
    kunci = berkas_audio(teks)
    if not kunci:
        st.caption("Rekaman untuk bagian ini belum tersedia.")
        return
    try:
        st.audio(baca_audio(kunci), format="audio/mpeg", autoplay=autoplay)
    except Exception:
        st.caption("Rekaman tidak dapat dibuka.")


# ─────────────────────────────────────────────────────────────
# HALAMAN
# ─────────────────────────────────────────────────────────────
def page_home(kb):
    docs = kb["docs"]
    mosi, ibr = mosi_harian(kb), ibarah_harian(kb)
    # teks Arab mosi & ibarah harian ditampilkan dengan harakat yang sudah tersedia
    if mosi:
        mosi = (terapkan_harakat(mosi[0]), terapkan_harakat(mosi[1]), mosi[2])
    if ibr:
        ibr = (terapkan_harakat(ibr[0]), terapkan_harakat(ibr[1]), ibr[2])
    # Animasi pembuka hanya saat Beranda pertama kali dibuka; kunjungan berikutnya tampil diam.
    intro = not st.session_state.get("beranda_dilihat")
    st.session_state["beranda_dilihat"] = True

    def angka(n: int) -> str:
        return f"<span class='count' style='--to:{n}'></span>" if intro else str(n)

    kartu_mosi = ""
    if mosi:
        kartu_mosi = (
            f"<aside class='mosi reveal' style='--i:4'>{KHATAM}"
            f"<div class='mosi-top'><span class='eyebrow'>Mosi hari ini</span><span class='mosi-no'>{esc(tanggal_id())}</span></div>"
            f"<div class='mosi-ar' dir='rtl' lang='ar'>{esc(mosi[1])}</div>"
            f"<p class='mosi-id'>{fmt_campur(mosi[2])}</p><span class='tag'>Tema · {bungkus_arab(esc(mosi[0]))}</span></aside>"
        )
    st.markdown(
        f"<section class='hero{' intro' if intro else ''}'>"
        "<div class='hero-top reveal'><span class='eyebrow'>Panduan debat bahasa Arab</span>"
        "<span class='hero-meta'>Format Qatar Debate · untuk pelajar, santri, dan mahasiswa</span></div>"
        f"<div class='hero-head'>{video_logo('hero-logo')}"
        "<div class='hero-teks'>"
        "<div class='hero-ar ink-in' dir='rtl' lang='ar'>أتقن فن المناظرة باللغة العربية</div>"
        "<p class='hero-arti reveal' style='--i:1'>Kuasailah seni berdebat dalam bahasa Arab</p>"
        "</div></div>"
        "<div class='rule-draw'></div>"
        "<div class='hero-grid'><div>"
        "<p class='hero-lead reveal' style='--i:2'>Belajar debat bahasa Arab dari dasar: sistem, mosi, ibarah, kamus, dan muqaddimah. "
        "Asisten MUNĀẒIR menjawab hanya dari materi, lengkap dengan teks Arab dan sumbernya.</p>"
        "<div class='hero-cta reveal' style='--i:3'><a class='btn' href='sistem_debat' target='_self'>Mulai belajar</a>"
        "<a class='btn-ghost' href='chat' target='_self'>Tanya MUNĀẒIR <span class='arr'>→</span></a></div>"
        "<dl class='stats reveal' style='--i:4'>"
        f"<div><dt>Materi</dt><dd>{angka(len(docs))}</dd></div>"
        f"<div><dt>Bagian</dt><dd>{angka(len(CATEGORIES))}</dd></div>"
        "</dl></div>"
        f"{kartu_mosi}</div></section>",
        unsafe_allow_html=True,
    )

    baris = ""
    for i, (cat, meta) in enumerate(CATEGORIES.items(), 1):
        n = sum(1 for d in docs if d["cat"] == cat)
        baris += (
            f"<li class='reveal' style='--i:{i}'><a href='{cat}' target='_self' style='--c:{meta['warna']}'>"
            f"<span class='idx-n'>{i:02d}</span>"
            f"<span><span class='idx-t'>{esc(meta['label'])}</span><span class='idx-d'>{esc(meta['desc'])}</span></span>"
            f"<span class='idx-ar' dir='rtl' lang='ar'>{esc(tanpa_harakat(meta['ar']))}</span>"
            f"<span class='idx-c'>{n} materi</span><span class='idx-go' aria-hidden='true'>→</span></a></li>"
        )
    st.markdown(
        "<section class='sec'><div class='sec-head'><div><div class='eyebrow'>Daftar isi</div>"
        "<div class='sec-t'>Lima bagian materi</div></div>"
        "<p class='sec-note'>Pilih bagian untuk membaca, mencari, atau bertanya langsung pada materinya.</p></div>"
        f"<ol class='idx'>{baris}</ol></section>",
        unsafe_allow_html=True,
    )

    if ibr:
        st.markdown(
            "<section class='quote reveal'><div>"
            f"<div class='eyebrow'>Ibārah pilihan · {bungkus_arab(esc(ibr[0].replace('Ibārah untuk ', '')))}</div>"
            f"<p class='q-id'>{fmt_campur(ibr[2])}</p></div>"
            f"<div class='q-ar' dir='rtl' lang='ar'>{esc(ibr[1])}</div></section>",
            unsafe_allow_html=True,
        )

    langkah = [
        ("Pahami sistem debat", f"Peran pembicara, {LABEL_POI}, dan cara juri menilai.", "فَهْمُ النِّظَامِ"),
        ("Bedah mosi", "Kenali jenis mosi, definisi, dan beban pembuktian.", "تَحْلِيلُ الْقَضِيَّةِ"),
        ("Kuasai ibarah & kosakata", "Ungkapan untuk berargumen, menyanggah, dan bertanya.", "إِتْقَانُ الْعِبَارَاتِ"),
        ("Latihan berpidato", "Susun muqaddimah, lalu berlatih dengan Timer Debat.", "التَّدْرِيبُ عَلَى الْإِلْقَاءِ"),
    ]
    isi = "".join(
        f"<li class='reveal' style='--i:{n}'><span class='st-n'>{n}</span><div class='st-t'>{esc(t)}</div>"
        f"<div class='st-d'>{esc(d)}</div><div class='st-a' dir='rtl' lang='ar'>{ar}</div></li>"
        for n, (t, d, ar) in enumerate(langkah, 1)
    )
    st.markdown(
        "<section class='sec' id='jalur'><div class='sec-head'><div><div class='eyebrow'>Jalur belajar</div>"
        "<div class='sec-t'>Empat langkah menjadi munāẓir</div></div></div>"
        f"<ol class='steps'>{isi}</ol></section>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<section class='band reveal'><span class='band-zha' aria-hidden='true'>ظ</span>"
        "<div><div class='band-t'>Bingung harus mulai dari mana?</div>"
        "<p class='band-p'>Tanyakan langsung ke MUNĀẒIR. Jawaban dalam bahasa Indonesia, disertai teks Arab dan sumbernya.</p></div>"
        "<a class='btn btn-light' href='chat' target='_self'>Buka Chat MUNĀẒIR</a></section>",
        unsafe_allow_html=True,
    )


def cek_api_key():
    """Kalau API key Groq belum diatur di Secrets, minta pengguna mengisinya sementara."""
    if not get_api_key():
        st.warning("API key Groq belum diatur. Isi di Secrets Streamlit (GROQ_API_KEY), atau masukkan sementara di bawah.")
        st.text_input("Groq API key (sementara)", type="password", key="user_api_key")


AVATAR_AI = ":material/menu_book:"
AVATAR_USER = ":material/person:"


def page_chat():
    page_header("Chat MUNĀẒIR", "حِوَارٌ مَعَ مُنَاظِرٍ",
                "Tanyakan apa saja seputar materi debat. Jawaban hanya dari materi MUNĀẒIR, disertai teks Arab dan nama file sumbernya.", "Asisten")
    cek_api_key()
    history = st.session_state.setdefault("chat", [])
    if history:
        _, kanan = st.columns([3, 1])
        with kanan.container(key="aksi_sekunder"):
            if st.button("Hapus riwayat chat"):
                st.session_state["chat"] = []
                st.rerun()
    scope_labels = ["Semua menu"] + [v["label"] for v in CATEGORIES.values()]
    scope = st.selectbox("Cari di menu:", scope_labels, key="chat_scope")
    cats = None if scope == "Semua menu" else [k for k, v in CATEGORIES.items() if v["label"] == scope]

    if not history:
        with st.chat_message("assistant", avatar=AVATAR_AI):
            st.markdown(
                "<b><span class='ar-in' lang='ar' dir='rtl'>السَّلَامُ عَلَيْكُمْ</span></b> — saya **MUNĀẒIR**, "
                "asisten debat bahasa Arab Anda. Silakan tanya tentang sistem debat, mosi, ibarah, kosakata, atau muqaddimah.",
                unsafe_allow_html=True,
            )
        st.markdown("<div class='subhead'>Coba tanyakan</div>", unsafe_allow_html=True)
        with st.container(key="contoh_chat"):
            ex_cols = st.columns(3)
            examples = ["Apa itu POI dan kapan boleh diajukan?", "Ungkapan untuk menyanggah argumen lawan", "Contoh muqaddimah kontra pembicara kedua"]
            for c, ex in zip(ex_cols, examples):
                if c.button(ex):
                    st.session_state["pending_q"] = ex
                    st.rerun()

    for m in history:
        with st.chat_message(m["role"], avatar=AVATAR_AI if m["role"] == "assistant" else AVATAR_USER):
            if m["role"] == "user":
                st.markdown(m["content"])
            elif m.get("error"):
                st.error(m["content"])
            else:
                render_answer(m["parsed"], m.get("hits"))

    q = st.chat_input("Tulis pertanyaan Anda… (bahasa Indonesia atau Arab)")
    q = q or st.session_state.pop("pending_q", None)
    if q:
        with st.chat_message("user", avatar=AVATAR_USER):
            st.markdown(q)
        with st.chat_message("assistant", avatar=AVATAR_AI):
            with st.spinner("Mencari di materi…"):
                try:
                    raw, parsed, hits = answer_question(q, cats=cats, history=history)
                    render_answer(parsed, hits)
                    item = {"role": "assistant", "raw": raw, "parsed": parsed, "hits": hits}
                except Exception as e:
                    st.error(str(e))
                    item = {"role": "assistant", "content": str(e), "error": True, "raw": ""}
        history.append({"role": "user", "content": q})
        history.append(item)


def page_category(cat: str, kb):
    meta = CATEGORIES[cat]
    nomor = list(CATEGORIES).index(cat) + 1
    page_header(meta["label"], meta["ar"], meta["desc"], f"Materi · {nomor:02d} dari {len(CATEGORIES):02d}")
    docs = [d for d in kb["docs"] if d["cat"] == cat]
    t1, t2, t3 = st.tabs(["Baca materi", "Cari", "Tanya MUNĀẒIR"])

    with t1:
        if not docs:
            st.info(f"Belum ada materi di menu ini. Tambahkan file ke folder `data/{cat}/` di GitHub atau lewat menu **Kelola Materi**.")
        else:
            subs = sorted({d["sub"] for d in docs})
            c1, c2 = st.columns([1, 1.6])
            sub_sel = c1.selectbox("Subtopik", ["Semua subtopik"] + subs, key=f"sub_{cat}", format_func=terapkan_harakat)
            shown = docs if sub_sel == "Semua subtopik" else [d for d in docs if d["sub"] == sub_sel]
            shown = sorted(shown, key=lambda d: (d["sub"], d["source"]))
            pick_key = f"doc_{cat}_{sub_sel}"
            pick = c2.selectbox(
                "Materi yang dibaca",
                range(len(shown)),
                format_func=lambda i: terapkan_harakat(shown[i]["source"]),
                key=pick_key,
            )
            with st.expander(f"Daftar isi · {len(shown)} materi", expanded=False):
                with st.container(key=f"toc_{cat}"):
                    for s_name in sorted({d["sub"] for d in shown}):
                        st.markdown(f"<div class='subhead'>{bungkus_arab(esc(terapkan_harakat(s_name)))}</div>",
                                    unsafe_allow_html=True)
                        for i, d in enumerate(shown):
                            if d["sub"] != s_name:
                                continue
                            label = (("→ " if i == pick else "") + terapkan_harakat(d["source"])
                                     + (" · unggahan" if d["origin"] != "repo" else ""))
                            st.button(label, key=f"tocbtn_{cat}_{sub_sel}_{i}", on_click=pilih_materi, args=(pick_key, i))
            ada_rekaman = cat in KATEGORI_AUDIO
            if ada_rekaman:
                o1, o2, o3 = st.columns([1, 1.4, 0.8])
            else:
                o1, o2 = st.columns([1, 2.2])
                o3 = None
            mode = o1.radio("Tampilan baca", ["Kertas", "Malam"], horizontal=True, key="mode_baca_v2")
            ukuran = o2.slider("Ukuran teks Arab", 20, 36, 26, key="ukuran_arab")
            pakai_audio = False
            if ada_rekaman:
                pakai_audio = o3.toggle("Audio", value=True, key="audio_doc",
                                        help="Tampilkan tombol Dengarkan di setiap paragraf berbahasa Arab.")
                if pakai_audio:
                    pilihan_suara()
            doc = shown[pick]
            teks = siapkan_harakat_materi(doc)
            if pakai_audio:
                render_doc_audio(teks, cat, kitab=(mode == "Kertas"), ukuran=ukuran,
                                 asli=doc["text"])
            else:
                render_doc(teks, kitab=(mode == "Kertas"), ukuran=ukuran)

    with t2:
        q = st.text_input("Kata kunci (Indonesia / Arab):", key=f"search_{cat}", placeholder="contoh: sanggahan, حُجَّةٌ, نُقْطَةُ الاِسْتِشَارَةِ …")
        if q:
            hits = search(kb, q, k=10, cats=[cat], min_score=0.02)
            if not hits:
                st.warning("Tidak ditemukan. Coba kata kunci lain atau tanya MUNĀẒIR.")
            for h in hits:
                st.markdown(
                    f"<div class='snip'><div class='h'><b>{bungkus_arab(esc(terapkan_harakat(h['sub'])))}</b> › {esc(h['source'])} · relevansi {h['score']:.2f}</div>"
                    f"<div dir='auto'>{bungkus_arab(highlight(terapkan_harakat(h['text']), q)).replace(chr(10), '<br>')}</div></div>",
                    unsafe_allow_html=True,
                )

    with t3:
        with st.form(f"ask_{cat}", clear_on_submit=False):
            q2 = st.text_area(f"Pertanyaan tentang {meta['label']}:", height=90, key=f"askq_{cat}")
            go = st.form_submit_button("Tanyakan")
        if go and q2.strip():
            with st.spinner("Mencari jawaban…"):
                try:
                    raw, parsed, hits = answer_question(q2, cats=[cat])
                    st.session_state[f"ans_{cat}"] = (parsed, hits)
                except Exception as e:
                    st.session_state[f"ans_{cat}"] = None
                    st.error(str(e))
        res = st.session_state.get(f"ans_{cat}")
        if res:
            render_answer(*res)


def page_translate(kb):
    page_header("Penerjemah", "الْمُتَرْجِمُ", "Terjemahkan Indonesia ⇄ Arab dengan istilah debat dari basis pengetahuan.", "Alat")
    cek_api_key()
    c1, c2, c3 = st.columns([1.3, 1, 1])
    direction = c1.selectbox("Arah terjemahan", ["Otomatis", "Indonesia → Arab", "Arab → Indonesia"])
    style = c2.selectbox("Gaya bahasa", ["Formal debat", "Umum"])
    harakat = c3.checkbox("Beri harakat (Arab)", value=True)
    use_kb = st.checkbox("Gunakan istilah dari basis pengetahuan (glosarium)", value=True)
    text = st.text_area("Teks yang ingin diterjemahkan:", height=160, key="tr_text")

    if st.button("Terjemahkan") and text.strip():
        if direction == "Otomatis":
            direction_eff = "Arab → Indonesia" if is_mostly_arabic(text) else "Indonesia → Arab"
        else:
            direction_eff = direction
        glossary = ""
        if use_kb and kb["chunks"]:
            hits = search(kb, text, k=4, cats=["kosakata", "ibarah"]) or search(kb, text, k=3)
            glossary = build_context(hits, limit_chars=3500)
        instr = f"Arah: {direction_eff}. Gaya: {style}."
        if harakat and direction_eff.endswith("Arab"):
            instr += " Berikan harakat (syakal) lengkap pada teks Arab."
        user = f"{instr}\n\nGLOSARIUM:\n{glossary or '-'}\n\nTEKS:\n{text}"
        with st.spinner("Menerjemahkan…"):
            try:
                raw = call_llm([{"role": "system", "content": SYSTEM_TRANSLATE}, {"role": "user", "content": user}], temperature=0.2)
                hasil = parse_sections(raw, ("TERJEMAHAN", "CATATAN"))
                if harakat:
                    hasil = lengkapi_harakat(hasil, ("TERJEMAHAN", "CATATAN"))
                asal = text.strip()
                if harakat and is_mostly_arabic(asal):
                    asal = harakati(asal, maks_panggilan=4)  # teks Arab asli juga diberi harakat agar dibaca tepat
                hasil["ASAL"] = asal
                st.session_state["tr_result"] = hasil
                st.session_state["tts_terjemahan_on"] = False
            except Exception as e:
                st.session_state["tr_result"] = None
                st.error(str(e))

    res = st.session_state.get("tr_result")
    if res:
        tr = res.get("TERJEMAHAN", "")
        if is_mostly_arabic(tr):
            kotak_arab(fmt_inline(tr), "Hasil terjemahan", "التَّرْجَمَةُ")
        else:
            st.markdown(f"<div class='id-box'><div class='eyebrow'>Hasil terjemahan</div>{fmt_campur(tr)}</div>", unsafe_allow_html=True)
        st.code(tr, language=None)
        note = res.get("CATATAN", "").strip()
        if note and note != "-":
            with st.expander("Catatan istilah"):
                st.markdown(md_arab(note), unsafe_allow_html=True)


TIMER_HTML = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Aref+Ruqaa:wght@400;700&family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,500&family=Noto+Sans:wght@400;500;600&family=Noto+Serif:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--paper:#F4F0E7;--paper2:#FFFFFF;--ink:#202824;--ink2:#3C4B44;--muted:#4A5A52;--rule:#DCE7DF;--umber:#102A27;--cream:#F4F0E7;--brass:#C6A15B;--poi:#7FA58A;--stop:#D46A5A;--pro:#4E6B58;--kon:#9B4E3A}
*{box-sizing:border-box}
body{margin:0;font-family:'IBM Plex Sans',system-ui,sans-serif;color:var(--ink);background:transparent;-webkit-font-smoothing:antialiased}
.wrap{display:flex;flex-wrap:wrap;gap:20px}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
.main{flex:999 1 420px;min-width:0;padding:28px 22px 26px;border-radius:16px;background:var(--umber);color:var(--cream);display:flex;flex-direction:column;align-items:center;gap:16px}
.side{flex:1 1 260px;padding:18px 14px;border-radius:16px;background:var(--paper2);border:1px solid var(--rule);display:flex;flex-direction:column;gap:6px}
.tim{font-size:11px;letter-spacing:.16em;font-weight:600;text-align:center;text-transform:uppercase;line-height:2}
.nama{font-family:'Newsreader',Georgia,serif;font-size:26px;color:#F4F0E7;text-align:center;margin-top:4px}
.ar{font-family:'Amiri',serif;font-size:22px;line-height:2.4;word-spacing:.12em;color:#C6A15B;text-align:center;margin-top:8px}
.tar{font-family:'Amiri',serif;font-size:15px;letter-spacing:0;text-transform:none;font-weight:400;line-height:2;margin-left:4px}
.ring{position:relative;width:260px;height:260px}
.ring svg{display:block}
#arc{transition:stroke-dashoffset 1s linear,stroke .4s ease}
.ring .t{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.sisa{font-family:'Newsreader',Georgia,serif;font-size:64px;color:#F4F0E7;line-height:1;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.dari{font-size:12px;color:#9FB3A6;margin-top:6px}
.fase{display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border-radius:999px;border:1px solid;font-size:13px;font-weight:500;transition:color .3s,border-color .3s}
.fase i{width:8px;height:8px;border-radius:50%;display:inline-block;transition:background .3s}
.fase.jalan i{animation:pulse 1.2s ease-in-out infinite}
.btns{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin-top:4px}
button{font-family:inherit;cursor:pointer;transition:transform .15s cubic-bezier(.2,.7,.2,1),background-color .2s,border-color .2s}
button:active{transform:scale(.97)}
button:focus-visible{outline:2px solid var(--brass);outline-offset:2px}
.b2{min-height:44px;padding:0 18px;border-radius:8px;border:1px solid rgba(243,233,210,.28);background:transparent;color:var(--cream);font-size:14px}
.b2:hover{border-color:var(--brass)}
.b1{min-width:140px;min-height:44px;padding:0 24px;border-radius:8px;border:1px solid var(--cream);background:var(--cream);color:var(--umber);font-weight:600;font-size:15px}
.b1:hover{background:#FFFFFF}
.lbl{font-size:11px;letter-spacing:.14em;color:var(--muted);font-weight:600;padding:0 6px 8px}
.it{position:relative;display:flex;align-items:center;gap:10px;min-height:44px;padding:8px 12px;border-radius:8px;border:1px solid transparent;background:transparent;color:var(--ink2);font-size:14px;text-align:left;width:100%}
.it:hover{background:#F1EADC}
.it.on{background:#fff;border-color:var(--rule);color:var(--ink);box-shadow:0 6px 16px -12px rgba(43,31,21,.5)}
.it i{width:3px;height:22px;border-radius:2px;flex:none}
.it span{flex:1}
.it small{color:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}
.ket{margin-top:10px;padding:12px;border-top:1px solid var(--rule);font-size:12px;line-height:1.7;color:var(--muted)}
.ket b{font-weight:600}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style></head><body>
<div class="wrap">
 <div class="main">
  <div><div class="tim" id="tim"></div><div class="nama" id="nama"></div><div class="ar" id="ar" dir="rtl" lang="ar"></div></div>
  <div class="ring"><svg width="260" height="260" viewBox="0 0 300 300" aria-hidden="true"><circle cx="150" cy="150" r="130" fill="none" stroke="rgba(243,233,210,.10)" stroke-width="10"/><circle id="arc" cx="150" cy="150" r="130" fill="none" stroke="#C9A04E" stroke-width="10" stroke-linecap="round" stroke-dasharray="816.8" stroke-dashoffset="0" transform="rotate(-90 150 150)"/></svg>
   <div class="t"><div class="sisa" id="sisa" role="timer">00:00</div><div class="dari" id="dari"></div></div></div>
  <div class="fase" id="fase"><i id="dot"></i><span id="faseTxt"></span></div>
  <div class="btns"><button class="b2" id="ulang">Ulang</button><button class="b1" id="toggle">Mulai</button><button class="b2" id="next">Berikutnya &rarr;</button></div>
 </div>
 <div class="side"><div class="lbl">URUTAN PEMBICARA</div><div id="list" style="display:flex;flex-direction:column;gap:4px"></div>
  <div class="ket"><b style="color:#4E6B58">Hijau</b> POI boleh diajukan · <b style="color:#6B5526">Kuning</b> waktu terlindungi (menit pertama &amp; terakhir) · <b style="color:#B4513F">Merah</b> waktu habis. Bel berbunyi saat fase berganti.</div></div>
</div>
<script>
const U=__UTAMA__, B=__BALASAN__;
const P=[
 {t:'PRO',n:'Pembicara Pertama',ar:'الْمُوَالَاةُ – الْمُتَحَدِّثُ الْأَوَّلُ',m:U},
 {t:'KONTRA',n:'Pembicara Pertama',ar:'الْمُعَارَضَةُ – الْمُتَحَدِّثُ الْأَوَّلُ',m:U},
 {t:'PRO',n:'Pembicara Kedua',ar:'الْمُوَالَاةُ – الْمُتَحَدِّثُ الثَّانِي',m:U},
 {t:'KONTRA',n:'Pembicara Kedua',ar:'الْمُعَارَضَةُ – الْمُتَحَدِّثُ الثَّانِي',m:U},
 {t:'PRO',n:'Pembicara Ketiga',ar:'الْمُوَالَاةُ – الْمُتَحَدِّثُ الثَّالِثُ',m:U},
 {t:'KONTRA',n:'Pembicara Ketiga',ar:'الْمُعَارَضَةُ – الْمُتَحَدِّثُ الثَّالِثُ',m:U},
 {t:'KONTRA',n:'Pidato Balasan',ar:'الْمُعَارَضَةُ – خِطَابُ الرَّدِّ',m:B,r:1},
 {t:'PRO',n:'Pidato Balasan',ar:'الْمُوَالَاةُ – خِطَابُ الرَّدِّ',m:B,r:1}
];
let idx=0, jalan=false, lewat=0, faseLama='', ac=null;
const $=id=>document.getElementById(id);
function bel(n){try{ac=ac||new (window.AudioContext||window.webkitAudioContext)();for(let k=0;k<n;k++){const o=ac.createOscillator(),g=ac.createGain();o.type='sine';o.frequency.value=880;o.connect(g);g.connect(ac.destination);const t=ac.currentTime+k*0.35;g.gain.setValueAtTime(0.0001,t);g.gain.exponentialRampToValueAtTime(0.4,t+0.02);g.gain.exponentialRampToValueAtTime(0.0001,t+0.3);o.start(t);o.stop(t+0.32);}}catch(e){}}
function fase(p,total,sisa){
 if(lewat>=total) return ['Waktu habis','#D46A5A',3];
 if(p.r) return ['Pidato balasan – tanpa POI','#C9A04E',0];
 if(lewat<60) return ['Menit pertama – waktu terlindungi','#C9A04E',0];
 if(sisa<=60) return ['Menit terakhir – waktu terlindungi','#C9A04E',2];
 return ['POI boleh diajukan','#7FA58A',1];
}
function render(){
 const p=P[idx], total=p.m*60, sisa=Math.max(0,total-lewat);
 $('tim').innerHTML=p.t==='PRO'?'Tim Pro · <span class="tar" lang="ar">الْمُوَالَاةُ</span>':'Tim Kontra · <span class="tar" lang="ar">الْمُعَارَضَةُ</span>';
 $('tim').style.color=p.t==='PRO'?'#9CC2A7':'#E3A08F';
 $('nama').textContent=p.n; $('ar').textContent=p.ar;
 $('sisa').textContent=String(Math.floor(sisa/60)).padStart(2,'0')+':'+String(sisa%60).padStart(2,'0');
 $('dari').textContent='dari '+p.m+' menit';
 const f=fase(p,total,sisa);
 if(jalan && faseLama && f[0]!==faseLama && f[2]>0) bel(f[2]);
 faseLama=f[0];
 $('faseTxt').textContent=f[0]; $('fase').style.borderColor=f[1]; $('fase').style.color=f[1]; $('dot').style.background=f[1];
 $('fase').classList.toggle('jalan',jalan);
 $('arc').setAttribute('stroke',f[1]); $('arc').setAttribute('stroke-dashoffset',(816.8*Math.min(1,lewat/total)).toFixed(1));
 $('toggle').textContent=jalan?'Jeda':(lewat>0?'Lanjutkan':'Mulai');
 const L=$('list'); L.innerHTML='';
 P.forEach((x,i)=>{const b=document.createElement('button');b.className='it'+(i===idx?' on':'');
  b.innerHTML='<i style="background:'+(x.t==='PRO'?'#4E6B58':'#9B4E3A')+'"></i><span>'+(x.t==='PRO'?'Pro':'Kontra')+' – '+x.n+'</span><small>'+x.m+' mnt</small>';
  b.onclick=()=>{idx=i;jalan=false;lewat=0;faseLama='';render();}; L.appendChild(b);});
}
$('toggle').onclick=()=>{ac=ac||new (window.AudioContext||window.webkitAudioContext)(); if(lewat>=P[idx].m*60) return; jalan=!jalan; render();};
$('ulang').onclick=()=>{jalan=false;lewat=0;faseLama='';render();};
$('next').onclick=()=>{idx=(idx+1)%P.length;jalan=false;lewat=0;faseLama='';render();};
setInterval(()=>{if(jalan){lewat++;render();if(lewat>=P[idx].m*60){jalan=false;render();}}},1000);
render();
</script></body></html>"""


def page_timer():
    page_header("Timer Debat", "مُؤَقِّتُ الْمُنَاظَرَةِ",
                f"Untuk latihan dan simulasi lomba: urutan pembicara, sisa waktu, dan kapan {LABEL_POI} boleh diajukan.", "Alat")
    c1, c2, _ = st.columns([1, 1, 2])
    utama = c1.number_input("Pidato utama (menit)", min_value=1, max_value=15, value=7, key="t_utama")
    balasan = c2.number_input("Pidato balasan (menit)", min_value=1, max_value=10, value=4, key="t_balasan")
    import streamlit.components.v1 as components
    components.html(TIMER_HTML.replace("__UTAMA__", str(int(utama))).replace("__BALASAN__", str(int(balasan))),
                    height=650, scrolling=True)
    st.caption("Durasi bawaan: 7 menit pidato utama dan 4 menit pidato balasan. Sesuaikan dengan aturan lomba Anda.")


def page_feedback():
    page_header("Respon Pengguna", "آرَاءُ الْمُسْتَخْدِمِينَ",
                "Bagikan pengalaman, kritik, dan saran Anda tentang website MUNĀẒIR.", "Tentang")
    url = (_secret("FORM_URL") or FORM_URL).strip()
    if not url:
        st.info("Formulir respon belum diatur. Isi `FORM_URL` di app.py dengan link Google Form.")
        return
    if not url.startswith("http"):
        url = "https://" + url
    if "docs.google.com/forms" in url and "embedded=true" not in url:
        url += ("&" if "?" in url else "?") + "embedded=true"
    st.markdown("Terima kasih telah menggunakan **MUNĀẒIR**. Respon Anda membantu kami memperbaiki website ini.")
    import streamlit.components.v1 as components
    components.iframe(url, height=1100, scrolling=True)
    st.link_button("Formulir tidak muncul? Buka di tab baru ↗", url.replace("embedded=true", "").rstrip("?&"))


def link_kontak(jenis: str, nilai: str) -> str:
    """Ubah isi kontak menjadi link: WhatsApp → wa.me, Instagram → instagram.com, Email → mailto."""
    v, j = nilai.strip(), jenis.lower()
    if v.startswith("http"):
        return v
    if "mail" in j:
        return f"mailto:{v}"
    if "insta" in j:
        return f"https://instagram.com/{v.lstrip('@')}"
    if "wa" in j or "whatsapp" in j:
        nomor = re.sub(r"\D", "", v)
        if nomor.startswith("0"):
            nomor = "62" + nomor[1:]
        return f"https://wa.me/{nomor}"
    return ""


def page_profile():
    page_header("Profil Pengembang", "عَنِ الْمُطَوِّرِ", "Mengenal pengembang di balik MUNĀẒIR.", "Tentang")
    p = PROFIL
    if FOTO_PENGEMBANG:
        img = f"<img src='data:image/jpeg;base64,{FOTO_PENGEMBANG}' alt='Foto {esc(p['nama'])}'>"
    else:
        img = "<div class='kosong'></div>"
    baris = ""
    for k, v in p.get("kontak", {}).items():
        if not v.strip():
            continue
        url = link_kontak(k, v)
        isi = f"<span class='k'>{esc(k)}</span><span>{esc(v)}</span>"
        if url:
            baris += f"<li><a href='{esc(url)}' target='_blank' rel='noopener'>{isi}<span class='arr'>↗</span></a></li>"
        else:
            baris += f"<li><span class='row'>{isi}<span></span></span></li>"
    kontak = f"<ul class='pf-kontak'>{baris}</ul>" if baris else ""
    st.markdown(
        f"<div class='pf'><div class='pf-photo reveal'>{img}</div>"
        f"<div class='reveal' style='--i:1'><div class='eyebrow'>Pengembang</div><div class='pf-nama'>{esc(p['nama'])}</div>"
        f"<div class='pf-peran'>{esc(p['peran'])}</div><div class='pf-inst'>{esc(p['instansi'])}</div>"
        f"<div class='pf-bio'>{fmt_inline(p['bio'])}</div>{kontak}</div></div>",
        unsafe_allow_html=True,
    )


def panel_harakat_admin(kb):
    """Status harakat otomatis + tombol untuk mencoba lagi bila pekerja sedang menunggu."""
    st.markdown("<div class='subhead' style='margin-top:2rem'>Harakat otomatis</div>", unsafe_allow_html=True)
    state = pekerja_harakat()
    stt = state["status"]
    total = stt.get("total") or 0
    selesai = stt.get("selesai") or 0
    if total:
        st.progress(selesai / total, text=f"{selesai:,} dari {total:,} potongan teks Arab sudah berharakat")
    st.caption(f"Keadaan: {stt.get('keadaan', '-')}" + (f" · GitHub: {stt['github']}" if stt.get("github") else ""))
    if stt.get("model"):
        st.caption(f"Model yang dipakai: {stt['model']}" +
                   (f" · terakhir berhasil: {stt['model_terakhir']}" if stt.get("model_terakhir") else ""))
    if stt.get("galat"):
        st.caption(f"Galat terakhir dari Groq: {stt['galat']}")
    if st.button("Coba lagi sekarang", help="Hapus jeda model & hitungan gagal, lalu baca ulang daftar model Groq."):
        state["jeda"].clear()
        _gagal_harakat().clear()
        state["segarkan"] = True
        mulai_pekerja_harakat(kb["docs"])
        st.success("Pekerja harakat dijalankan ulang. Muat ulang halaman ini beberapa menit lagi untuk melihat progres.")
    if not (_secret("GITHUB_TOKEN") and _secret("GITHUB_REPO")):
        st.info(
            "Agar hasil harakat **permanen** (tidak hilang saat aplikasi di-restart), isi di **Settings → Secrets**:\n\n"
            "`GITHUB_TOKEN = \"token_github_anda\"`  \n`GITHUB_REPO = \"nama-akun/nama-repo\"`\n\n"
            "Hasil harakat lalu tersimpan otomatis ke GitHub setiap 10 menit."
        )


def page_manage(kb):
    page_header("Kelola Materi", "إِدَارَةُ الْمَوَادِّ", "Unggah file PDF / DOCX / TXT sebagai basis pengetahuan MUNĀẒIR.", "Admin")
    admin_pw = _secret("ADMIN_PASSWORD")
    if admin_pw and not st.session_state.get("admin_ok"):
        pw = st.text_input("Kata sandi admin", type="password")
        if st.button("Masuk"):
            if pw == admin_pw:
                st.session_state["admin_ok"] = True
                st.rerun()
            else:
                st.error("Kata sandi salah.")
        st.stop()

    st.info(
        "**Agar materi tersimpan permanen**, unggah file ke folder `data/<menu>/` di repository GitHub Anda. "
        "File yang diunggah di sini aktif sampai aplikasi di-restart."
    )
    cat = st.selectbox("Masukkan ke menu:", list(CATEGORIES), format_func=lambda k: CATEGORIES[k]["label"])
    existing = sorted({d["sub"] for d in kb["docs"] if d["cat"] == cat})
    sub_opt = st.selectbox("Subtopik:", existing + ["+ Subtopik baru…"], key="up_sub")
    sub = st.text_input("Nama subtopik baru", value="Unggahan") if sub_opt == "+ Subtopik baru…" else sub_opt
    sub = re.sub(r'[\\/:*?"<>|]', "-", (sub or "Unggahan").strip()) or "Unggahan"
    up_key = st.session_state.setdefault("up_key", 0)
    files = st.file_uploader(
        "Pilih file (bisa lebih dari satu)", type=["pdf", "docx", "txt", "md"], accept_multiple_files=True, key=f"uploader_{up_key}"
    )
    if st.button("Tambahkan ke basis pengetahuan", disabled=not files):
        added = 0
        for f in files:
            data = f.getvalue()
            text = extract_text(f.name, data)
            if not text.strip():
                st.warning(f"`{f.name}`: teks tidak terbaca (mungkin PDF hasil scan). Gunakan DOCX/TXT atau PDF berbasis teks.")
                continue
            saved = False
            try:
                target = DATA_DIR / cat / sub / Path(f.name).name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                saved = True
            except Exception:
                pass
            if not saved:
                st.session_state.setdefault("uploads", []).append(
                    make_doc(cat, sub, Path(f.name).stem, text, "upload")
                )
            added += 1
        if added:
            st.success(f"{added} file ditambahkan ke {CATEGORIES[cat]['label']} › {sub}.")
            build_disk_kb.clear()
            load_disk_docs.clear()
            st.session_state["up_key"] = up_key + 1
            st.rerun()

    panel_harakat_admin(kb)

    st.markdown("<div class='subhead' style='margin-top:2rem'>Isi basis pengetahuan</div>", unsafe_allow_html=True)
    counts = {}
    for c in kb["chunks"]:
        counts[(c["cat"], c["source"])] = counts.get((c["cat"], c["source"]), 0) + 1
    rows = [
        {"Menu": CATEGORIES[d["cat"]]["label"], "Subtopik": terapkan_harakat(d["sub"]), "File": terapkan_harakat(d["source"]),
         "Potongan": counts.get((d["cat"], d["source"]), 0),
         "Karakter": len(d["text"])}
        for d in kb["docs"]
    ]
    if rows:
        st.dataframe(rows, hide_index=True)
    else:
        st.caption("Belum ada file.")


# ─────────────────────────────────────────────────────────────
# NAVIGASI (MENU ATAS) & MAIN
# ─────────────────────────────────────────────────────────────
def halaman(fungsi, judul, alamat, ikon_menu=None, default=False):
    """Bungkus fungsi halaman menjadi st.Page dengan alamat sendiri (misal .../mosi)."""
    def jalankan():
        fungsi()
    jalankan.__name__ = f"halaman_{alamat}"
    return st.Page(jalankan, title=judul, icon=ikon_menu, url_path=alamat, default=default)


def main():
    # Ikon tab memakai lambang MUNĀẒIR bila berkasnya ada; kalau belum, tetap emoji.
    ikon = STATIC_DIR / "favicon.png"
    st.set_page_config(page_title="MUNĀẒIR · مُنَاظِرٌ", page_icon=(str(ikon) if ikon.exists() else "🕌"),
                       layout="wide", initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)
    st.session_state.setdefault("uploads", [])
    # Harakat untuk seluruh materi dibuat otomatis di latar belakang (pengunjung tidak menunggu)
    try:
        mulai_pekerja_harakat(get_kb()["docs"])
    except Exception:
        pass

    # Layar pembuka animasi logo 3D: hanya sekali tiap kali website dibuka
    if not st.session_state.get("splash_tampil"):
        st.session_state["splash_tampil"] = True
        vid = video_logo("splash-logo", ulang=False)
        if vid:
            st.markdown(
                f"<div class='splash' style='--t:{SPLASH_DETIK}s' aria-hidden='true'>{vid}"
                "<div class='splash-nama'>MUNĀẒIR<span lang='ar'>مناظر</span></div></div>",
                unsafe_allow_html=True,
            )
    try:
        st.logo(LOGO_SVG, size="large")
    except Exception:
        pass

    halaman_materi = [
        halaman(lambda c=cat: page_category(c, get_kb()), meta["label"], cat, IKON_MENU.get(cat))
        for cat, meta in CATEGORIES.items()
    ]
    menu = {
        "": [
            halaman(lambda: page_home(get_kb()), "Beranda", "beranda", ":material/home:", default=True),
            halaman(page_chat, "Chat MUNĀẒIR", "chat", ":material/forum:"),
        ],
        "Materi": halaman_materi,
        "Alat": [
            halaman(lambda: page_translate(get_kb()), "Penerjemah", "penerjemah", ":material/translate:"),
            halaman(page_timer, "Timer Debat", "timer", ":material/timer:"),
        ],
        "Tentang": [
            halaman(page_profile, "Profil Pengembang", "profil", ":material/person:"),
            halaman(page_feedback, "Respon", "respon", ":material/rate_review:"),
            halaman(lambda: page_manage(get_kb()), "Kelola Materi", "kelola", ":material/upload_file:"),
        ],
    }
    st.navigation(menu, position="top").run()

    st.markdown(
        f"<footer class='foot'><span><b>MUNĀẒIR</b><span class='ar-in' lang='ar' dir='rtl'>مُنَاظِرٌ</span> · Panduan debat bahasa Arab</span>"
        f"<span>Dikembangkan oleh {esc(PROFIL['nama'])}</span></footer>",
        unsafe_allow_html=True,
    )


# Foto pengembang (gambar JPEG yang disimpan sebagai teks base64, jangan diubah)
FOTO_PENGEMBANG = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAQDAwMDAgQDAwMEBAQFBgoGBgUFBgwICQcKDgwPDg4MDQ0PERYTDxAVEQ0NExoTFRcYGRkZDxIbHRsYHRYYGRj/2wBDAQQEBAYFBgsGBgsYEA0QGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBj/wAARCAB7AHsDASIAAhEBAxEB/8QAHQAAAAcBAQEAAAAAAAAAAAAAAAECAwQFBgcICf/EADsQAAECBAQEBAUACAcBAAAAAAECAwAEBREGEiExBxNBUQgiYXEUMoGRoRUjQnKxwdHhCRYkM1KCovH/xAAcAQABBQEBAQAAAAAAAAAAAAAAAQQFBgcCAwj/xAAyEQABAwIDBgUCBgMAAAAAAAABAAIDBBEFIUEGEjFhcZEHE1GBoSKxFTJSksHh0fDx/9oADAMBAAIRAxEAPwDzXvBmBA6RSl9YIoOC6wOsIkSoEJg72Fzaw6wJb2RwR9ozc/iuVQ8ZeVLpNyOYE6G29u8UJxQyh1ZQh1wrJBUtwnSJWHCpHt3nmyz3FPESjpZTFTsMluJvYe2Rv26LoY21g4yEvisNLSsvIzWFw6m6AB6A6xfytcptQcV8O6lBuf1ZO3tfeOajC5IhvNO8E4wXb2ir5BDO3ynHhc3B98rHqLc1YQBBCFRGK+BF0gaQdoK0CVCDgQIEWSQNYBNoHWCO0C4Q3OsC0FB6wIRRVV+cEtTeSFAKe8hJ1IHe0WpMZjELb01XpSSYQVOPBLaLdSVQ9w+MPmG9wGaqu2dbJSYVI6Li6ze/H4Wh4acJlY3mVz9ScUxS2FZUtpNi8b62P9I9I0Xgnw8EmlhWHpJwgADmoube51vGfwnLTeEMLU+iSFIXUptpAukKyNlZ1Pm3jfUTHFSp1YaksX4LcpSXLZZhmYDzZv01AP1EP6iSWQktNh1WRUcEMLQHtuel0xOeHfh3U5L4JvDEi2CMqXWgpCh9QY82cUeCVW4SVR2rSbCqjh55Yazk+eXUVaJX3HQH7x7RnsXylFmGwmkVioh06GSbCg2NwTmUNPa8ZzG01T+IeAapRGJSclZh+VW6w1PMKaWtSPMNDuQRtBDJLEQ4m41XVVTwTAtAAdpovG1LmjMSykL0W2rLa9zl6XPe0WAMUdD57czNy0ymzragFEnU+8XgiOr42sncG8FseyFXJV4TDJKbusRfoSB8BCBAgQ0VmQgQcFAkSYIwZMFvAuEWxgyYKBAhDpE6UwjWnMcYYqRkFqlHX2zzkEEIsq9l9rjUX7iIPSO30oTyKfS3pRptmkolELSU+dS3VebKT0ygEfaHVG7dfvBUzbdxNE2G2Tj9s1sZjh5MYjlviEVl9lAFkssPKasT1BTrEdOF5pt+UoL1YnZiWl3Ww6ZqYLwbUCSPOrzXI0t2AjRYfxIJCVU8tlSlpTdCBreMVIStOxdXvj5Wm1StFEwuacak0qW0hf7Ssw2IAte/SHzQ4i18lnDWx5G2a6Zj7C2Jq7SmBh6qKpk2wgKS6hCV81OlrX0uO2kTaZI4nZpTacTzMtUi0EcuaTL8hYUE2N0gka66i28R6VJUikVCZls01S6pOhLzss/zEDmAaOJCtCqwANt421XqbLmFsqkAOpRbMnYqtv8AeEc0tBavRwG8Hf8AF8/Kq1L/AOda1MsBI5s45qna2Y2hqO48b8OYQo2B6JN4ep0tT5x6ccRNM8rK6VgHOSdyL2+42vHDQdYYVT9+Uu/3gtX2UY2PDImAcL97klHA6QIEN1Y0OkCDtpBQISYBgusHvAvNJMCB1gGBCEX9MxniClUdNIl50/ApdDgaUkKtrcgHcA9ooIEKCRmF4VFNFUM3Jmhw5r0ZSKsw6w0+wQtDiQoeqSP6GLzA+F5+jtJlsOzj0hIpzKRLNOlCRmNyBYjcmOVU74hzB9KnpFwoIYDawNQSklP8o12GcX4ikFhSZcTCduth6+8SsbjYEFYfO3yJ3REX3SR2K7lWMJqxPhZinYrn5ubk23UzXKDpz81JuCHL5k+oBAI0N4q8f4vpODMHNz1UQ860Hm0liXUA4q52STpewJ+kRZDF+LapJNMGjcpvYLWcoP4jifiGnJ9Nfo9LnXytYl1TS0p0RdSsosPTKdfWPOolIzupLBaIV1WyJ4sDx0yGfzwWa4ucSGOImKGHqZIOSFJk0FMuy7bmKUqxW4uxIuSAN9gI58N4Ie0GIjnEuNytfpaaOmibDELNCPrAgoAhE5RwILrB3gSpEAQOsCBeaKBrbWATYXJAHc6RAmaxIywILnMX/wAW9fzHpHE+Q2YLpnWYjS0Td+pkDBzP21Psp14h1WpN0ymuvqILgQShHc2/hFFN4gnXlBqVSljNpcaqHreKmZK3wUvOKcKtFEm5MStPhLyQ6XIeiz3GvESBrHRYc0ud+o5AcwOJ97e69/VrhlM0jCNBq9PbM1SJilymbKLqlV8hFwu24UbkK7mx9abCNHmGayQyjRK7KSrUER3Lw6YsGNPD1heozZCnhJCTfUUixW1+rNxtYhINvWKrifTuHWAa9Kzr+LKRQpqcBWilzc0GlOW3U3c6JPZVhfY9Ie1dAR9UfZZ3R4nvENnOfr69f8pxqVIfQp8iyEg5eg7WEcK8WuEHcPUzB2L5tvlO1FcxKTKVk50WCVtDLsABnJ63V6R6j4OKwxiijLxVTMRUuvKSvlJbknOYiSI6LvrzD3IAttfc+fP8QGupLOCMNJSgqK5moKUT5k2CWx9DdX2jmnw4EHzRx+P7Xt+Py0s7JKQ2LTe+h5dDqvJ6SFJzAgg6giDtGWDk4y1nln1JcT0/ZI7WiVKYhUoZZpkZhoSnT8QwmwiVmbMx8rTcN8RKCoAbVAxu7t7jPuPdaDWBERmoykwfI8AeytIlXBAIt7iI18T4zZ4srtSV9NWN36aQPHIgpUDWBAjhPEjfSKWp1lUrMKl2EjMndRF/tF0Ld4wszMB6puKGy1H+MSmF07JXkvFwFn+32M1GH00bKZ+655OY42Azt6ZkZ8U6/OTMyo8x5ar9CYaDZI6esGCM2gtBrItoYsrWhosFiEkr5XF8hJJ1OZUdbTxfzMOBKrW8wuCPWFKQpQBWBcb26mDaJTOWOzo0v0I/tEgjynWFXK9v+BbFT6uG2KsOKl3HhTJlM4wABY85JBR3+ZF79j6R558QeGOINK4uT+LMcT7VRXV5wtqeaCkiWUAMrISflQE/LbQgHreN/wCBautU3xC1CivLbSmr0l1tGc6qcbUlwBI6mwUfYGNZ45MQy7U/QcLNi0xNzAnn0pGnKbGVF9NfMo+2X1j0yLc1zqofhCwnxHpFemOKNEZKsN5/0ZM09JuupIzDOtA2u2rY98w7xmvGtiZOIPEwZGWezytKprMujceZd3FGx/eA+npHb/A/j01TA1X4ezZQl+jTPxcqsaFcu8okp/6rCvor0jy34kKmuq+KDFjikAfDzAlAb3zBCd//AF+ILBC5OXHENqSF5b7EbiGVNhNjdRV1JN7+sOLVlOYi+loSDnI020vHKUJSb5b7RIbnJmXQVNrVoNr6Q0lJCdN4Jak3QkgXKr29tf6Ry5gcLOF16xTyQvEkTi1w1BsVq5V4vSiHVWuRraHrxV0V7PKLbO6FX+8WcU2rj8uZzANV9J7PVxrcNgncbktFzzGR+QVCqq1N0aZUgkKKMt+1za/5jDrtnzJFgna0avEkyWqaiXSdXla+w1P8oyWY57Xidwhm7CXHUrJvEaqEuJtiafyNAPU3P2IT+YBagNtx9YWhfmsraIa15Hkna4tDyVXIPeJVUCydfQVN5m/nQcyfcRIStLjCXEbKF/aGQfLrAl/I6tgWsfOj+YgQF0fgDiVWE/Exg2sqcWhpNTbl3uWkKUpDx5SkgHuF2jXeK6rKrHipq7biVA05tuSOtwSm6rjt8wH0jhqXHGJlDrWi0kKBvbUHSNrxKxQzjHirVMSy6kqE4WlKKAQM4aSF2B1AzBQ17R1ohdd8IdbNJ8T9PZLrTbdQkJmWOfdSgjmJSk9ypA/Mcbx/VE1riviertTC325qqTDjbi9ynmED7AW+kSMC4mawhxIoeJHXuUmSfK+Za5QShSQfW2aMs444+tcw8q7rii4tVrXUTcm3uTC3SJlRuemmsLaQkJ1IJ6+kNlViDbc9ocSoEjKDCITlhfy7RHWr/VlOY2Cb/Un+0LKz1AA733iGw4HHnnO6sunppCoV1R3eXPhN7BYykRooxzbqmnUOI+ZJvGvbWHGkuDZQBit41FZ7ZBr/AAtl8NK/zKaWkcc2m46H+x8rN4rebSWGgbukE27A/wDyM0EjTrFpiBROI37m+VKQPQWEViSc0StAzcgYOV++azvaqpNRi9Q8i1nEft+n+ExPryOMm+l7GHm3NPWIdVNkJ/eh1Gwh3fNV5WjawpAB+0IfDjYDreqmzmA7jqIZYJ5idYnK1b1hUqJRS42h1GqVC4MLQbTZB2WAoREp5uy6g/KlwgDtEtf+8z7KH8IXRIiqpLjkpLD9twKPsNYlFOtrxDdJViJkK1AZJH3ETHCeWr2hUJvNqVXHpCgbp8uh9oQNoWkDKIEJmae5TK3FahKSdog0peaUuRqTcwqrEiQeANvLDdKA/RqVW1udYTVCsb8tWYjY/iNRT5lJpjOZKlEJtcekZc6kg7Q7LzMw3LpQh1QSL2A94ZV9N57A3mrTsnjZwmpfLYkObbLqDr7r/9k="


if __name__ == "__main__":
    main()
