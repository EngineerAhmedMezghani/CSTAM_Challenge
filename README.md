# OliveSoft Tender Scraper

MVP de la première brique CSTAM-OliveSoft : une URL publique est téléchargée, les appels d'offres visibles sont normalisés, stockés dans PostgreSQL puis affichés dans React.

Documentation détaillée : [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md)

## Lancement Docker

Prérequis : Docker Desktop avec Compose.

```bash
docker compose -f docker/docker-compose.yml up --build
```

URLs :

- Frontend : http://localhost:5173
- API : http://localhost:8000
- Swagger : http://localhost:8000/docs
- Health : http://localhost:8000/health

Les identifiants de développement sont configurés par défaut à `olivesoft/olivesoft`. Pour les modifier, créez `.env` depuis `.env.example` avant le lancement. Les données PostgreSQL sont conservées dans le volume `postgres_data`.

## Lancement local

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/Activate.ps1
pip install -r backend/requirements.txt
$env:PYTHONPATH = "backend"
$env:DATABASE_URL = "postgresql+psycopg://olivesoft:olivesoft@localhost:5432/olivesoft"
uvicorn app.main:app --app-dir backend --reload
```

Dans un autre terminal :

```bash
cd frontend
npm install
npm run dev
```

## API

`POST /api/scrape`

```json
{"url": "https://www.marchespublics.gov.tn", "max_depth": 3, "max_pages": 50}
```

Retourne un `job_id`. Le frontend interroge ensuite `GET /api/scrape/{job_id}` jusqu'à `done` ou `failed`, puis appelle `GET /api/tenders?job_id={job_id}`. Le job expose aussi l'étape et la progression du crawler; `max_depth` et `max_pages` bornent l'exploration.

## Architecture

```text
React -> FastAPI -> BackgroundTasks -> ScraperRouter -> Scraper -> TenderData -> PostgreSQL
```

`GenericExtractor` utilise httpx et BeautifulSoup. `MarchesPublicsTnScraper` découvre depuis une URL racine la liste `/appels-doffres`, suit les fiches `/appels-doffres/Tender-*` du même domaine et réutilise l'extraction générique pour normaliser leurs détails. Les pages dynamiques peuvent nécessiter Playwright. Un nouvel adapter implémente `BaseScraper`, retourne `TenderData`, puis est ajouté dans `scrapers/router.py`.

Les doublons sont détectés avec un SHA-256 calculé sur URL source, titre, description et dates normalisées. Un tender déjà connu est mis à jour et réassocié au dernier job, sans créer de nouvelle ligne ; le titre seul n'est jamais une clé d'unicité.

## Tests

```powershell
$env:PYTHONPATH = "backend"
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
```

Les tests d'extraction utilisent `backend/tests/fixtures/tenders.html` et ne dépendent pas d'Internet. Le test d'intégration PostgreSQL nécessite le service Docker.

## Limites et roadmap

Le MVP ne gère pas encore l'authentification, le RAG, les LLM, le scoring, la recherche sémantique ou la génération de propositions. Ces fonctions pourront consommer les tenders normalisés via PostgreSQL et n8n. Le workflow préparatoire se trouve dans `n8n/workflows/scrape_trigger.json`.
