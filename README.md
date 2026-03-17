# Webové kalkulačky

Flask aplikace s praktickými kalkulačkami pro finance, mzdy, bydlení a rodinné dávky v Česku.

Aktuálně obsahuje:
- složené úročení
- čistou mzdu v ČR
- hypotéku
- mateřskou
- rodičovskou
- nemocenskou

## Lokální spuštění

Požadavky:
- Python 3.12+

Instalace závislostí:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Spuštění aplikace:

```bash
python3 app.py
```

Aplikace poběží na adrese [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Testy

Rychlá kontrola syntaxe:

```bash
python3 -m py_compile app.py calculators/*.py tests/*.py
```

Spuštění všech testů:

```bash
python3 -m unittest discover -s tests -v
```

## Struktura projektu

- `app.py` obsahuje Flask aplikaci, routy a error handlery
- `calculators/` drží výpočtovou a validační logiku
- `templates/` obsahuje HTML šablony
- `static/` obsahuje CSS, JavaScript a favicon
- `tests/` obsahuje unit testy a smoke testy

## Nasazení na Render

Projekt je připravený pro jednoduché nasazení jako Flask web service.

V repozitáři je i soubor `render.yaml`, takže Render umí základní konfiguraci načíst automaticky.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn app:app
```

Postup:
1. Nahraj projekt do GitHub repozitáře.
2. V Renderu vytvoř novou `Web Service`.
3. Propoj repozitář.
4. Pokud Render nabídne použití `render.yaml`, potvrď to.
5. Po prvním deployi otevři `/health` a zkontroluj, že vrací `{"status":"ok"}`.
6. Potom otevři hlavní stránku webu a zkus alespoň jednu kalkulačku.

## Google Analytics 4

Google Analytics se načte automaticky, pokud nastavíš proměnnou prostředí `GOOGLE_ANALYTICS_ID`.

Postup:
1. V Google Analytics 4 vytvoř webový datový stream.
2. Zkopíruj své měřicí ID ve tvaru `G-XXXXXXXXXX`.
3. Na Renderu otevři službu `webove-kalkulacky`.
4. Jdi do `Environment`.
5. Přidej proměnnou `GOOGLE_ANALYTICS_ID` s hodnotou svého měřicího ID.
6. Ulož změnu a spusť redeploy.

## Důležitá poznámka

Výsledky kalkulaček jsou orientační. U mezd, dávek a dalších právně citlivých oblastí vždy záleží na konkrétní situaci a aktuálně platných pravidlech.
