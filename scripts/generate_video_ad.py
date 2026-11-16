"""
burn_ad_overlay.py
------------------
Ia descrierile audio generate (stage2) si le pune peste clipuri, ca voce,
cu  . Scoate CATE UN VIDEO PER CLIP.

Flux:
  1. citeste descrierile (CSV stage2) si adnotarile (ca sa stie din ce clip e fiecare)
  2. grupeaza descrierile PE CLIP
  3. pentru fiecare clip: sintetizeaza vocea, o plaseaza fara suprapuneri,
     o mixeaza peste sunetul original si arde subtitrarile
  4. salveaza un .mp4 per clip in output_dir

Necesita: edge-tts (pip install edge-tts), ffmpeg in PATH.
"""
import os, asyncio, argparse, tempfile, subprocess
import pandas as pd

# ---- cai implicite (se pot schimba cu argumente) ----
BASE = r"D:\Master\dizertatie\Dizertatie"
CSV   = os.path.join(BASE, r"outputs\cmdad_ads\stage2_gemeni_single.csv")
ANNO  = os.path.join(BASE, r"shot-by-shot\resources\annotations\cmdad_small_2018_downloaded.csv")
VIDEOS = os.path.join(BASE, r"data\videos")
OUTDIR = os.path.join(BASE, r"outputs\ad_videos")

VOICE = "en-US-AriaNeural"   # vocea naratorului
MIN_GAP = 0.40               # pauza minima intre doua descrieri (secunde)
AD_VOLUME = 1.4              # cat de tare e vocea fata de sunetul original

SUB_STYLE = ("FontName=Arial,FontSize=16,PrimaryColour=&H00FFFFFF,"
             "OutlineColour=&H00000000,Bold=1,Outline=2,Shadow=1,Alignment=2,MarginV=30")


def srt_time(s):
    s = max(0.0, s)
    h, m, sec = int(s // 3600), int((s % 3600) // 60), int(s % 60)
    ms = int(round((s - int(s)) * 1000))
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"


def tts(text, out_mp3, voice):
    import edge_tts
    asyncio.run(edge_tts.Communicate(text, voice).save(out_mp3))


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def process_clip(clip_name, group, video_path, out_dir, voice):
    """Genereaza un video cu descriere audio pentru un singur clip."""
    group = group.sort_values("start").reset_index(drop=True)
    safe_name = clip_name.replace("/", "_")

    with tempfile.TemporaryDirectory() as tmp:
        ad_clips = []   # (wav, start_sec)
        srt_rows = []   # (start, end, text)
        last_end = 0.0

        for i, row in group.iterrows():
            text = str(row["text_gen"]).strip()
            if not text or text.lower() == "nan":
                continue

            mp3 = os.path.join(tmp, f"ad_{i}.mp3")
            wav = os.path.join(tmp, f"ad_{i}.wav")
            tts(text, mp3, voice)
            subprocess.run(["ffmpeg", "-y", "-i", mp3, "-ar", "44100", "-ac", "1", wav],
                           capture_output=True, text=True)
            dur = duration(wav)
            if dur <= 0:
                continue

            # porneste la momentul descrierii, dar nu peste descrierea precedenta
            start = max(float(row["start"]), last_end + MIN_GAP)
            end = start + dur
            ad_clips.append((wav, start))
            srt_rows.append((start, end, text))
            last_end = end
            print(f"    [{start:6.2f}s] {text[:55]}")

        if not ad_clips:
            print(f"  [SKIP] nicio descriere valida pentru {clip_name}")
            return

        # subtitrari
        srt = os.path.join(out_dir, f"{safe_name}_ad.srt")
        with open(srt, "w", encoding="utf-8") as f:
            for n, (s, e, t) in enumerate(srt_rows, 1):
                f.write(f"{n}\n{srt_time(s)} --> {srt_time(e)}\n{t}\n\n")

        # mix: sunet original + fiecare voce intarziata la momentul ei
        orig = os.path.join(tmp, "orig.wav")
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-ar", "44100", "-ac", "2", orig],
                       capture_output=True, text=True)
        inputs = ["-i", orig]
        for wav, _ in ad_clips:
            inputs += ["-i", wav]
        parts = []
        for idx, (_, start) in enumerate(ad_clips):
            ms = int(start * 1000)
            parts.append(f"[{idx+1}]adelay={ms}|{ms},volume={AD_VOLUME}[ad{idx}]")
        mix = "[0]" + "".join(f"[ad{idx}]" for idx in range(len(ad_clips)))
        parts.append(f"{mix}amix=inputs={len(ad_clips)+1}:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.95[out]")
        mixed = os.path.join(tmp, "mixed.wav")
        r = subprocess.run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(parts),
                            "-map", "[out]", mixed], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  [EROARE mix]:\n{r.stderr[-500:]}")
            return

        # video original + audio mixat + subtitrari arse
        srt_esc = srt.replace("\\", "/").replace(":", "\\:")
        out = os.path.join(out_dir, f"{safe_name}_ad.mp4")
        r = subprocess.run(["ffmpeg", "-y", "-i", video_path, "-i", mixed,
                            "-vf", f"subtitles='{srt_esc}':force_style='{SUB_STYLE}'",
                            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "23",
                            "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k", out],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  [EROARE combine]:\n{r.stderr[-500:]}")
        else:
            print(f"  [OK] {os.path.basename(out)}  ({len(ad_clips)} descrieri)")


def main(a):
    os.makedirs(a.out, exist_ok=True)
    df = pd.read_csv(a.csv)
    anno = pd.read_csv(a.anno)

    # leaga fiecare descriere de clipul ei (cmd_filename), dupa anno_idx
    clip_of = dict(zip(anno["anno_idx"], anno["cmd_filename"]))
    df["clip"] = df["anno_idx"].map(clip_of)
    if df["clip"].isna().any():
        print(f"[ATENTIE] {df['clip'].isna().sum()} descrieri fara clip (anno_idx negasit)")
        df = df.dropna(subset=["clip"])

    print(f"{len(df)} descrieri in {df['clip'].nunique()} clipuri\n")

    for clip_name, group in df.groupby("clip"):
        video = os.path.join(a.videos, clip_name.replace("/", os.sep) + ".mkv")
        if not os.path.isfile(video):
            print(f"[SKIP] video negasit: {video}")
            continue
        print(f"[{clip_name}]  ({len(group)} descrieri)")
        process_clip(clip_name, group, video, a.out, a.voice)

    print("\n=== gata ===")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=CSV)
    p.add_argument("--anno", default=ANNO)
    p.add_argument("--videos", default=VIDEOS)
    p.add_argument("--out", default=OUTDIR)
    p.add_argument("--voice", default=VOICE)
    main(p.parse_args())
