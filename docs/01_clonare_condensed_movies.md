# 02 — Clonare CondensedMovies

## Scop
Avem nevoie de scriptul `download.py` care descarca videoclipurile de pe YouTube,
pe baza listei de ID-uri (`2012_cmdad.csv`).

## Comanda rulata
git clone https://github.com/m-bain/CondensedMovies.git

## Rezultat
Folderul `CondensedMovies/` creat in radacina proiectului, cu urmatoarea
structura (relevanta pentru noi):

- `data_prep/download.py` — scriptul de descarcare
- `data_prep/config.json` — configurare (unde salveaza, ce descarca)
- `data/metadata/clips.csv` — tabela cu toate clipurile (imdbid, videoid)

## Observatii
- Repo-ul contine si cod pentru antrenare (base/, utils/, parse_config.py)
  care nu ne intereseaza acum.
- Toate videoclipurile ocupa ~250 GB, dar vom descarca doar 10 clipuri de proba.