# Frontend DORY

Aplikacja w przeglądarce, uruchamiana na pełnym ekranie laptopa (układ poziomy 16:9).

Odpowiada za:

- awatar 2D (SVG) i jego animacje dla każdego stanu rozmowy;
- automat stanów interakcji (XState) – odwzorowanie schematów z `docs/schematy-interakcji`;
- detekcję twarzy z kamery (MediaPipe, obraz przetwarzany tylko lokalnie);
- nagrywanie mowy z wykrywaniem jej końca (VAD) i odtwarzanie odpowiedzi;
- napisy, źródła odpowiedzi, pasek stanu i tryb zapasowy (przycisk + pole tekstowe).

Do czasu powstania backendu (Etap 2) asystent jest tu podstawiony (mock) za tym samym interfejsem, którego później użyje prawdziwy serwer.

## Uruchomienie

Wymaga Node.js 22.12 lub nowszego. W folderze `frontend`:

```bash
npm install
npm run dev
```

Aplikacja działa pod adresem http://localhost:5173.

## Skrypty

| Polecenie            | Działanie                                                           |
| -------------------- | ------------------------------------------------------------------- |
| `npm run dev`        | serwer deweloperski z automatycznym odświeżaniem                    |
| `npm run build`      | sprawdzenie typów i wersja produkcyjna w `dist/`                    |
| `npm run preview`    | podgląd wersji produkcyjnej                                         |
| `npm run lint`       | analiza kodu (oxlint)                                               |
| `npm run format`     | formatowanie kodu (Prettier)                                        |
| `npm test`           | testy jednorazowo (Vitest)                                          |
| `npm run test:watch` | testy w trybie obserwacji zmian                                     |
| `npm run check`      | typy + lint + formatowanie + testy – do uruchomienia przed commitem |

## Technologie

React 19, TypeScript 7, Vite 8, Vitest 5 z Testing Library, oxlint, Prettier.
