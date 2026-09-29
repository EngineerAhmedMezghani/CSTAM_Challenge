# OliveSoft Tender Scraper - Guide du projet

## 1. Objectif

Cette application constitue la première brique du système CSTAM-OliveSoft :

```text
URL publique
    -> scraping HTTP ou navigateur
    -> extraction des appels d'offres
    -> normalisation
    -> déduplication
    -> PostgreSQL
    -> API FastAPI
    -> interface React
```

Le projet ne contient pas encore de logique RAG, LLM, scoring ou génération de propositions commerciales.

## 2. Entrée utilisateur

L'interface frontend demande l'URL du site à explorer. Le scraper tunisien découvre
automatiquement le lien `/appels-doffres` depuis la page fournie, puis suit les fiches
`/appels-doffres/Tender-*` et ignore les plans, résultats et actualités.

Exemple :

```text
https://www.marchespublics.gov.tn
```

L'API reçoit cette URL avec :

```http
POST /api/scrape
Content-Type: application/json
```

```json
{
  "url": "https://www.marchespublics.gov.tn",
  "max_depth": 3,
  "max_pages": 50
}
```

### Règles de validation

- `url` est obligatoire.
- Seuls les schémas `http://` et `https://` sont acceptés.
- Les schémas comme `file://`, `ftp://` ou autres sont rejetés.
- L'URL doit être valide selon Pydantic.

## 3. Sortie de `POST /api/scrape`

Le job est enregistré avant le scraping et l'API répond immédiatement :

```json
{
  "job_id": "27e6e100-d06e-46be-9a0b-8367a3790e6d",
  "status": "pending"
}
```

### Signification des champs

| Champ | Explication |
|---|---|
| `job_id` | Identifiant UUID unique du job de scraping. Il sert à suivre le job et à filtrer les résultats. |
| `status` | État initial du job. Il évolue de `pending` vers `running`, puis `done` ou `failed`. |

## 4. Suivi du job

```http
GET /api/scrape/{job_id}
```

Exemple de réponse :

```json
{
  "id": "27e6e100-d06e-46be-9a0b-8367a3790e6d",
  "input_url": "https://www.marchespublics.gov.tn/fr/appels-doffres",
  "status": "done",
  "error_message": null,
  "started_at": "2026-09-19T17:05:10.963Z",
  "finished_at": "2026-09-19T17:05:16.700Z",
  "created_at": "2026-09-19T17:05:10.928Z"
}
```

### Champs de réponse du job

| Champ | Explication |
|---|---|
| `id` | UUID du job. |
| `input_url` | URL envoyée par l'utilisateur. |
| `status` | `pending`, `running`, `done` ou `failed`. |
| `error_message` | Détail de l'erreur lorsque le statut est `failed`. Sinon `null`. |
| `started_at` | Moment où le traitement de scraping commence. |
| `finished_at` | Moment où le traitement se termine, avec succès ou échec. |
| `created_at` | Moment où le job est créé. |
| `current_stage` | Étape courante du discovery engine. |
| `pages_visited` | Nombre de pages déjà analysées. |
| `pages_discovered` | Nombre d'URLs découvertes. |
| `tender_pages_found` | Pages classées comme candidates tender. |
| `tenders_extracted` | Tenders extraits avant déduplication. |

## 5. Sortie des appels d'offres

```http
GET /api/tenders?page=1&page_size=20
```

Pour récupérer les résultats d'un job précis :

```http
GET /api/tenders?job_id={job_id}&page=1&page_size=100
```

Exemple :

```json
{
  "items": [
    {
      "id": "772cc045-974a-4002-8ed7-9d665c7fc1c5",
      "job_id": "27e6e100-d06e-46be-9a0b-8367a3790e6d",
      "source_url": "https://www.marchespublics.gov.tn/fr/appels-doffres/Tender-103830",
      "title": "Acquisition et transport de matériels informatiques",
      "description": "Objet et contenu textuel extrait de la page",
      "owner": "Commissariat Régional au Développement Agricole de Jendouba",
      "contact": null,
      "published_date": "2026-09-19",
      "deadline": "2026-10-19",
      "documents": [],
      "extraction_method": "marchespublics_tn",
      "scraped_at": "2026-09-19T17:05:16.700Z"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 100
}
```

### Champs d'un tender retourné par l'API

| Champ | Explication |
|---|---|
| `id` | UUID unique de l'appel d'offres enregistré. |
| `job_id` | UUID du job ayant produit ou actualisé cet appel d'offres. |
| `source_url` | URL de la page détaillée ou URL source de l'appel d'offres. |
| `title` | Titre ou objet de l'appel d'offres. |
| `description` | Texte descriptif extrait du HTML ou du contenu rendu. |
| `owner` | Organisme acheteur ou entité responsable. |
| `contact` | Contact trouvé par l'extracteur. Peut être `null`. |
| `page_type` | Type de page, notamment `TENDER_DETAIL`. |
| `confidence_score` | Confiance calculée par règles déterministes. |
| `confidence_signals` | Signaux explicables utilisés par le classificateur. |
| `discovery_url` | URL racine du job. |
| `discovery_depth` | Profondeur de découverte. |
| `discovery_path` | Chemin d'URLs jusqu'à la fiche. |
| `published_date` | Date de publication si elle est détectée. |
| `deadline` | Date limite de soumission si elle est détectée. |
| `documents` | Tableau JSON contenant les URLs de documents PDF, DOC ou DOCX. |
| `extraction_method` | Scraper utilisé, par exemple `generic` ou `marchespublics_tn`. |
| `scraped_at` | Date et heure de l'extraction ou de la mise à jour. |

Les champs optionnels peuvent être `null` lorsqu'ils ne sont pas présents sur la page source.

## 6. Données sauvegardées dans PostgreSQL

Le projet utilise deux tables principales : `scrape_jobs` et `tenders`.

### Table `scrape_jobs`

| Colonne | Type | Explication |
|---|---|---|
| `id` | UUID | Identifiant primaire du job. |
| `input_url` | TEXT | URL fournie pour le scraping. |
| `status` | TEXT | Statut contrôlé : `pending`, `running`, `done`, `failed`. |
| `error_message` | TEXT nullable | Message d'erreur en cas d'échec. |
| `started_at` | TIMESTAMPTZ nullable | Début du traitement. |
| `finished_at` | TIMESTAMPTZ nullable | Fin du traitement. |
| `created_at` | TIMESTAMPTZ | Création du job, par défaut `now()`. |

### Table `tenders`

| Colonne | Type | Explication |
|---|---|---|
| `id` | UUID | Identifiant primaire de l'appel d'offres. |
| `job_id` | UUID | Référence vers `scrape_jobs(id)`. Suppression en cascade si le job est supprimé. |
| `source_url` | TEXT | URL source ou URL détaillée. |
| `title` | TEXT nullable | Titre normalisé. |
| `description` | TEXT nullable | Description ou texte utile extrait. |
| `owner` | TEXT nullable | Organisme acheteur détecté. |
| `contact` | TEXT nullable | Contact détecté. |
| `published_date` | DATE nullable | Date de publication. |
| `deadline` | DATE nullable | Date limite. |
| `documents` | JSONB | Liste d'URLs de documents, par défaut `[]`. |
| `raw_html_snippet` | TEXT nullable | Extrait HTML limité pour conserver une trace de l'extraction. |
| `extraction_method` | TEXT | Méthode utilisée, par défaut `generic`. |
| `content_hash` | TEXT nullable | SHA-256 du contenu normalisé, utilisé pour détecter les doublons. |
| `scraped_at` | TIMESTAMPTZ | Date d'extraction, par défaut `now()`. |

### Déduplication

Le hash est calculé à partir de valeurs normalisées :

```text
source_url + title + description + published_date + deadline
```

Si un tender avec le même hash existe déjà :

- aucune nouvelle ligne n'est créée ;
- la ligne existante est mise à jour ;
- elle est réassociée au dernier `job_id` ;
- le frontend peut donc afficher les résultats du job courant.

Le titre seul ne sert pas de clé d'unicité.

### Index PostgreSQL

Les index principaux portent sur :

- le statut des jobs ;
- `tenders.job_id` ;
- `tenders.source_url` ;
- `tenders.content_hash` ;
- `tenders.scraped_at`.

## 7. Technologies utilisées

### Backend

- Python 3.11+
- FastAPI : API HTTP et Swagger
- Uvicorn : serveur ASGI
- SQLAlchemy 2.x : ORM
- PostgreSQL : base de données relationnelle
- Psycopg : driver PostgreSQL
- Pydantic v2 et Pydantic Settings : validation et configuration
- httpx : téléchargement HTTP
- BeautifulSoup4 et lxml : parsing HTML
- Playwright : rendu JavaScript pour les sites dynamiques
- pytest et pytest-asyncio : tests

### Frontend

- React
- Vite
- JavaScript
- Nginx pour le conteneur de production

### Infrastructure

- Docker
- Docker Compose
- n8n : workflow préparatoire d'appel API

## 8. Commandes d'exécution locale

Pour une base existante, appliquer la migration additive :

```powershell
psql "$env:DATABASE_URL" -f db/migrations/002_discovery_engine.sql
```

### PostgreSQL avec Docker

Depuis la racine du projet :

```powershell
docker compose -f docker/docker-compose.yml up -d postgres
```

Vérifier PostgreSQL :

```powershell
docker compose -f docker/docker-compose.yml ps
```

### Backend

Dans un terminal PowerShell :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\backend\.venv\Scripts\Activate.ps1

$env:PYTHONPATH="backend"
$env:DATABASE_URL="postgresql+psycopg://olivesoft:olivesoft@localhost:5432/olivesoft"
$env:BACKEND_CORS_ORIGINS='["http://localhost:5173","http://localhost:5174","http://192.168.0.14:5174"]'

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

URLs backend :

- API : http://localhost:8000
- Swagger : http://localhost:8000/docs
- Health : http://localhost:8000/health
- Health PostgreSQL : http://localhost:8000/health/db

### Frontend

Dans un autre terminal :

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

URLs frontend possibles :

- http://localhost:5173
- http://localhost:5174
- http://192.168.0.14:5174

Le port dépend de la disponibilité de Vite.

## 9. Commandes Docker complètes

```powershell
docker compose -f docker/docker-compose.yml up --build -d
```

Vérifier les services :

```powershell
docker compose -f docker/docker-compose.yml ps
```

Voir les logs backend :

```powershell
docker compose -f docker/docker-compose.yml logs -f backend
```

Arrêter les services :

```powershell
docker compose -f docker/docker-compose.yml stop
```

## 10. Tests

```powershell
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
```

Les tests utilisent une fixture HTML locale et ne dépendent pas d'un site Internet réel.

## 11. Test API manuel

```powershell
$body = @{ url = "https://www.marchespublics.gov.tn/fr/appels-doffres" } | ConvertTo-Json
$response = Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/api/scrape `
  -ContentType "application/json" `
  -Body $body

$response
```

Puis remplacer `<JOB_ID>` :

```powershell
Invoke-RestMethod http://localhost:8000/api/scrape/<JOB_ID>
Invoke-RestMethod "http://localhost:8000/api/tenders?job_id=<JOB_ID>&page=1&page_size=100"
```

## 12. Vérification PostgreSQL

```powershell
docker exec docker-postgres-1 psql -U olivesoft -d olivesoft -c "SELECT count(*) FROM scrape_jobs; SELECT count(*) FROM tenders;"
```

## 13. Limites actuelles

- Les sites JavaScript nécessitent Playwright ou un adapter spécifique.
- Les documents ne sont pas téléchargés ; seules leurs URLs sont stockées.
- Le crawling multi-pages n'est pas encore implémenté.
- Les données peuvent contenir des informations manquantes selon la structure du site.
- Le pipeline RAG, les LLM et la génération de propositions ne font pas partie de ce MVP.
