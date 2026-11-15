# 00 — Setup proiect dizertație

## Context
Reproducere a metodei Shot-by-Shot (ICCV 2025) pentru generarea 
automată de descrieri audio pentru nevăzători.

## Setup inițial
- Repo clonat de la: https://github.com/Jyxarthur/Shot-by-Shot
- Repo clonat de la: https://github.com/m-bain/CondensedMovies
- Sistem: Windows 11, GPU Nvidia RTX 3050 Laptop (4 GB VRAM)
- Python: [versiunea ta, verifici cu `python --version`]

## Decizii amanate
- Modele: Gemini API vs modele locale (Qwen2-VL + LLaMA3) — se decidel
  dupa primele teste
- Seturi de date: deocamdata doar CMD-AD; TV-AD si MAD-Eval pastrate 
  ca optiune

## Structura folderelor
Dizertatie/
├── CondensedMovies/   (date si scripturi pentru descarcare YouTube)
├── shot-by-shot/      (metoda si cod)
├── data/videos/       (videoclipurile descarcate, nu in Git)
├── outputs/           (rezultate rulari, nu in Git)
└── docs/              (documentatie proces)

## Subset de test ales
10 clipuri din filme din 2012, selectate prin scriptul:
shot-by-shot/stage1/make_cmdad_small_2012.py

Lista ID-urilor: CondensedMovies/data_prep/2012_cmdad.csv