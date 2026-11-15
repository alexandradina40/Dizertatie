"""
make_subset.py
--------------
Extrage lista de 14 ID-uri YouTube din splitul 2018 al CMD-AD,
pentru descarcare prin CondensedMovies/download.py.

Anul = cand a fost incarcat clipul pe YouTube (nu anul lansarii filmului).
"""

import pandas as pd
import os

# ----- CONFIGURARE -----

ANNO_PATH = r"..\shot-by_shot\resources\annotations\cmdad_anno.csv"
OUT_IDS = r"..\CondensedMovies\data_prep\2018_cmdad.csv"

MAX_UNIQUE_VIDEOS = 14
TARGET_YEAR = "2018"


def main():
    print(f"Citim: {ANNO_PATH}")
    df = pd.read_csv(ANNO_PATH)
    print(f"Total descrieri: {len(df)}")

    df_year = df[df["cmd_filename"].astype(str).str.startswith(f"{TARGET_YEAR}/")]
    print(f"Descrieri din {TARGET_YEAR}: {len(df_year)}")

    unique_cmds = df_year["cmd_filename"].drop_duplicates().head(MAX_UNIQUE_VIDEOS).tolist()

    os.makedirs(os.path.dirname(OUT_IDS), exist_ok=True)
    with open(OUT_IDS, "w", encoding="utf-8") as f:
        for cmd in unique_cmds:
            video_id = cmd.split("/")[1]
            f.write(video_id + "\n")

    print(f"\n{'=' * 50}")
    print(f"Salvate {len(unique_cmds)} ID-uri in: {OUT_IDS}")
    print(f"\nVideoclipuri selectate:")
    for cmd in unique_cmds:
        print(f"  - {cmd}")


if __name__ == "__main__":
    main()