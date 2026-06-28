# AI Shorts Factory

Pipeline Python buat bikin video Shorts faceless otomatis: script → voiceover →
visual → caption animasi → render. Style-nya niru format @3intheworld /
@NarratoChannel (fact/story shorts dengan AI narration).

## 0. Yang harus diinstall dulu

1. **Python 3.10+** — cek dengan `python --version`
2. **ffmpeg** — wajib ada di sistem (bukan cuma lewat pip).
   - Windows: download dari https://ffmpeg.org/download.html, tambahin ke PATH
   - atau pakai `choco install ffmpeg` / `winget install ffmpeg`
3. Buka terminal di folder ini, lalu:
   ```
   pip install -r requirements.txt
   ```

## 1. API keys yang dibutuhkan

Copy `.env.example` jadi `.env`, isi dengan key kamu:

| Key | Gratis? | Cara dapat |
|---|---|---|
| `GEMINI_API_KEY` | Ada free tier | https://aistudio.google.com/apikey (akun Google biasa, BUKAN dari subscription AI Pro — ini API key developer terpisah) |
| `PEXELS_API_KEY` | 100% gratis | https://www.pexels.com/api/ — daftar, langsung dapat key |
| `LEONARDO_API_KEY` | Pakai credit yang sudah ada | https://cloud.leonardo.ai/api-access — generate key dari dashboard |

⚠️ **Penting**: `GEMINI_API_KEY` ini BUKAN bagian dari subscription Google AI Pro
kamu. Itu API key developer terpisah dari Google AI Studio, billingnya beda
(ada free tier yang cukup generous buat text generation, jadi kemungkinan besar
gratis buat pemakaian script generation harian).

## 2. Siapin background music + soundboard SFX

**Music** — drop 1-2 file `.mp3` royalty-free ke folder `assets/music/`:
- YouTube Audio Library (studio.youtube.com → Audio Library)
- https://pixabay.com/music/

**Soundboard (SFX)** — drop 2 file ke folder `assets/sfx/` dengan nama PERSIS ini:
- `whoosh.mp3` — bunyi transisi tiap kali cut ke segment baru
- `ding.mp3` — bunyi "ding/pop" pas badge angka muncul (format top3)

Sumber gratis buat SFX:
- https://pixabay.com/sound-effects/ — cari "whoosh" dan "ding" / "pop"
- https://mixkit.co/free-sound-effects/ — banyak whoosh & transition sound gratis

Kalau file-nya belum ada, pipeline tetep jalan normal (cuma skip efek itu) —
jadi gak wajib semua lengkap dari hari pertama. Mau nambah SFX lain (misal
"tick.mp3" buat suspense sebelum reveal)? Tinggal tambah function baru di
`modules/sfx_manager.py`, polanya udah ada buat dicontoh.

**Badge angka "#3 #2 #1"** — ini sudah otomatis, di-generate langsung sama
kode (`modules/rank_badge.py`) pakai Pillow, gak perlu asset gambar dari luar.
Cuma muncul kalau `CONTENT_FORMAT = "top3"` di config.py.

## 3. Edit config.py

Minimal yang perlu diubah:
- `NICHE_DESCRIPTION` — niche spesifik kamu
- `CONTENT_FORMAT` — `"top3"` atau `"story"`
- `LANGUAGE` — `"en"` atau `"id"`

## 4. Jalankan

```
python main.py
```

atau kasih topik spesifik:
```
python main.py "the deepest hole humans have ever dug"
```

Hasilnya muncul di folder `output/` — file `.mp4` siap upload + file `.json`
berisi script-nya (buat nulis title/description di YouTube).

## Soal Veo (video AI dari Google AI Pro)

Veo di subscription kamu cuma bisa dipakai manual lewat web app Gemini/Flow,
nggak ada di pipeline ini. Kalau mau pakai klip Veo: generate manual di Flow,
simpan filenya ke `assets/manual_veo/`, terus edit `main.py` buat masukin file
itu langsung sebagai salah satu segment alih-alih lewat
`fetch_visual_for_segment()`.

## Yang udah ke-cover vs yang masih level "manual/next upgrade"

Sudah otomatis di pipeline ini: script, voiceover, visual, caption animasi,
zoom Ken Burns, badge angka, whoosh+ding SFX, background music.

Belum, dan ini wajar buat versi awal — bisa ditambah belakangan kalau channel
udah jalan dan kerasa butuhnya:
- **Watermark/logo channel** di pojok (gampang, tambah 1 ImageClip lagi)
- **Outro card** dengan animasi subscribe di 2-3 detik terakhir
- **Color grading/LUT** konsisten antar video (butuh ffmpeg filter tambahan)

Gak perlu buru-buru semua — 90% video di niche ini sukses cuma modal script
bagus + caption rapi + pacing cepat. Elemen di atas itu "polish" tambahan,
bukan yang bikin atau gak laku.

## Hal yang perlu diingat sebelum upload

1. **Review manual dulu** sebelum publish — jangan auto-upload tanpa dicek.
   Selain buat quality control, ini juga yang ngebedain channel kamu dari
   channel "mass-produced" yang gampang kena flag.
2. Kalau visualnya AI-generated dan keliatan realistis (orang/tempat/event),
   centang toggle **"Altered or synthetic content"** di YouTube Studio pas upload.
3. Jangan upload >5 video/hari dengan pola identik — YouTube bisa nge-flag
   sebagai spam/inauthentic content dan itu bisa kena ke seluruh channel,
   bukan cuma 1 video. Mending 1 video matang per hari, konsisten.
4. Variasikan topik & sedikit gaya tiap beberapa video — jangan bener-bener
   template yang sama 100% setiap saat.

## Kalau ada error

Library yang dipakai di sini (`edge-tts`, `moviepy`) lumayan sering update dan
kadang ada breaking change kecil di API-nya. Kalau pas run ada error, paste
aja error message-nya ke Antigravity atau Gemini — karena scope tiap modul di
sini kecil dan jelas tanggung jawabnya, biasanya itu fix-nya cepat banget.
