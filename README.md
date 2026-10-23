# 🕌 MUNAZIR · مُنَاظِر

**Panduan & Pedoman Debat Bahasa Arab** dengan chatbot AI (Groq) yang menjawab berdasarkan file materi Anda.

## Fitur
- 💬 **Chat MUNAZIR**: jawaban berbahasa Indonesia, lalu teks Arab yang dikutip dari sumber, disertai nama file sumbernya.
- ⚖️ **Kumpulan Sistem Debat** · 📜 **Mosi** · 🖋️ **Ibarah** · 📖 **Kosa Kata** · 🕌 **Muqaddimah**: tiap menu punya daftar materi, pencarian, dan tanya-jawab AI khusus menu itu.
- 🌐 **Penerjemah** Indonesia ⇄ Arab yang memakai istilah dari basis pengetahuan, dengan opsi harakat.
- 📤 **Kelola Materi**: unggah PDF / DOCX / TXT langsung dari website.

## Struktur folder
```
app.py                 ← aplikasi utama
requirements.txt
DAFTAR_MATERI.md       ← daftar lengkap 129 file materi & klasifikasinya
.streamlit/config.toml ← tema coklat & emas
data/
  <menu>/<subtopik>/<file>.txt
  sistem_debat/  mosi/  ibarah/  kosakata/  muqaddimah/
```
Basis pengetahuan berasal dari 10 sumber: buku **MIZAN**, **Al-Murshed fi Fann al-Munazarah**, booklet QatarDebate (Arab & Inggris), dan slide pelatihan. Semua sumber itu sudah diekstrak menjadi teks bersih lalu dipecah per topik.
Setiap file diawali header `JUDUL / MENU / SUMBER` agar asal materi selalu jelas.

**Menambah materi permanen:** upload file ke `data/<menu>/<subtopik>/` di GitHub. Subfolder baru otomatis muncul sebagai subtopik.
Format terbaik untuk teks Arab adalah **.docx atau .txt**, karena PDF hasil scan atau PDF tertentu sering membuat huruf Arab terbaca acak.

## Deploy (tanpa coding)
1. Buat repository baru di GitHub. Upload lewat web GitHub dibatasi **maksimal 100 file per sekali upload**, sedangkan proyek ini berisi 136 file. Karena itu, gunakan file `munazir_github_upload.zip`:
   - Klik **Add file → Upload files**, lalu drag **semua isi** folder `BAGIAN_1`. Setelah itu klik **Commit changes**.
   - Ulangi dengan **semua isi** folder `BAGIAN_2`. Folder `data` di dalamnya akan otomatis tergabung dengan yang sudah ada.
   - Folder `.streamlit` bisa saja tidak ikut terupload karena namanya diawali titik. Kalau begitu, klik **Add file → Create new file**, beri nama `.streamlit/config.toml`, lalu salin isinya.
2. Buka **share.streamlit.io**, klik **Create app**, pilih repo Anda, dan isi *Main file* dengan `app.py`.
3. Buka **Advanced settings → Secrets** (atau setelah deploy: **⋮ → Settings → Secrets**), lalu tempel:
   ```toml
   GROQ_API_KEY = "gsk_key_anda"
   # ADMIN_PASSWORD = "sandi"   # opsional, untuk mengunci menu Kelola Materi
   ```
4. Klik **Deploy** dan tunggu sampai selesai.

> ⚠️ **Jangan pernah menulis API key di file yang diupload ke GitHub.** Key yang bocor di GitHub akan dicabut otomatis oleh Groq.

## Jalankan di komputer
```bash
pip install -r requirements.txt
# buat file .streamlit/secrets.toml berisi GROQ_API_KEY = "..."
streamlit run app.py
```
