# Frontend DORY

Aplikacja w przeglądarce, uruchamiana na pełnym ekranie laptopa (układ poziomy 16:9).

Odpowiada za:

- awatar 2D (SVG) i jego animacje dla każdego stanu rozmowy;
- automat stanów interakcji (XState) – odwzorowanie schematów z `docs/schematy-interakcji`;
- detekcję twarzy z kamery (MediaPipe, obraz przetwarzany tylko lokalnie);
- nagrywanie mowy z wykrywaniem jej końca (VAD) i odtwarzanie odpowiedzi;
- napisy, źródła odpowiedzi, pasek stanu i tryb zapasowy (przycisk + pole tekstowe).

Kod powstaje w Etapie 1. Do czasu powstania backendu (Etap 2) asystent jest tu podstawiony (mock) za tym samym interfejsem, którego później użyje prawdziwy serwer.
