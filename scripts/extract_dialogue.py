"""
extract_dialogue.py  (faster-whisper)
-------------------------------------
Transcrie dialogul din fiecare clip cu faster-whisper (Whisper).
Pentru fiecare clip salveaza momentele si textul replicilor in JSON.

- model 'small' multilingv: pastreaza fiecare limba asa cum e (nu traduce)
- word_timestamps: timpii fiecarei replici vin de la cuvinte, nu de la segment
- garda: un segment anormal de lung (fara timpi pe cuvinte) e limitat la o
  fereastra rezonabila, ca sa nu "inghita" pauzele lungi

Necesita: faster-whisper, ffmpeg in PATH. Implicit pe CPU.
"""
import os, json, glob, argparse

BASE = r"D:\Master\dizertatie\Dizertatie"
VIDEOS = os.path.join(BASE, r"data\videos")
OUTDIR = os.path.join(BASE, r"outputs\dialogue")

MAX_SEG = 15.0   # peste atatea secunde, un segment e considerat anormal
CLAMP = 5.0      # il limitam la o fereastra de atatea secunde, terminata la 'end'


def load_model(name, device):
    from faster_whisper import WhisperModel
    if device == "cuda":
        return WhisperModel(name, device="cuda", compute_type="float16")
    m = WhisperModel(name, device="cpu", compute_type="int8")
    print(f"Model '{name}' pe CPU (int8)")
    return m


def transcribe(model, video_path, task):
    segments, info = model.transcribe(video_path, task=task, word_timestamps=True,
                                      vad_filter=True,
                                      vad_parameters=dict(onset=0.3, offset=0.2, speech_pad_ms=400))
    segs = []
    for s in segments:
        if s.words:
            start = s.words[0].start
            end = s.words[-1].end
        else:
            start, end = s.start, s.end
        if end - start > MAX_SEG:
            start = max(end - CLAMP, 0.0)
        segs.append({"start": round(start, 2), "end": round(end, 2), "text": s.text.strip()})
    return segs, info.language


def main(a):
    os.makedirs(a.out, exist_ok=True)
    videos = sorted(glob.glob(os.path.join(a.videos, "**", "*.mkv"), recursive=True))
    if not videos:
        print(f"Niciun .mkv gasit in {a.videos}")
        return
    print(f"{len(videos)} clipuri de transcris\n")

    model = load_model(a.model, a.device)

    for vid in videos:
        name = os.path.splitext(os.path.relpath(vid, a.videos).replace(os.sep, "_"))[0]
        print(f"[{name}] transcriu...")
        segs, lang = transcribe(model, vid, a.task)
        out = {
            "clip": name,
            "video": vid,
            "language": lang,
            "num_segments": len(segs),
            "segments": segs,
            "full_text": " ".join(s["text"] for s in segs),
        }
        with open(os.path.join(a.out, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"  {len(segs)} replici ({lang}) -> {name}.json")

    print("\n=== gata ===")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--videos", default=VIDEOS)
    p.add_argument("--out", default=OUTDIR)
    p.add_argument("--model", default="small", help="base / small / medium (multilingv)")
    p.add_argument("--device", default="cpu", help="cpu / cuda")
    p.add_argument("--task", default="transcribe", help="transcribe / translate")
    main(p.parse_args())
