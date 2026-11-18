# D.O.R.A. – założenia projektu

Dokument opisuje, co budujemy, dla kogo, z czego i w jakiej kolejności. Jest punktem odniesienia dla wszystkich etapów: gdy kod lub schemat różni się od tego dokumentu, jedno z nich trzeba poprawić.

## 1. Cel

DORA (Developer's Own Repository Assistant) to interaktywny asystent AI z wizualnym awatarem, który zna portfolio projektów programistycznych autora. Potrafi:

- odpowiadać na pytania o budowę i działanie projektów;
- wskazać, czy dane rozwiązanie lub technologia było już użyte, i w którym projekcie;
- podać źródło odpowiedzi (projekt, plik), a gdy czegoś nie wie – powiedzieć to wprost.

Inspiracją jest Charlie, lokalny asystent AI prezentowany przez Wydział Informatyki Politechniki Opolskiej: awatar na ekranie, sztuczna inteligencja uruchamiana na własnym sprzęcie, bez usług chmurowych.

## 2. Użytkownicy i kontekst użycia

- **Kto:** prowadzący zajęcia, osoby oglądające portfolio (np. rekruterzy), sam autor szukający, gdzie już coś zrobił.
- **Gdzie:** laptop leżący normalnie na biurku lub stole prezentacyjnym, ekran poziomy 16:9 (projektowo 1920×1080, ze skalowaniem do mniejszych rozdzielczości).
- **Jak:** użytkownik siedzi lub stoi na wprost laptopa, ok. 0,5–1 m od kamery wbudowanej nad ekranem. Rozmawia głosem; klawiatura i mysz są tylko zapasem.

## 3. Założenia

| Obszar | Założenie |
|---|---|
| Lokalność | Wszystko działa na laptopie. Żadne dane nie trafiają do chmury. |
| Prywatność | Obraz z kamery jest analizowany tylko w przeglądarce, niczego nie zapisujemy. To wykrywanie obecności twarzy, nie rozpoznawanie tożsamości. |
| Bez użycia rąk | Wykrycie twarzy uruchamia powitanie, mikrofon włącza się sam, koniec wypowiedzi wykrywa VAD. Przycisk i pole tekstowe są tylko zapasem. |
| Układ ekranu | Wyłącznie poziomy. Brak wariantu pionowego. |
| Język | Interfejs, rozmowa i dokumentacja po polsku. Kod i komunikaty commitów po angielsku. |
| Sprzęt | RTX 2060 (6 GB VRAM), 32 GB RAM, Ryzen 7 4800H. Model językowy na karcie graficznej, mowa (STT/TTS) na procesorze. |
| Kolejność prac | Najpierw w pełni działający interfejs z podstawionymi usługami (mock), potem wymiana usług na prawdziwe bez zmian w interfejsie. |

## 4. Zachowanie awatara

### Stany rozmowy

| Stan | Co się dzieje | Pasek stanu | Awatar |
|---|---|---|---|
| Bezczynność | Nikogo nie ma przed ekranem. Kamera działa. | „Czekam na rozmowę” | oddycha, mruga, rozgląda się |
| Powitanie | Twarz wykryta. DORA sama wita się i podpowiada pytania. | „Zapraszam do rozmowy” | macha, uśmiech |
| Słuchanie | Mikrofon aktywny, VAD czeka na koniec wypowiedzi. | „Słucham…” | zwrócona do użytkownika, wskaźnik poziomu głosu |
| Przetwarzanie | Rozpoznanie mowy → wyszukiwanie → generowanie. | „Rozpoznaję mowę…”, „Szukam w projektach…”, „Myślę…” | zamyślona |
| Mówienie | Odpowiedź głosem, napisy, źródła. Mikrofon wyciszony. | „Mówię…” | ruch ust zgodny z głośnością dźwięku |
| Pożegnanie | Koniec rozmowy, czyszczenie historii. | „Do zobaczenia” | macha |
| Błąd / tryb zapasowy | Brak urządzenia lub usługi. | komunikat o problemie | zmartwiona |

Szczegółowe przebiegi pokazują [schematy interakcji](schematy-interakcji/opis-interakcji.md).

### Reguły i parametry czasowe

Te wartości są jedynym źródłem prawdy dla automatu stanów (Etap 1) i schematów.

| Reguła | Wartość |
|---|---|
| Wykrycie użytkownika | twarz widoczna nieprzerwanie ≥ 1 s i wystarczająco duża w kadrze (próg do kalibracji dla odległości 0,5–1 m) |
| Odejście użytkownika | twarz niewidoczna > 5 s → koniec rozmowy |
| Cisza | brak mowy > 15 s po powitaniu lub po odpowiedzi → pożegnanie. Cisza **nie** jest liczona jako nieudana próba. |
| Niezrozumiała mowa | VAD wykrył mowę, ale transkrypcja jest pusta lub niepewna → prośba o powtórzenie. Po 3 **kolejnych** nieudanych próbach → pożegnanie. Licznik zerowany po poprawnej transkrypcji i na początku każdej rozmowy. |
| Echo | mikrofon wyciszony, gdy DORA mówi |
| Przerwanie rozmowy | słowo „koniec” w czasie słuchania; przycisk „Zakończ” lub Esc w dowolnej chwili; odejście. W trakcie odpowiedzi DORY działa tylko przycisk, Esc lub odejście, bo mikrofon jest wtedy wyciszony. |
| Ponowne powitanie | po pożegnaniu przez 30 s bez automatycznego powitania; przycisk „Rozpocznij rozmowę” działa od razu |
| Limit odpowiedzi | brak odpowiedzi w 30 s → anulowanie zapytania, wpis w logu, przeprosiny, powrót do słuchania (bez automatycznego ponawiania) |
| Utrata połączenia z backendem | ponowne łączenie co 5 s, maks. 3 próby → ekran „DORA jest chwilowo niedostępna”, sprawdzanie co 30 s |
| Brak syntezy mowy | odpowiedź tylko jako tekst z informacją „Brak dźwięku” |

## 5. Układ ekranu

Ekran poziomy, podzielony na dwie części:

- **lewa (ok. 45% szerokości):** awatar na całą wysokość – przyciąga wzrok i pokazuje stan;
- **prawa:** panel rozmowy – rozpoznane pytanie, odpowiedź jako napisy, pod nią źródła (projekt, plik);
- **góra:** wąski pasek stanu, wskaźnik kamery i mikrofonu, ustawienia;
- **dół prawej części:** podpowiedzi pytań, zapasowy przycisk mikrofonu i pole tekstowe.

## 6. Architektura

```
 Przeglądarka (frontend)                      Laptop (backend, localhost)
┌──────────────────────────────┐  WebSocket  ┌───────────────────────────────┐
│ kamera   → MediaPipe (twarz) │◄───────────►│ FastAPI                       │
│ mikrofon → VAD → nagranie    │             │  ├─ faster-whisper (STT)      │
│ automat stanów (XState)      │             │  ├─ RAG: LanceDB + bge-m3     │
│ awatar SVG, napisy, źródła   │             │  ├─ Ollama, model ok. 4B      │
│ odtwarzanie mowy, ruch ust   │             │  └─ Piper (TTS)               │
└──────────────────────────────┘             └───────────────────────────────┘
                                                          ▲
                                           lokalne foldery z repozytoriami
```

| Warstwa | Technologia | Uzasadnienie |
|---|---|---|
| Frontend | React + TypeScript + Vite | szybki start, typowanie, popularny ekosystem |
| Logika interakcji | XState | automat stanów odwzorowuje schemat blokowy 1:1 i daje się testować |
| Awatar | SVG + animacje CSS/JS, Web Audio | pełna kontrola nad stanami, ruch ust z głośności dźwięku, brak zewnętrznych zasobów |
| Detekcja twarzy | MediaPipe Face Detector | działa w przeglądarce, model serwowany lokalnie |
| Backend | Python 3.12 + FastAPI + WebSocket | biblioteki AI są w Pythonie; strumieniowanie stanów i tekstu |
| Model językowy | Ollama, model ok. 4B | mieści się w 6 GB VRAM; kandydaci: Bielik 4.5B, Qwen 4B, Gemma 4B – wybór po teście na pytaniach o projekty |
| Embeddingi | bge-m3 | wielojęzyczny, dobrze radzi sobie z polskim |
| Baza wektorowa | LanceDB | wbudowana, bez osobnego serwera |
| Rozpoznawanie mowy | faster-whisper (CPU) | lokalnie, obsługuje polski |
| Synteza mowy | Piper, polski głos (CPU) | lokalnie, szybka |
| Testy | Vitest, pytest | |

**Python 3.12, nie 3.15:** systemowy Python 3.15 jest za nowy dla części bibliotek ML. Backend dostaje własną wersję przez `uv`.

**Rozpoznawanie mowy w Etapie 1:** zanim powstanie backend, interfejs może korzystać z wbudowanego rozpoznawania mowy w Chrome. Wysyła ono nagranie na serwery Google, więc służy wyłącznie do testów i znika w Etapie 5.

### Wstępny kontrakt frontend ↔ backend

Doprecyzowany w Etapie 1. Podstawiony asystent (mock) w Etapie 1 i prawdziwy serwer w Etapie 2 spełniają ten sam kontrakt.

| Kierunek | Komunikat | Treść |
|---|---|---|
| → backend | `question` | tekst pytania lub nagranie audio, identyfikator rozmowy |
| → backend | `cancel` | przerwanie bieżącej odpowiedzi |
| ← frontend | `status` | etap przetwarzania: rozpoznawanie, wyszukiwanie, generowanie |
| ← frontend | `transcript` | rozpoznany tekst pytania wraz z oceną pewności |
| ← frontend | `answer_delta` | kolejny fragment tekstu odpowiedzi |
| ← frontend | `answer_done` | pełna odpowiedź, lista źródeł (projekt, plik), audio |
| ← frontend | `error` | rodzaj błędu i komunikat dla użytkownika |

## 7. Baza wiedzy (RAG)

- Indeksowane są wskazane lokalne foldery z repozytoriami: README, dokumentacja, kod, pliki manifestów (`package.json`, `requirements.txt`, `pyproject.toml`, `*.csproj` itp.) i historia gita. Pliki z `.gitignore` są pomijane.
- Dla każdego projektu powstaje **karta projektu**: opis, cel, lista technologii wyciągnięta z manifestów.
- Pytania typu „czy używałem już X i gdzie?” obsługuje osobny indeks technologia → projekty. Samo wyszukiwanie wektorowe jest przy takich pytaniach zawodne.
- Odpowiedź zawsze zawiera źródła. Bez pasujących źródeł DORA mówi, że nie wie, zamiast zmyślać.
- Częste pytania mogą mieć gotowe odpowiedzi w pamięci podręcznej (cache), żeby DORA odpowiadała od razu.

## 8. Powiązanie z zajęciami

### Pięć wymiarów projektowania interakcji

| Wymiar | Realizacja w DORZE |
|---|---|
| Słowa | krótkie polskie komunikaty na pasku stanu, naturalne powitania (kilka losowanych wariantów), jasne komunikaty błędów z podpowiedzią, co zrobić |
| Reprezentacje wizualne | awatar z animacją dla każdego stanu, stałe kolory stanów, napisy i źródła, czytelna typografia |
| Obiekty fizyczne i przestrzeń | laptop na biurku, kamera nad ekranem, mikrofon, odległość 0,5–1 m, układ poziomy |
| Czas | animacje bezczynności i mówienia, informacja o postępie przetwarzania, limity czasu z punktu 4 |
| Zachowanie | automat stanów, samodzielne rozpoczęcie rozmowy, informacja zwrotna na każdym kroku, łagodna degradacja przy awariach |

### Zasady Gestalt w układzie ekranu

- **Bliskość i region:** pytanie, odpowiedź i jej źródła tworzą jedną grupę w panelu rozmowy.
- **Podobieństwo:** jeden styl przycisków akcji, jeden kolor na stan „słucham”.
- **Figura i tło:** awatar i aktywny element wyraźnie oddzielone od tła.
- **Wspólny los:** napisy pojawiają się w rytmie mowy, elementy jednego stanu animują się razem.
- **Zamknięcie i ciągłość:** wskaźnik postępu przetwarzania.

Szczegółowy opis zastosowania zasad powstanie w Etapie 6.

## 9. Plan etapów

| Etap | Zakres | Znacznik |
|---|---|---|
| 0 | Struktura repozytorium, README, założenia, schematy interakcji | – |
| 1 | Interfejs z podstawionymi usługami | `v0.1-interface` |
| 2 | Szkielet backendu, WebSocket, podmiana mocka | `v0.2` |
| 3 | Lokalny model w Ollamie, strumieniowanie odpowiedzi | `v0.3` |
| 4 | Indeksowanie repozytoriów, karty projektów, wyszukiwanie, źródła | `v0.4` |
| 5 | Lokalny głos: Whisper + Piper | `v0.5` |
| 6 | Tryb kiosku, cache, testy z użytkownikami, dokumentacja końcowa | `v1.0` |

### Etap 1 – interfejs (każdy krok kończy się commitem)

1. Szkielet Vite + React + TypeScript, linter, formatowanie, testy.
2. Tokeny wyglądu (kolory, typografia, odstępy) i układ ekranu z punktu 5.
3. Automat stanów z reguł z punktu 4, z testami.
4. Awatar SVG z animacjami dla każdego stanu.
5. Panel rozmowy: napisy, źródła, podpowiedzi, pole tekstowe; podstawiony asystent ze strumieniowaną odpowiedzią.
6. Głos: mikrofon z VAD i wskaźnikiem poziomu, odtwarzanie odpowiedzi, ruch ust.
7. Detekcja twarzy uruchamiająca powitanie i pożegnanie (rozmowa bez użycia rąk).
8. Ustawienia (kamera, mikrofon, głośność, napisy), stany błędów, dostępność (klawiatura, kontrast, ograniczenie animacji).

### Praca z gitem

- Commity i wypychanie na GitHub wykonuje ręcznie autor projektu.
- Commit po każdym zamkniętym kroku, w formacie Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`, `style:`).
- Znacznik (tag) na koniec każdego etapu.

## 10. Kwestie otwarte

| Kwestia | Potrzebna przed |
|---|---|
| Wygląd postaci awatara (oryginalna postać, np. sowa-archiwistka lub stylizowany robot) | Etap 1, krok 4 |
| Wybór modelu językowego po teście kandydatów | Etap 3 |
| Lista folderów z projektami do zaindeksowania | Etap 4 |
| Wymagania zaliczeniowe: termin, forma sprawozdania, obowiązkowe elementy | Etap 6 |

## 11. Dziennik decyzji

| Data | Decyzja |
|---|---|
| 2026-11-12 | Model językowy lokalnie (Ollama), bez chmury. |
| 2026-11-12 | Rozmowa głosowa z tekstem jako kanałem zapasowym. |
| 2026-11-12 | Awatar 2D rysowany w kodzie (SVG). |
| 2026-11-12 | Wiedza z lokalnych folderów z repozytoriami. |
| 2026-11-12 | Rozmowa bez użycia rąk: wykrycie twarzy rozpoczyna rozmowę. |
| 2026-11-12 | Układ ekranu wyłącznie poziomy (laptop leży normalnie). |
| 2026-11-18 | Commity i wypychanie na GitHub wykonuje ręcznie autor projektu. |
