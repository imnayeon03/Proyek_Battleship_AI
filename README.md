# WAR BATTLESHIPS - Bayesian AI vs Manusia (10S3109 Kecerdasan Buatan, Proyek 1)

Game perang kapal 10x10 dengan Pygame: laut bergelombang, mode SIANG/MALAM, peluru, ledakan, percikan. Kategori: Uncertainty | Metode: inferensi probabilistik (Bayesian) | Pembanding: Random AI.

## Menjalankan
    pip install -r requirements.txt     # numpy + pygame (jika gagal: pip install pygame-ce)
    python main.py                      # game Pygame: Human vs AI
    python main.py --fleet dataset --dataset-id 3
    python manual_input.py              # input armada manual (tersimpan di data/custom_layouts.csv)
    python bukti_ai.py                  # bukti AI benar-benar menginferensi (300 armada acak)
    python evaluate.py                  # Bayes vs Random pada data/layouts.csv -> docs/hasil_evaluasi.csv
    python run_demo.py [id]             # demo AI di terminal
    python -m unittest discover -s tests -t . -v

## Cara bermain
Klik sel di papan RADAR (kanan) untuk menembak; AI membalas menembak papan Anda (kiri).
Lingkaran jingga = KENA, cincin putih = MELESET. Kapal lawan terlihat saat tenggelam.
Tiga sumber armada Anda: acak, manual (contoh), dan dataset CSV (layar "Susun Armada").

## Kontrol
Klik = tembak | H saran AI + alasan | A AI menembak untuk Anda | T auto-play | M heatmap probabilitas |
I AI Analysis | D ganti SIANG/MALAM | R ulang | Esc menu

## Struktur
- core/ : state (koordinat), actions (Shot), board, fleet_loader (acak/manual/CSV + validasi), random_ai, bayes_ai,
          explain (penjelasan langkah AI), ai_service (solve, validasi, evaluasi)
- ui/   : layout (posisi papan), session (logika Human vs AI tanpa pygame), gfx + sprites (gambar), app (menu, setup, game, overlay)
- data/ : layouts.csv (100 susunan), custom_layouts.csv (dibuat otomatis)
- tests/: unit test dan smoke test (pygame tiruan)
