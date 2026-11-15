"""
filter-annotations.py
---------------------
Pastreaza din adnotarile CMD-AD doar randurile pentru clipurile 
descarcate efectiv in data/videos/2018/.

Input:  adnotarile complete cu fete + film grammar
Output: CSV mic (filtrat) pentru Shot-by-Shot
"""

import pandas as pd
import os

# ----- CONFIGURARE -----
GT_TEXT = r"..\shot-by-shot\action_score\gt_actions\cmdad_gt_action.csv"
ANNO_FULL = r"..\shot-by-shot\resources\annotations\cmdad_anno_context-3.0-8.0_face-0.2-0.4_scale_thread.csv"
VIDEOS_DIR = r"..\data\videos\2018"
OUT_ANNO = r"..\shot-by-shot\resources\annotations\cmdad_small_2018_downloaded.csv"
YEAR = "2018"


def main():
    # 1. Lista videoclipurilor efectiv descarcate
    files = os.listdir(VIDEOS_DIR)
    # Pastram doar extensiile video (.mkv, .mp4), scoatem .part
    video_files = [f for f in files if f.endswith((".mkv", ".mp4")) and not f.endswith(".part")]
    downloaded_ids = [os.path.splitext(f)[0] for f in video_files]

    print(f"Videoclipuri descarcate: {len(downloaded_ids)}")
    for vid in downloaded_ids:
        print(f"  - {vid}")

    # Construim cmd_filename ca sa potrivim coloana din CSV
    target_cmds = {f"{YEAR}/{vid}" for vid in downloaded_ids}

    # 2. Citim adnotarile complete
    print(f"\nCitim: {ANNO_FULL}")
    df = pd.read_csv(ANNO_FULL)
    print(f"Total randuri: {len(df)}")

    # 3. Filtram doar randurile corespunzatoare
    df_filtered = df[df["cmd_filename"].isin(target_cmds)].copy()

    # 3b. Textul AD de referinta, din fisierul oficial al autorilor (folosit si la Action score)
    gt = pd.read_csv(GT_TEXT)[["anno_idx", "text_gt"]].rename(columns={"text_gt": "text"})
    df_filtered = df_filtered.merge(gt, on="anno_idx", how="left")
    print(f"Descrieri fara text de referinta: {df_filtered['text'].isna().sum()}")

    # 4. Salvam
    os.makedirs(os.path.dirname(OUT_ANNO), exist_ok=True)
    df_filtered.to_csv(OUT_ANNO, index=False)

    print(f"\n{'=' * 50}")
    print(f"Randuri in CSV filtrat: {len(df_filtered)}")
    print(f"Salvat: {OUT_ANNO}")


if __name__ == "__main__":
    main()