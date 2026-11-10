# -*- coding: utf-8 -*-
"""
MUNĀẒIR — tambahan.py
Berkas pelengkap hasil revisi angket validasi ahli bahasa & ahli materi.

Letakkan berkas ini di folder yang SAMA dengan app.py (sejajar, bukan di dalam data/).

Isi:
  1. GAMBAR    — tujuh diagram (SVG) untuk Beranda dan halaman materi
  2. VIDEO     — panel video QatarDebate di setiap halaman materi
  3. ANGKA     — bank ibarah untuk data & argumentasi kuantitatif
  4. KAMUS     — sakelar tampilan kamus ringkas (hanya terjemahan)
  5. PENILAIAN — halaman Simulasi Penilaian Debat (lembar nilai juri)

Semua warna memakai token desain yang sudah ada di app.py (--umber, --brass, dst.),
jadi tampilannya otomatis seirama dengan website.
"""
import html
import re

import streamlit as st

# ─────────────────────────────────────────────────────────────
# UTILITAS KECIL (berdiri sendiri, tidak mengimpor app.py)
# ─────────────────────────────────────────────────────────────
HURUF_ARAB = re.compile(r"[\u0600-\u06FF]")
# Tajuk Arab di situs ini ditulis tanpa harakat (font Aref Ruqaa).
HARAKAT = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")


def tanpa_harakat(t: str) -> str:
    return HARAKAT.sub("", t or "")


def esc(t: str) -> str:
    return html.escape(t or "")


_CSS = """
<style>
.gbr{ background:var(--paper-2); border:1px solid var(--rule); border-radius:10px;
      padding:1.15rem 1.3rem 1rem; margin:.4rem 0 1.3rem; }
.gbr-h{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center;
        gap:.4rem 1rem; margin-bottom:1rem; }
.gbr-t{ font-family:var(--serif); font-size:1.08rem; color:var(--ink); line-height:1.25; }
.gbr-a{ font-family:var(--arab-judul); font-size:1.3rem; color:var(--brass-ink); line-height:2.1; }
.gbr svg{ width:100%; height:auto; display:block; }
.gbr-n{ font-size:.84rem; color:var(--muted); margin-top:.85rem; line-height:1.65; }
.gbr-n b{ color:var(--brass-ink); font-weight:600; }

.kart{ background:var(--paper-2); border:1px solid var(--rule); border-left:3px solid var(--brass);
       border-radius:8px; padding:.85rem 1.1rem; margin:0 0 .7rem; }
.kart .ar{ font-family:var(--arab); font-size:1.4rem; line-height:2.55; word-spacing:.14em;
           color:var(--ink); text-align:right; direction:rtl; }
.kart .id{ color:var(--ink-2); font-size:.92rem; line-height:1.6; margin-top:.35rem; }
.grup{ font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; font-weight:600;
       color:var(--brass-ink); margin:1.3rem 0 .6rem; }
.grup:first-child{ margin-top:.2rem; }

.nilai-t{ background:var(--paper-2); border:1px solid var(--rule); border-radius:10px;
          padding:1rem 1.2rem; margin:.3rem 0 1rem; }
.nilai-t table{ width:100%; border-collapse:collapse; font-size:.9rem; }
.nilai-t th{ text-align:left; font-size:.68rem; letter-spacing:.12em; text-transform:uppercase;
             color:var(--muted); font-weight:600; padding:.4rem .5rem; border-bottom:1px solid var(--rule); }
.nilai-t td{ padding:.5rem; border-bottom:1px solid var(--rule-soft); color:var(--ink-2); }
.nilai-t td.n{ text-align:right; font-variant-numeric:tabular-nums; color:var(--ink); }
.nilai-t tr:last-child td{ border-bottom:none; font-weight:600; color:var(--ink); }
.menang{ background:var(--umber); color:var(--cream); border-radius:12px;
         padding:1.3rem 1.5rem; margin:.4rem 0 1.2rem; }
.menang .k{ font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; color:#9FB3A6; font-weight:600; }
.menang .v{ font-family:var(--serif); font-size:1.9rem; line-height:1.2; margin-top:.35rem; }
.menang .s{ color:#DCE7DF; font-size:.9rem; margin-top:.45rem; }

.kms{ display:flex; align-items:center; gap:1rem; background:var(--paper-2);
      border:1px solid var(--rule); border-radius:8px; padding:.7rem 1rem; margin:0 0 .45rem; }
.kms .idn{ flex:1; min-width:0; color:var(--ink); font-size:1rem; line-height:1.45; }
.kms .arb{ font-family:var(--arab); font-size:1.55rem; line-height:2.1; color:var(--ink);
           direction:rtl; text-align:right; white-space:nowrap; }
.kms .tma{ font-size:.7rem; letter-spacing:.1em; text-transform:uppercase; color:var(--muted);
           display:block; margin-top:.15rem; }
.kms-h{ font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; font-weight:600;
        color:var(--brass-ink); margin:1.2rem 0 .5rem; }
.kms-h:first-child{ margin-top:.2rem; }
</style>
"""


def _css():
    st.markdown(_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# 1. GAMBAR — diagram SVG
# ─────────────────────────────────────────────────────────────
HIJAU, HIJAU_BG = "#4E6B58", "#E9F0EB"
MERAH, MERAH_BG = "#9B4E3A", "#F7EBE7"
EMAS, EMAS_BG = "#C6A15B", "#F6EFDF"


def _kotak(x, y, w, h, arab="", judul="", baris=(), garis="var(--rule)", isi="var(--paper-2)",
           warna_ar="var(--brass-ink)", ukuran_ar=16):
    """Satu kotak diagram: teks Arab di atas, judul Latin, lalu keterangan."""
    g = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{isi}" stroke="{garis}" stroke-width="1.2"/>']
    cx = x + w / 2
    ty = y + 30
    if arab:
        g.append(f'<text x="{cx}" y="{ty}" text-anchor="middle" font-size="{ukuran_ar}" fill="{warna_ar}" '
                 f'font-family="Amiri, serif" direction="rtl">{arab}</text>')
        ty += 26
    if judul:
        g.append(f'<text x="{cx}" y="{ty}" text-anchor="middle" font-size="13" font-weight="600" '
                 f'fill="var(--ink)" font-family="IBM Plex Sans, sans-serif">{esc(judul)}</text>')
        ty += 19
    for b in baris:
        g.append(f'<text x="{cx}" y="{ty}" text-anchor="middle" font-size="10.5" fill="var(--muted)" '
                 f'font-family="IBM Plex Sans, sans-serif">{esc(b)}</text>')
        ty += 14
    return "".join(g)


def _panah(x1, x2, y):
    """Panah mendatar antar kotak."""
    return (f'<line x1="{x1}" y1="{y}" x2="{x2 - 7}" y2="{y}" stroke="{EMAS}" stroke-width="1.4"/>'
            f'<path d="M{x2} {y} L{x2 - 8} {y - 4.5} L{x2 - 8} {y + 4.5} Z" fill="{EMAS}"/>')


def _svg_format_qatar() -> str:
    urutan = [
        ("pro", "Pembicara 1", "7 menit"),
        ("kontra", "Pembicara 1", "7 menit"),
        ("pro", "Pembicara 2", "7 menit"),
        ("kontra", "Pembicara 2", "7 menit"),
        ("pro", "Pembicara 3", "7 menit"),
        ("kontra", "Pembicara 3", "7 menit"),
        ("kontra", "Pidato balasan", "4 menit"),
        ("pro", "Pidato balasan", "4 menit"),
    ]
    g = ['<svg viewBox="0 0 720 530" xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="Skema format debat Qatar Debate">']
    g.append('<rect x="255" y="6" width="210" height="46" rx="9" fill="var(--umber)"/>')
    g.append('<text x="360" y="25" text-anchor="middle" font-size="12" fill="#F4F0E7" '
             'font-family="IBM Plex Sans, sans-serif">Ketua sidang</text>')
    g.append('<text x="360" y="43" text-anchor="middle" font-size="13" fill="#C6A15B" '
             'font-family="Amiri, serif" direction="rtl">رَئِيسُ الْجَلْسَةِ</text>')
    g.append(f'<text x="170" y="78" text-anchor="middle" font-size="10.5" letter-spacing="2.2" '
             f'font-weight="600" fill="{HIJAU}" font-family="IBM Plex Sans, sans-serif">TIM PRO</text>')
    g.append(f'<text x="170" y="98" text-anchor="middle" font-size="15" fill="{HIJAU}" '
             f'font-family="Amiri, serif" direction="rtl">الْمُوَالَاةُ</text>')
    g.append(f'<text x="550" y="78" text-anchor="middle" font-size="10.5" letter-spacing="2.2" '
             f'font-weight="600" fill="{MERAH}" font-family="IBM Plex Sans, sans-serif">TIM KONTRA</text>')
    g.append(f'<text x="550" y="98" text-anchor="middle" font-size="15" fill="{MERAH}" '
             f'font-family="Amiri, serif" direction="rtl">الْمُعَارَضَةُ</text>')
    for i, (sisi, nama, lama) in enumerate(urutan):
        y = 112 + i * 44
        pro = sisi == "pro"
        x = 40 if pro else 420
        isi, garis = (HIJAU_BG, HIJAU) if pro else (MERAH_BG, MERAH)
        g.append(f'<rect x="{x}" y="{y}" width="260" height="36" rx="8" fill="{isi}" stroke="{garis}" '
                 f'stroke-width="1.1"/>')
        g.append(f'<text x="{x + 16}" y="{y + 23}" font-size="12.5" fill="var(--ink)" '
                 f'font-family="IBM Plex Sans, sans-serif">{esc(nama)}</text>')
        g.append(f'<text x="{x + 244}" y="{y + 23}" text-anchor="end" font-size="11" fill="var(--muted)" '
                 f'font-family="IBM Plex Sans, sans-serif">{esc(lama)}</text>')
        g.append(f'<circle cx="360" cy="{y + 18}" r="14" fill="var(--paper)" stroke="{EMAS}" stroke-width="1.3"/>')
        g.append(f'<text x="360" y="{y + 22.5}" text-anchor="middle" font-size="12" fill="var(--brass-ink)" '
                 f'font-family="Newsreader, Georgia, serif">{i + 1}</text>')
    g.append('<rect x="240" y="472" width="240" height="46" rx="9" fill="var(--paper-3)" '
             'stroke="var(--rule)" stroke-width="1.2"/>')
    g.append('<text x="360" y="491" text-anchor="middle" font-size="12" fill="var(--ink)" '
             'font-family="IBM Plex Sans, sans-serif">Dewan juri</text>')
    g.append('<text x="360" y="509" text-anchor="middle" font-size="13" fill="var(--brass-ink)" '
             'font-family="Amiri, serif" direction="rtl">لَجْنَةُ التَّحْكِيمِ</text>')
    g.append("</svg>")
    return "".join(g)


def _svg_alur_waktu() -> str:
    x0, lebar = 52, 616
    seg = lebar / 7
    g = ['<svg viewBox="0 0 720 150" xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="Alur waktu pidato utama tujuh menit">']
    g.append('<text x="52" y="22" font-size="11" letter-spacing="1.6" font-weight="600" '
             'fill="var(--muted)" font-family="IBM Plex Sans, sans-serif">PIDATO UTAMA · 7 MENIT</text>')
    for i in range(7):
        x = x0 + i * seg
        lindung = i == 0 or i == 6
        isi, garis = (EMAS_BG, EMAS) if lindung else (HIJAU_BG, HIJAU)
        g.append(f'<rect x="{x:.1f}" y="40" width="{seg - 2:.1f}" height="50" rx="5" fill="{isi}" '
                 f'stroke="{garis}" stroke-width="1.1"/>')
    g.append(f'<text x="360" y="71" text-anchor="middle" font-size="13" fill="{HIJAU}" '
             f'font-family="IBM Plex Sans, sans-serif">نُقْطَةُ الاِسْتِشَارَةِ · POI boleh diajukan</text>')
    for i in range(8):
        x = x0 + i * seg
        g.append(f'<line x1="{x:.1f}" y1="94" x2="{x:.1f}" y2="100" stroke="var(--rule)" stroke-width="1"/>')
        g.append(f'<text x="{x:.1f}" y="114" text-anchor="middle" font-size="10.5" fill="var(--muted)" '
                 f'font-family="IBM Plex Sans, sans-serif">{i}</text>')
    g.append('<text x="360" y="136" text-anchor="middle" font-size="10.5" fill="var(--muted)" '
             'font-family="IBM Plex Sans, sans-serif">menit</text>')
    g.append("</svg>")
    return "".join(g)


def _svg_anatomi_hujjah() -> str:
    isi = [
        ("الدَّعْوَى", "Klaim", ("Pernyataan yang", "kami ajukan")),
        ("التَّعْلِيلُ", "Alasan", ("Mengapa klaim itu", "masuk akal")),
        ("الدَّلِيلُ", "Bukti", ("Data, contoh,", "atau kesaksian")),
        ("الْأَثَرُ", "Dampak", ("Mengapa ini penting", "bagi mosi")),
    ]
    g = ['<svg viewBox="0 0 720 150" xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="Anatomi hujjah: klaim, alasan, bukti, dampak">']
    for i, (ar, judul, baris) in enumerate(isi):
        x = i * 190
        g.append(_kotak(x, 10, 150, 120, ar, judul, baris))
        if i < 3:
            g.append(_panah(x + 152, x + 188, 70))
    g.append("</svg>")
    return "".join(g)


def _svg_analisis_mosi() -> str:
    isi = [
        ("تَعْرِيفٌ", "Definisi", ("Batasan makna", "istilah mosi")),
        ("أَرْضِيَّةٌ", "Landasan", ("Konteks dan", "keadaan saat ini")),
        ("نِقَاطُ الاِشْتِبَاكِ", "Titik bentrok", ("Di mana kedua tim", "benar-benar berbeda")),
        ("عِبْءُ الْإِثْبَاتِ", "Beban pembuktian", ("Apa yang wajib", "dibuktikan tiap tim")),
    ]
    g = ['<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="Empat langkah analisis mosi">']
    g.append('<rect x="250" y="0" width="220" height="48" rx="9" fill="var(--umber)"/>')
    g.append('<text x="360" y="20" text-anchor="middle" font-size="12" fill="#F4F0E7" '
             'font-family="IBM Plex Sans, sans-serif">Mosi</text>')
    g.append('<text x="360" y="39" text-anchor="middle" font-size="14" fill="#C6A15B" '
             'font-family="Amiri, serif" direction="rtl">الْقَضِيَّةُ</text>')
    g.append(f'<line x1="360" y1="48" x2="360" y2="74" stroke="{EMAS}" stroke-width="1.3"/>')
    g.append(f'<line x1="85" y1="74" x2="635" y2="74" stroke="{EMAS}" stroke-width="1.3"/>')
    for i, (ar, judul, baris) in enumerate(isi):
        x = i * 186.7
        cx = x + 80
        g.append(f'<line x1="{cx:.1f}" y1="74" x2="{cx:.1f}" y2="96" stroke="{EMAS}" stroke-width="1.3"/>')
        g.append(_kotak(x, 96, 160, 124, ar, judul, baris, ukuran_ar=13))
    g.append("</svg>")
    return "".join(g)


def _svg_struktur_muqaddimah() -> str:
    isi = [
        ("تَحِيَّةٌ", "Salam dan sapaan", "Salam, sapaan kepada ketua sidang, juri, dan lawan"),
        ("تَعْرِيفٌ", "Definisi mosi", "Batasan istilah dan ruang lingkup yang diperdebatkan"),
        ("مَوْقِفُ الْفَرِيقِ", "Posisi tim", "Pernyataan sikap tim beserta garis besar alasannya"),
        ("تَقْسِيمُ الْأَدْوَارِ", "Pembagian tugas", "Apa yang dibawakan pembicara pertama, kedua, dan ketiga"),
        ("عَرْضُ الْحُجَجِ", "Paparan argumen", "Argumen utama lengkap dengan alasan dan buktinya"),
    ]
    g = ['<svg viewBox="0 0 720 292" xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="Lima bagian muqaddimah">']
    for i, (ar, judul, ket) in enumerate(isi):
        y = i * 56
        g.append(f'<circle cx="22" cy="{y + 23}" r="16" fill="var(--paper)" stroke="{EMAS}" stroke-width="1.3"/>')
        g.append(f'<text x="22" y="{y + 28}" text-anchor="middle" font-size="13" fill="var(--brass-ink)" '
                 f'font-family="Newsreader, Georgia, serif">{i + 1}</text>')
        g.append(f'<rect x="50" y="{y}" width="670" height="46" rx="8" fill="var(--paper-2)" '
                 f'stroke="var(--rule)" stroke-width="1.1"/>')
        g.append(f'<text x="68" y="{y + 21}" font-size="12.5" font-weight="600" fill="var(--ink)" '
                 f'font-family="IBM Plex Sans, sans-serif">{esc(judul)}</text>')
        g.append(f'<text x="68" y="{y + 37}" font-size="10.5" fill="var(--muted)" '
                 f'font-family="IBM Plex Sans, sans-serif">{esc(ket)}</text>')
        g.append(f'<text x="704" y="{y + 30}" text-anchor="end" font-size="16" fill="var(--brass-ink)" '
                 f'font-family="Amiri, serif">{ar}</text>')
        if i < 4:
            g.append(f'<line x1="22" y1="{y + 39}" x2="22" y2="{y + 63}" stroke="{EMAS}" '
                     f'stroke-width="1.1" stroke-dasharray="3 3"/>')
    g.append("</svg>")
    return "".join(g)


def _svg_fungsi_ibarah() -> str:
    atas = [("الاِفْتِتَاحُ", "Membuka"), ("التَّأْطِيرُ", "Membingkai"),
            ("الاِسْتِدْلَالُ", "Berargumen"), ("تَقْدِيمُ الْبَيِّنَةِ", "Memberi bukti")]
    bawah = [("التَّفْنِيدُ", "Menyanggah"), ("نُقْطَةُ الاِسْتِشَارَةِ", "Menjawab POI"),
             ("الْخِتَامُ", "Menutup")]
    g = ['<svg viewBox="0 0 720 212" xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="Fungsi ibarah sepanjang satu pidato">']

    def pil(x, y, ar, idn):
        return (f'<rect x="{x:.1f}" y="{y}" width="165" height="56" rx="28" fill="var(--paper-2)" '
                f'stroke="{EMAS}" stroke-width="1.1"/>'
                f'<text x="{x + 82.5:.1f}" y="{y + 24}" text-anchor="middle" font-size="13.5" '
                f'fill="var(--brass-ink)" font-family="Amiri, serif" direction="rtl">{ar}</text>'
                f'<text x="{x + 82.5:.1f}" y="{y + 43}" text-anchor="middle" font-size="11.5" '
                f'fill="var(--ink-2)" font-family="IBM Plex Sans, sans-serif">{esc(idn)}</text>')

    for i, (ar, idn) in enumerate(atas):
        g.append(pil(i * 185, 10, ar, idn))
        if i < 3:
            g.append(_panah(i * 185 + 167, i * 185 + 183, 38))
    g.append(f'<path d="M690 66 L690 96 L30 96 L30 126" stroke="{EMAS}" stroke-width="1.2" '
             f'fill="none" stroke-dasharray="4 4"/>')
    for i, (ar, idn) in enumerate(bawah):
        g.append(pil(92.5 + i * 185, 130, ar, idn))
        if i < 2:
            g.append(_panah(92.5 + i * 185 + 167, 92.5 + i * 185 + 183, 158))
    g.append("</svg>")
    return "".join(g)


def _svg_kriteria_penilaian() -> str:
    isi = [("الْمُحْتَوَى", "Isi", 40, "Kekuatan argumen, alasan, dan bukti"),
           ("الْأُسْلُوبُ", "Gaya", 40, "Suara, bahasa, kontak mata, dan percaya diri"),
           ("الاِسْتِرَاتِيجِيَّةُ", "Strategi", 20, "Ketepatan peran, prioritas, dan waktu")]
    X_BATANG, L_BATANG = 300, 380          # batang nilai mulai di 300, panjang penuh 380
    SKALA = L_BATANG / 40.0
    g = ['<svg viewBox="0 0 720 234" xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="Bobot kriteria penilaian debat">']
    for i, (ar, judul, nilai, ket) in enumerate(isi):
        y = i * 76
        g.append(f'<text x="0" y="{y + 24}" font-size="13" font-weight="600" fill="var(--ink)" '
                 f'font-family="IBM Plex Sans, sans-serif">{esc(judul)}</text>')
        g.append(f'<text x="250" y="{y + 26}" text-anchor="end" font-size="15" fill="var(--brass-ink)" '
                 f'font-family="Amiri, serif">{ar}</text>')
        g.append(f'<text x="0" y="{y + 45}" font-size="10.5" fill="var(--muted)" '
                 f'font-family="IBM Plex Sans, sans-serif">{esc(ket)}</text>')
        g.append(f'<rect x="{X_BATANG}" y="{y + 10}" width="{L_BATANG}" height="30" rx="6" '
                 f'fill="var(--paper-3)"/>')
        g.append(f'<rect x="{X_BATANG}" y="{y + 10}" width="{nilai * SKALA:.0f}" height="30" rx="6" '
                 f'fill="{EMAS_BG}" stroke="{EMAS}" stroke-width="1.1"/>')
        g.append(f'<text x="{X_BATANG + nilai * SKALA - 14:.0f}" y="{y + 30}" text-anchor="end" '
                 f'font-size="13" fill="var(--ink)" font-family="Newsreader, Georgia, serif">{nilai}</text>')
    g.append("</svg>")
    return "".join(g)


GAMBAR = {
    "format_qatar": ("Format dan urutan bicara", "نِظَامُ الْمُنَاظَرَةِ", _svg_format_qatar,
                     "Angka di tengah menunjukkan <b>urutan bicara</b>. Enam pidato utama bergantian "
                     "pro–kontra, lalu dua pidato balasan yang dibuka oleh tim kontra."),
    "alur_waktu": ("Alur waktu satu pidato", "زَمَنُ الْخِطَابِ", _svg_alur_waktu,
                   "Menit pertama dan menit terakhir adalah <b>waktu terlindungi</b>: POI tidak boleh "
                   "diajukan. Di antara keduanya, lawan boleh berdiri mengajukan "
                   "<b>نُقْطَةُ الاِسْتِشَارَةِ</b>."),
    "anatomi_hujjah": ("Anatomi satu argumen", "بِنْيَةُ الْحُجَّةِ", _svg_anatomi_hujjah,
                       "Argumen baru utuh bila keempat bagian ini lengkap. Argumen yang berhenti di "
                       "<b>klaim</b> paling mudah dipatahkan lawan."),
    "analisis_mosi": ("Empat langkah membedah mosi", "تَحْلِيلُ الْقَضِيَّةِ", _svg_analisis_mosi,
                      "Kerjakan berurutan saat persiapan. <b>Titik bentrok</b> adalah hal yang paling "
                      "menentukan arah debat, bukan definisi."),
    "struktur_muqaddimah": ("Lima bagian muqaddimah", "أَجْزَاءُ الْمُقَدِّمَةِ", _svg_struktur_muqaddimah,
                            "Urutan ini dipakai pembicara pertama. Pembicara kedua dan ketiga "
                            "mengganti bagian definisi dengan <b>sanggahan</b> lebih dahulu."),
    "fungsi_ibarah": ("Fungsi ibarah sepanjang pidato", "وَظَائِفُ الْعِبَارَاتِ", _svg_fungsi_ibarah,
                      "Setiap kotak punya banknya sendiri di halaman ini. Pilih satu ibarah untuk "
                      "tiap fungsi, lalu hafalkan agar lancar saat tampil."),
    "kriteria_penilaian": ("Bobot penilaian juri", "مَعَايِيرُ التَّحْكِيمِ", _svg_kriteria_penilaian,
                           "Total 100 untuk setiap pidato utama. <b>Pidato balasan</b> dinilai "
                           "setengahnya, yaitu maksimal 50."),
}

GAMBAR_MENU = {
    "sistem_debat": ["format_qatar", "alur_waktu", "anatomi_hujjah", "kriteria_penilaian"],
    "mosi": ["analisis_mosi"],
    "ibarah": ["fungsi_ibarah"],
    "kosakata": ["anatomi_hujjah"],
    "muqaddimah": ["struktur_muqaddimah", "format_qatar"],
}


def gambar(nama: str):
    """Tampilkan satu diagram beserta judul dan catatannya."""
    if nama not in GAMBAR:
        return
    judul, arab, buat, catatan = GAMBAR[nama]
    st.markdown(
        f"<div class='gbr'><div class='gbr-h'><div class='gbr-t'>{esc(judul)}</div>"
        f"<div class='gbr-a' dir='rtl' lang='ar'>{tanpa_harakat(arab)}</div></div>"
        f"{buat()}<div class='gbr-n'>{catatan}</div></div>",
        unsafe_allow_html=True,
    )


def gambar_beranda():
    """Dipanggil dari page_home: skema format debat di bawah daftar isi."""
    _css()
    st.markdown(
        "<section class='sec'><div class='sec-head'><div><div class='eyebrow'>Sekilas format</div>"
        "<div class='sec-t'>Seperti apa jalannya satu debat?</div></div>"
        "<p class='sec-note'>Delapan pidato, dua tim, satu mosi. Diagram ini dibahas lengkap pada "
        "menu Kumpulan Sistem Debat.</p></div></section>",
        unsafe_allow_html=True,
    )
    gambar("format_qatar")


# ─────────────────────────────────────────────────────────────
# 2. VIDEO — rekaman debat & pelatihan QatarDebate
#    CATATAN: tautan di bawah ini WAJIB diperiksa satu per satu
#    sebelum dipakai. Hapus baris yang videonya sudah tidak ada.
# ─────────────────────────────────────────────────────────────
KANAL_QD = "https://www.youtube.com/@qatardebate"

FINAL_ARAB = {
    "judul": "Final Kejuaraan Debat Bahasa Arab — Lebanon vs Turki",
    "url": "https://www.youtube.com/watch?v=Glj8jM2vmx8",
    "ket": "Debat penuh dalam format Qatar Debate. Perhatikan urutan bicara, cara juri duduk, "
           "dan bagaimana pembicara berdiri saat mengajukan POI.",
}
HASIL_FINAL = {
    "judul": "Pengumuman pemenang Kejuaraan Debat Bahasa Arab",
    "url": "https://www.youtube.com/watch?v=6uAPS11brUQ",
    "ket": "Cuplikan penjurian dan pengumuman hasil pada kejuaraan debat bahasa Arab Qatar.",
}
PERSIAPAN = {
    "judul": "Strategi persiapan debat — pelatih QatarDebate",
    "url": "https://www.youtube.com/watch?v=90VV2I0y4Pg",
    "ket": "Pelatih di Markaz Munazharat Qatar menjelaskan langkah persiapan sebelum naik mimbar.",
}
STRATEGI = {
    "judul": "Strategi dalam munazarah",
    "url": "https://www.youtube.com/watch?v=7Zie31k3Mp8",
    "ket": "Pengertian strategi debat dan penerapannya sebelum serta saat debat berlangsung.",
}
PENGAJARAN = {
    "judul": "Mengajarkan seni munazarah",
    "url": "https://www.youtube.com/watch?v=qrAS2ympigU",
    "ket": "Pembahasan cara menumbuhkan budaya debat, dengan debat sekolah di Qatar sebagai contoh.",
}

VIDEO = {
    "sistem_debat": [FINAL_ARAB, PERSIAPAN, STRATEGI, HASIL_FINAL],
    "mosi": [FINAL_ARAB, STRATEGI],
    "ibarah": [FINAL_ARAB, PERSIAPAN],
    "kosakata": [FINAL_ARAB],
    "muqaddimah": [FINAL_ARAB, PENGAJARAN],
}

JUDUL_VIDEO = {
    "ibarah": "Dengar ibarah ini dipakai dalam debat sungguhan",
    "muqaddimah": "Dengar muqaddimah dibawakan dalam debat sungguhan",
}


def panel_video(cat: str):
    """Panel video rujukan untuk satu menu materi."""
    daftar = VIDEO.get(cat)
    if not daftar:
        return
    judul = JUDUL_VIDEO.get(cat, "Video rujukan debat")
    with st.expander(f"{judul} · {len(daftar)} video", expanded=False):
        st.caption(
            "Video berikut berasal dari kanal QatarDebate dan siaran kejuaraan debat bahasa Arab. "
            "Gunakan sebagai contoh penyampaian, bukan sebagai sumber materi website."
        )
        for v in daftar:
            st.markdown(f"**{v['judul']}**")
            try:
                st.video(v["url"])
            except Exception:
                st.caption("Video tidak dapat dimuat di sini.")
            st.markdown(f"<div class='gbr-n'>{esc(v['ket'])}</div>", unsafe_allow_html=True)
            st.markdown("<div style='height:1.1rem'></div>", unsafe_allow_html=True)
        st.link_button("Buka kanal QatarDebate ↗", KANAL_QD)


# ─────────────────────────────────────────────────────────────
# 3. ANGKA — ibarah untuk data dan argumentasi kuantitatif
# ─────────────────────────────────────────────────────────────
IBARAH_ANGKA = [
    ("Menyebut angka dan persentase", [
        ("تَبْلُغُ النِّسْبَةُ الْمِئَوِيَّةُ سَبْعِينَ بِالْمِائَةِ.",
         "Persentasenya mencapai tujuh puluh persen."),
        ("مَا يُعَادِلُ ثُلُثَ الْمُجْتَمَعِ تَقْرِيبًا.",
         "Yang setara dengan hampir sepertiga masyarakat."),
        ("وَاحِدٌ مِنْ كُلِّ خَمْسَةِ طُلَّابٍ يُعَانِي مِنْ هَذِهِ الْمُشْكِلَةِ.",
         "Satu dari setiap lima mahasiswa mengalami masalah ini."),
        ("أَكْثَرُ مِنْ نِصْفِ الْعَيِّنَةِ أَيَّدَ هَذَا الرَّأْيَ.",
         "Lebih dari separuh sampel mendukung pendapat ini."),
        ("مَا يَزِيدُ عَلَى مِلْيُونِ شَخْصٍ.",
         "Lebih dari satu juta orang."),
        ("مَا يَقْرُبُ مِنْ ثَلَاثِينَ بِالْمِائَةِ.",
         "Mendekati tiga puluh persen."),
    ]),
    ("Kenaikan, penurunan, dan kelipatan", [
        ("اِرْتَفَعَ الْمُعَدَّلُ بِنِسْبَةِ عِشْرِينَ بِالْمِائَةِ خِلَالَ خَمْسِ سَنَوَاتٍ.",
         "Rata-ratanya naik dua puluh persen dalam lima tahun."),
        ("اِنْخَفَضَتِ النِّسْبَةُ إِلَى النِّصْفِ.",
         "Persentasenya turun hingga separuh."),
        ("تَضَاعَفَ الْعَدَدُ ثَلَاثَةَ أَضْعَافٍ.",
         "Jumlahnya menjadi tiga kali lipat."),
        ("يَتَزَايَدُ هَذَا الرَّقْمُ بِوَتِيرَةٍ مُتَسَارِعَةٍ عَامًا بَعْدَ عَامٍ.",
         "Angka ini meningkat dengan laju yang makin cepat dari tahun ke tahun."),
        ("فِي الْمُتَوَسِّطِ، يُنْفِقُ الطَّالِبُ سَاعَتَيْنِ يَوْمِيًّا.",
         "Rata-rata, seorang mahasiswa menghabiskan dua jam setiap hari."),
    ]),
    ("Menyebut sumber data", [
        ("تُشِيرُ الْإِحْصَاءَاتُ الصَّادِرَةُ عَنْ وِزَارَةِ التَّعْلِيمِ إِلَى أَنَّ...",
         "Statistik yang dikeluarkan Kementerian Pendidikan menunjukkan bahwa..."),
        ("أَظْهَرَتْ دِرَاسَةٌ حَدِيثَةٌ أَنَّ...",
         "Sebuah penelitian terbaru menunjukkan bahwa..."),
        ("وَفْقًا لِتَقْرِيرِ الْبَنْكِ الدَّوْلِيِّ لِهَذَا الْعَامِ...",
         "Menurut laporan Bank Dunia tahun ini..."),
        ("وَهَذَا رَقْمٌ مُوَثَّقٌ يُمْكِنُ الرُّجُوعُ إِلَيْهِ.",
         "Ini angka terdokumentasi yang dapat ditelusuri kembali."),
    ]),
    ("Membandingkan angka", [
        ("بِالْمُقَارَنَةِ مَعَ الْعَامِ الْمَاضِي، الْفَارِقُ وَاضِحٌ.",
         "Dibandingkan tahun lalu, selisihnya terlihat jelas."),
        ("أَيْ ضِعْفَ مَا ذَكَرَهُ الْفَرِيقُ الْمُقَابِلُ.",
         "Yakni dua kali lipat dari yang disebutkan tim lawan."),
        ("الْفَارِقُ بَيْنَ الرَّقْمَيْنِ شَاسِعٌ وَلَا يُمْكِنُ تَجَاهُلُهُ.",
         "Selisih antara kedua angka itu sangat jauh dan tak bisa diabaikan."),
        ("وَهَذَا يُمَثِّلُ أَعْلَى نِسْبَةٍ مُسَجَّلَةٍ حَتَّى الْآنَ.",
         "Dan ini merupakan persentase tertinggi yang tercatat sampai sekarang."),
    ]),
    ("Menyanggah data lawan", [
        ("هَذِهِ الْإِحْصَائِيَّةُ قَدِيمَةٌ وَلَا تُعَبِّرُ عَنِ الْوَاقِعِ الْيَوْمَ.",
         "Statistik ini sudah lama dan tidak menggambarkan keadaan hari ini."),
        ("الْعَيِّنَةُ الَّتِي اعْتَمَدَ عَلَيْهَا الْفَرِيقُ الْمُقَابِلُ غَيْرُ مُمَثِّلَةٍ.",
         "Sampel yang dijadikan sandaran tim lawan tidak representatif."),
        ("الرَّقْمُ الْمُطْلَقُ لَا يَكْفِي دُونَ بَيَانِ النِّسْبَةِ.",
         "Angka mutlak tidak memadai tanpa menyebutkan persentasenya."),
        ("الاِرْتِبَاطُ بَيْنَ الظَّاهِرَتَيْنِ لَا يَعْنِي وُجُودَ عَلَاقَةٍ سَبَبِيَّةٍ.",
         "Adanya korelasi antara dua gejala tidak berarti ada hubungan sebab-akibat."),
        ("مِنْ أَيْنَ اسْتَقَى الْفَرِيقُ الْمُقَابِلُ هَذَا الرَّقْمَ؟",
         "Dari mana tim lawan memperoleh angka ini?"),
    ]),
]


def panel_angka():
    """Bank ibarah untuk menyampaikan data dan angka."""
    jumlah = sum(len(x[1]) for x in IBARAH_ANGKA)
    with st.expander(f"Ungkapan data dan angka · {jumlah} ibarah", expanded=False):
        st.caption(
            "Ibarah untuk menyampaikan persentase, kelipatan, dan statistik, serta untuk "
            "mempersoalkan data yang dibawakan lawan. Angka pada contoh boleh diganti sesuai mosi."
        )
        for judul, isi in IBARAH_ANGKA:
            st.markdown(f"<div class='grup'>{esc(judul)}</div>", unsafe_allow_html=True)
            for ar, idn in isi:
                st.markdown(
                    f"<div class='kart'><div class='ar' lang='ar'>{ar}</div>"
                    f"<div class='id'>{esc(idn)}</div></div>",
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────
# 4. KAMUS — tampilan ringkas (hanya terjemahan)
#
#    PENTING: ringkas_kamus() harus dikenakan pada teks tampilan
#    DAN pada teks asli dengan aturan yang sama. Kalau hanya salah
#    satu yang dipotong, jumlah paragrafnya tidak lagi sama dan
#    tombol Dengarkan di menu Kamus akan hilang.
# ─────────────────────────────────────────────────────────────
AWALAN_PENJELASAN = ("penjelasan", "keterangan", "catatan", "contoh penggunaan",
                     "uraian", "makna istilah", "definisi:")
BATAS_PROSA = 80  # baris non-Arab lebih panjang dari ini dianggap penjelasan


def _baris_penjelasan(baris: str) -> bool:
    s = baris.strip()
    if not s or HURUF_ARAB.search(s):
        return False
    if re.match(r"^(JUDUL|MENU|SUMBER):", s) or set(s) <= set("=-_ "):
        return False
    if s.lower().startswith(AWALAN_PENJELASAN):
        return True
    return len(s) > BATAS_PROSA


def sakelar_kamus(cat: str):
    """Sakelar tampilan kamus ringkas; hanya muncul di menu Kamus Debat."""
    if cat != "kosakata":
        return
    st.toggle(
        "Tampilan kamus ringkas",
        value=False,
        key="kamus_ringkas",
        help="Sembunyikan paragraf penjelasan sehingga setiap entri hanya menampilkan "
             "istilah Arab dan terjemahannya.",
    )


def ringkas_kamus(teks: str, cat: str, diam: bool = False) -> str:
    """Buang paragraf penjelasan dari materi kamus bila sakelar dinyalakan.

    `diam=True` dipakai saat memotong teks asli (untuk pencocokan rekaman),
    supaya keterangannya tidak tercetak dua kali di layar.
    """
    if cat != "kosakata" or not st.session_state.get("kamus_ringkas") or not teks:
        return teks
    simpan, dibuang = [], 0
    for baris in teks.split("\n"):
        if _baris_penjelasan(baris):
            dibuang += 1
        else:
            simpan.append(baris)
    if dibuang and not diam:
        st.caption(f"Tampilan kamus ringkas aktif: {dibuang} baris penjelasan disembunyikan. "
                   "Matikan sakelar di atas untuk melihat materi utuh.")
    return "\n".join(simpan)


# ─────────────────────────────────────────────────────────────
# 5. PANEL ATAS HALAMAN MATERI
# ─────────────────────────────────────────────────────────────
def panel_atas(cat: str):
    """Gambar, video, bank ibarah angka, dan sakelar kamus di atas tab halaman materi."""
    _css()
    daftar = GAMBAR_MENU.get(cat, [])
    if daftar:
        gambar(daftar[0])
        if len(daftar) > 1:
            with st.expander(f"Diagram lain di menu ini · {len(daftar) - 1}", expanded=False):
                for nama in daftar[1:]:
                    gambar(nama)
    panel_video(cat)
    if cat in ("ibarah", "kosakata"):
        panel_angka()


# ─────────────────────────────────────────────────────────────
# 6. HALAMAN SIMULASI PENILAIAN DEBAT
# ─────────────────────────────────────────────────────────────
PEMBICARA = [("pro", "Pembicara 1"), ("pro", "Pembicara 2"), ("pro", "Pembicara 3"),
             ("kontra", "Pembicara 1"), ("kontra", "Pembicara 2"), ("kontra", "Pembicara 3")]

RENTANG = [
    ("40 / 20", "Istimewa", "Nyaris tanpa cela, sulit dibantah"),
    ("36–39 / 18–19", "Sangat baik", "Kuat dan meyakinkan, kelemahan kecil"),
    ("33–35 / 17", "Baik", "Di atas rata-rata, ada celah yang terlihat"),
    ("30–32 / 15–16", "Cukup", "Memenuhi tugas, belum menonjol"),
    ("27–29 / 14", "Kurang", "Banyak bagian tidak tuntas"),
    ("≤ 26 / ≤ 13", "Sangat kurang", "Tugas peran tidak terpenuhi"),
]


def _nilai(label: str, kunci: str, kecil: bool = False):
    """Satu kolom isian nilai; 'kecil' untuk pidato balasan (bobot setengah)."""
    if kecil:
        return st.number_input(label, min_value=0, max_value=20, value=15, step=1, key=kunci)
    return st.number_input(label, min_value=0, max_value=40, value=30, step=1, key=kunci)


def _nilai_strategi(label: str, kunci: str, kecil: bool = False):
    if kecil:
        return st.number_input(label, min_value=0, max_value=10, value=7, step=1, key=kunci)
    return st.number_input(label, min_value=0, max_value=20, value=15, step=1, key=kunci)


def _baris_pembicara(tim: str, nama: str, kecil: bool = False):
    kunci = f"nilai_{tim}_{nama}".replace(" ", "_").lower()
    c1, c2, c3 = st.columns(3)
    with c1:
        isi = _nilai("Isi", f"{kunci}_isi", kecil)
    with c2:
        gaya = _nilai("Gaya", f"{kunci}_gaya", kecil)
    with c3:
        strategi = _nilai_strategi("Strategi", f"{kunci}_strategi", kecil)
    total = isi + gaya + strategi
    st.caption(f"Jumlah {nama}: **{total}** dari {50 if kecil else 100}")
    return {"nama": nama, "isi": isi, "gaya": gaya, "strategi": strategi, "total": total}


def _tabel(judul: str, baris: list, total: int) -> str:
    tr = "".join(
        f"<tr><td>{esc(b['nama'])}</td><td class='n'>{b['isi']}</td><td class='n'>{b['gaya']}</td>"
        f"<td class='n'>{b['strategi']}</td><td class='n'>{b['total']}</td></tr>"
        for b in baris
    )
    return (f"<div class='nilai-t'><div class='eyebrow'>{esc(judul)}</div>"
            "<table><thead><tr><th>Pembicara</th><th style='text-align:right'>Isi</th>"
            "<th style='text-align:right'>Gaya</th><th style='text-align:right'>Strategi</th>"
            "<th style='text-align:right'>Jumlah</th></tr></thead><tbody>"
            f"{tr}<tr><td>Total tim</td><td class='n'>—</td><td class='n'>—</td>"
            f"<td class='n'>—</td><td class='n'>{total}</td></tr></tbody></table></div>")


def _lembar_teks(mosi, nama_pro, nama_kontra, pro, kontra, t_pro, t_kontra) -> str:
    def blok(judul, baris, total):
        garis = [f"{judul}", "-" * 56,
                 f"{'Pembicara':<22}{'Isi':>6}{'Gaya':>7}{'Strategi':>10}{'Jumlah':>9}"]
        for b in baris:
            garis.append(f"{b['nama']:<22}{b['isi']:>6}{b['gaya']:>7}{b['strategi']:>10}{b['total']:>9}")
        garis.append(f"{'TOTAL TIM':<22}{'':>6}{'':>7}{'':>10}{total:>9}")
        return "\n".join(garis)

    selisih = abs(t_pro - t_kontra)
    if t_pro == t_kontra:
        hasil = "Seri — juri perlu memberi nilai pembeda."
    else:
        unggul = nama_pro if t_pro > t_kontra else nama_kontra
        hasil = f"Pemenang: {unggul} (selisih {selisih} angka)."
    return (
        "LEMBAR PENILAIAN DEBAT BAHASA ARAB\n"
        "Format Qatar Debate · dihasilkan dari website MUNĀẒIR\n"
        + "=" * 56 + "\n"
        f"Mosi: {mosi or '-'}\n\n"
        + blok(f"TIM PRO — {nama_pro}", pro, t_pro) + "\n\n"
        + blok(f"TIM KONTRA — {nama_kontra}", kontra, t_kontra) + "\n\n"
        + "=" * 56 + "\n" + hasil + "\n\n"
        "Bobot: Isi 40, Gaya 40, Strategi 20 untuk setiap pidato utama.\n"
        "Pidato balasan dinilai setengahnya (maksimal 50).\n"
    )


def page_penilaian():
    """Halaman Simulasi Penilaian Debat — lembar nilai juri."""
    _css()
    st.markdown(
        "<div class='ph'><div class='eyebrow'>Alat</div>"
        "<div class='ph-row'><div class='ph-t'>Simulasi Penilaian Debat</div>"
        "<div class='ph-a' dir='rtl' lang='ar'>محاكاة التحكيم</div></div>"
        "<p class='ph-d'>Lembar nilai juri untuk latihan: isi skor delapan pembicara, "
        "lalu jumlah tim dan pemenangnya dihitung otomatis.</p>"
        "<div class='rule-draw'></div></div>",
        unsafe_allow_html=True,
    )

    gambar("kriteria_penilaian")

    with st.expander("Rentang skor dan maknanya", expanded=False):
        baris = "".join(
            f"<tr><td class='n'>{esc(r)}</td><td>{esc(k)}</td><td>{esc(d)}</td></tr>"
            for r, k, d in RENTANG
        )
        st.markdown(
            "<div class='nilai-t'><table><thead><tr>"
            "<th style='text-align:right'>Skor (utama / balasan)</th><th>Kategori</th>"
            "<th>Keterangan</th></tr></thead>"
            f"<tbody>{baris}</tbody></table></div>",
            unsafe_allow_html=True,
        )
        st.caption("Kolom Isi dan Gaya memakai rentang pertama, kolom Strategi memakai rentang "
                   "setengahnya. Nilai di luar 27–40 sebaiknya disertai catatan tertulis dari juri.")

    mosi = st.text_input("Mosi yang diperdebatkan", placeholder="Tulis mosi di sini…", key="pn_mosi")
    c1, c2 = st.columns(2)
    nama_pro = c1.text_input("Nama tim pro", value="Tim Pro", key="pn_nama_pro")
    nama_kontra = c2.text_input("Nama tim kontra", value="Tim Kontra", key="pn_nama_kontra")

    t_pro_tab, t_kon_tab = st.tabs([f"Nilai {nama_pro or 'Tim Pro'}", f"Nilai {nama_kontra or 'Tim Kontra'}"])
    pro, kontra = [], []

    with t_pro_tab:
        for _, nama in [p for p in PEMBICARA if p[0] == "pro"]:
            st.markdown(f"<div class='subhead'>{esc(nama)}</div>", unsafe_allow_html=True)
            pro.append(_baris_pembicara("pro", nama))
        st.markdown("<div class='subhead'>Pidato balasan</div>", unsafe_allow_html=True)
        pro.append(_baris_pembicara("pro", "Pidato balasan", kecil=True))

    with t_kon_tab:
        for _, nama in [p for p in PEMBICARA if p[0] == "kontra"]:
            st.markdown(f"<div class='subhead'>{esc(nama)}</div>", unsafe_allow_html=True)
            kontra.append(_baris_pembicara("kontra", nama))
        st.markdown("<div class='subhead'>Pidato balasan</div>", unsafe_allow_html=True)
        kontra.append(_baris_pembicara("kontra", "Pidato balasan", kecil=True))

    t_pro = sum(b["total"] for b in pro)
    t_kontra = sum(b["total"] for b in kontra)
    selisih = abs(t_pro - t_kontra)

    st.markdown("<div class='subhead' style='margin-top:2rem'>Hasil</div>", unsafe_allow_html=True)
    if t_pro == t_kontra:
        judul, ket = "Hasil seri", f"Kedua tim sama-sama mengumpulkan {t_pro} angka."
    else:
        unggul = (nama_pro or "Tim Pro") if t_pro > t_kontra else (nama_kontra or "Tim Kontra")
        judul = unggul
        ket = f"Unggul {selisih} angka · {t_pro} berbanding {t_kontra}."
    st.markdown(
        f"<div class='menang'><div class='k'>Pemenang menurut skor</div>"
        f"<div class='v'>{esc(judul)}</div><div class='s'>{esc(ket)}</div></div>",
        unsafe_allow_html=True,
    )

    k1, k2 = st.columns(2)
    with k1:
        st.markdown(_tabel(f"Tim pro · {nama_pro}", pro, t_pro), unsafe_allow_html=True)
    with k2:
        st.markdown(_tabel(f"Tim kontra · {nama_kontra}", kontra, t_kontra), unsafe_allow_html=True)

    st.download_button(
        "Unduh lembar penilaian (.txt)",
        data=_lembar_teks(mosi, nama_pro or "Tim Pro", nama_kontra or "Tim Kontra",
                          pro, kontra, t_pro, t_kontra).encode("utf-8"),
        file_name="lembar_penilaian_debat.txt",
        mime="text/plain",
    )
    st.caption("Angka di sini adalah latihan penjurian, bukan hasil resmi lomba. "
               "Setiap juri lomba tetap wajib menulis catatan alasan di samping skornya.")


# ─────────────────────────────────────────────────────────────
# 7. KAMUS DEBAT — basis data entri + kolom pencarian dua arah
#    Materi kosakata tidak lagi ditampilkan sebagai bacaan; isinya
#    diurai jadi entri dan hanya dibuka lewat pencarian.
# ─────────────────────────────────────────────────────────────
PEMISAH_JUDUL = re.compile(r"^={10,}\s*$", re.M)
HURUF_ARAB_DASAR = re.compile(r"[\u0621-\u063A\u0641-\u064A]")


def _badan(teks: str) -> str:
    bagian = PEMISAH_JUDUL.split(teks or "", maxsplit=1)
    return bagian[1] if len(bagian) == 2 else (teks or "")


def _polos_arab(t: str) -> str:
    """Samakan bentuk huruf agar pencarian tidak gagal karena harakat atau hamzah."""
    t = tanpa_harakat(t)
    for a, b in (("أإآٱ", "ا"), ("ى", "ي"), ("ة", "ه"), ("ؤ", "و"), ("ئ", "ي")):
        for c in a:
            t = t.replace(c, b)
    # "ال" di awal kata dilepas agar الحجة juga menemukan حجة
    kata = [k[2:] if k.startswith("ال") and len(k) > 4 else k for k in t.split()]
    return re.sub(r"\s+", " ", " ".join(kata)).strip()


@st.cache_data(show_spinner=False)
def susun_kamus(bahan: tuple) -> list:
    """Ubah berkas kosakata menjadi daftar entri {idn, arab, tema, sumber}."""
    entri, terlihat = [], set()
    for judul, teks in bahan:
        tema = judul
        for baris in _badan(teks).split("\n"):
            b = baris.strip()
            if not b:
                continue
            if " : " not in b:
                # baris tanpa pemisah dianggap tajuk tema, misalnya "AGAMA DAN PEMIKIRAN"
                if len(b) < 60 and not HURUF_ARAB_DASAR.search(b):
                    tema = b.title()
                continue
            kiri, kanan = [x.strip() for x in b.split(" : ", 1)]
            if not kiri or not kanan:
                continue
            # pola berkas MIZAN adalah "Indonesia : عربي"; bila terbalik, ditukar
            if HURUF_ARAB_DASAR.search(kiri) and not HURUF_ARAB_DASAR.search(kanan):
                kiri, kanan = kanan, kiri
            if not HURUF_ARAB_DASAR.search(kanan):
                continue
            kunci = (kiri.lower(), _polos_arab(kanan))
            if kunci in terlihat:
                continue
            terlihat.add(kunci)
            entri.append({"idn": kiri, "arab": kanan, "tema": tema,
                          "idn_cari": kiri.lower(), "arab_cari": _polos_arab(kanan)})
    return entri


def _cocok(entri: list, q: str, arah: str) -> list:
    """Urutkan hasil: sama persis dulu, lalu berawalan, lalu mengandung."""
    arab = bool(HURUF_ARAB_DASAR.search(q))
    if arah == "Indonesia → Arab":
        arab = False
    elif arah == "Arab → Indonesia":
        arab = True
    kunci = _polos_arab(q) if arab else q.lower().strip()
    if not kunci:
        return []
    medan = "arab_cari" if arab else "idn_cari"
    sama, awal, isi = [], [], []
    for e in entri:
        v = e[medan]
        if v == kunci:
            sama.append(e)
        elif v.startswith(kunci):
            awal.append(e)
        elif kunci in v:
            isi.append(e)
    return sama + awal + isi


def _kartu(e: dict) -> str:
    return (f"<div class='kms'><div class='idn'>{esc(e['idn'])}"
            f"<span class='tma'>{esc(e['tema'])}</span></div>"
            f"<div class='arb' lang='ar'>{e['arab']}</div></div>")


def page_kamus(docs: list):
    """Kamus Debat: tanpa bacaan, hanya pencarian dua arah."""
    _css()
    bahan = tuple((d.get("title") or d.get("source", ""), d.get("text", "")) for d in docs)
    entri = susun_kamus(bahan)
    if not entri:
        st.info("Belum ada entri kosakata yang terbaca.")
        return

    tema = sorted({e["tema"] for e in entri})
    st.caption(f"{len(entri)} entri dari {len(tema)} tema. "
               "Ketik dalam bahasa Indonesia atau Arab — arahnya dikenali sendiri.")

    c1, c2 = st.columns([2, 1.3])
    q = c1.text_input("Cari kata", key="kamus_cari", placeholder="argumen · حُجَّة · menyanggah …",
                      label_visibility="collapsed")
    arah = c2.radio("Arah pencarian", ["Otomatis", "Indonesia → Arab", "Arab → Indonesia"],
                    horizontal=False, key="kamus_arah", label_visibility="collapsed")

    if q and q.strip():
        hasil = _cocok(entri, q, arah)
        if not hasil:
            st.warning(f"Tidak ada entri yang cocok dengan \u201c{q}\u201d. "
                       "Coba kata dasarnya, atau tukar arah pencarian.")
            return
        st.caption(f"{len(hasil)} entri ditemukan.")
        for e in hasil[:200]:
            st.markdown(_kartu(e), unsafe_allow_html=True)
        if len(hasil) > 200:
            st.caption(f"Ditampilkan 200 dari {len(hasil)} entri. Persempit pencarian Anda.")
        return

    pilih = st.selectbox("Atau telusuri per tema", ["—"] + tema, key="kamus_tema")
    if pilih != "—":
        isi = [e for e in entri if e["tema"] == pilih]
        st.markdown(f"<div class='kms-h'>{esc(pilih)} · {len(isi)} entri</div>", unsafe_allow_html=True)
        for e in isi:
            st.markdown(_kartu(e), unsafe_allow_html=True)
