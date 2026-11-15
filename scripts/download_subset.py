"""
download_subset.py
------------------
Descarca de pe YouTube cele 14 clipuri din subsetul 2018 CMD-AD,
folosind yt-dlp (versiunea moderna a youtube-dl).

Citeste lista de ID-uri din: CondensedMovies/data_prep/2018_cmdad.csv
Salveaza videoclipurile in: Dizertatie/data/videos/2018/
"""

import os
import subprocess

# ----- CONFIGURARE -----
IDS_FILE = r"..\CondensedMovies\data_prep\2018_cmdad.csv"
OUT_DIR = r"..\data\videos\2018"


def main():
    # Creeaza folderul daca nu exista
    os.makedirs(OUT_DIR, exist_ok=True)

    # Citeste lista de ID-uri
    with open(IDS_FILE, "r", encoding="utf-8") as f:
        video_ids = [line.strip() for line in f if line.strip()]

    print(f"Descarc {len(video_ids)} videoclipuri in: {OUT_DIR}\n")

    for i, vid in enumerate(video_ids, start=1):
        print(f"[{i}/{len(video_ids)}] {vid}")

        # Verificam daca exista deja
        existing = [f for f in os.listdir(OUT_DIR) if f.startswith(vid)]
        if existing:
            print(f"  Deja descarcat: {existing[0]}")
            continue

        url = f"https://www.youtube.com/watch?v={vid}"
        out_template = os.path.join(OUT_DIR, "%(id)s.%(ext)s")

        cmd = [
            "yt-dlp",
            "-f", "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/mp4",
            "--merge-output-format", "mkv",
            "--ignore-errors",
            "-o", out_template,
            url,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  OK")
        else:
            print(f"  ESUAT: {result.stderr[-200:]}")

    print("\n" + "=" * 50)
    print("DESCARCARE TERMINATA")

    # Raport final
    files = [f for f in os.listdir(OUT_DIR) if not f.endswith(".part")]
    print(f"Fisiere in {OUT_DIR}: {len(files)}")


if __name__ == "__main__":
    main()