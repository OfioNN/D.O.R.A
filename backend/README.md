# Backend DORY

Lokalny serwer w Pythonie (FastAPI), z którym frontend rozmawia przez WebSocket.

Odpowiada za:

- indeksowanie wskazanych folderów z repozytoriami i indeks „technologia → projekty”;
- wyszukiwanie fragmentów pasujących do pytania (RAG);
- generowanie odpowiedzi ze źródłami przez lokalny model w Ollamie;
- zamianę mowy na tekst (faster-whisper) i tekstu na mowę (Piper).

Kod powstaje od Etapu 2. Wymaga Pythona 3.12 (instalowanego przez `uv`), bo systemowy Python 3.15 jest za nowy dla części bibliotek ML.
