# D.O.R.A. – Developer's Own Repository Assistant

Lokalny asystent AI z awatarem 2D, który zna portfolio projektów programistycznych autora. Odpowiada na pytania o budowę i działanie projektów oraz wskazuje, czy i w którym projekcie użyto danej technologii lub rozwiązania.

DORA działa w całości na laptopie, bez usług chmurowych. Sama zauważa użytkownika przed kamerą, wita się i zaczyna rozmowę głosową – nie trzeba niczego naciskać.

Projekt na zajęcia **Interfejsy człowiek–maszyna** (semestr VII).

## Status

| Etap | Zakres | Stan |
|---|---|---|
| 0 | Struktura repozytorium, założenia, schematy interakcji | ✅ |
| 1 | Interfejs: awatar, automat stanów, głos, detekcja twarzy (usługi podstawione) | ⏳ |
| 2 | Backend: FastAPI + WebSocket | – |
| 3 | Lokalny model językowy (Ollama) | – |
| 4 | Baza wiedzy o projektach (RAG) | – |
| 5 | Lokalny głos: Whisper (STT) + Piper (TTS) | – |
| 6 | Tryb kiosku, testy z użytkownikami, dokumentacja końcowa | – |

## Struktura

```
frontend/   aplikacja w przeglądarce: interfejs, awatar, mikrofon, kamera
backend/    serwer: wyszukiwanie w projektach, model językowy, mowa
docs/       założenia projektu i schematy interakcji
```

## Technologie

- **Frontend:** React + TypeScript + Vite, XState (automat stanów), awatar SVG, MediaPipe Face Detector
- **Backend:** Python + FastAPI + WebSocket
- **AI lokalnie:** Ollama (model ok. 4B), bge-m3 (embeddingi), LanceDB, faster-whisper, Piper

## Wymagania

- Node.js 22 lub nowszy
- Python 3.12 (instalowany przez `uv` w Etapie 2)
- Ollama
- Kamera i mikrofon (bez nich DORA działa w trybie tekstowym)

Instrukcja uruchomienia pojawi się wraz z Etapem 1.

## Dokumentacja

- [Założenia projektu](docs/zalozenia-projektu.md) – cele, zachowanie awatara, architektura, plan etapów
- [Schematy interakcji](docs/schematy-interakcji/opis-interakcji.md) – schemat ogólny i cztery warianty przebiegu
