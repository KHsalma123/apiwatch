# APIWatch – plateforme de monitoring d'API

Tableau de bord qui surveille la disponibilité et la performance d'API publiques : statut UP/DOWN, code HTTP,
temps de réponse, uptime, incidents.

**Stack :** React + Vite + Tailwind + Recharts · FastAPI + Pydantic + PyMongo Async · APScheduler + HTTPX · MongoDB Atlas · Docker · GitHub Actions · Azure.

## Comment ça marche

```
Navigateur (React) ──HTTPS/JSON+JWT──▶ API FastAPI ──▶ MongoDB ◀── Worker (APScheduler + HTTPX) ──▶ API surveillées
```

- **API (FastAPI)** : authentification, CRUD des monitors, lecture des stats. Elle ne fait **aucune** vérification planifiée.
- **Worker** : processus séparé (`python -m app.monitoring.worker`). Toutes les 10 s il *réserve* de façon atomique
  les monitors dont `next_check_at` est dépassé (`find_one_and_update`), les vérifie en parallèle, enregistre les
  résultats et ouvre/ferme les incidents. Deux workers lancés par erreur ne vérifieront jamais le même monitor deux fois.
- **MongoDB** est le seul point de rencontre entre l'API et le worker.

## Structure

```
backend/app/
  core/        configuration (variables d'environnement), rate limiting
  database/    connexion MongoDB + création des index
  security/    hash Argon2, JWT, dépendance get_current_user, protection SSRF
  schemas/     modèles Pydantic (validation des entrées/sorties)
  services/    logique métier (users, monitors, incidents, stats, dashboard)
  routers/     routes REST /api/v1/...
  monitoring/  checker.py (une vérification HTTPX) et worker.py (planificateur)
backend/tests/ tests Pytest (HTTP mocké)
frontend/src/  components, pages, layouts, services (axios), hooks, context, utils
docs/AZURE.md  architecture de déploiement et coûts
```

## Lancer le projet

### Option A – Docker Compose (le plus simple)

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # copier le résultat dans JWT_SECRET
docker compose up --build
```
Application : http://localhost:8080 · Documentation de l'API : http://localhost:8000/docs

Pour utiliser **MongoDB Atlas** au lieu du conteneur local : mettez votre URI `mongodb+srv://...` dans `MONGODB_URI`
(et autorisez votre IP dans *Network Access* sur Atlas).

### Option B – Développement sans Docker

```bash
# Terminal 1 – MongoDB local (ou une URI Atlas)
docker run -d --name apiwatch-mongo -p 27017:27017 mongo:7

# Terminal 2 – API
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env        # renseigner JWT_SECRET et MONGODB_URI=mongodb://localhost:27017
uvicorn app.main:app --reload

# Terminal 3 – Worker (même dossier backend, même venv)
python -m app.monitoring.worker

# Terminal 4 – Frontend
cd frontend
npm install
npm run dev                  # http://localhost:5173 (le proxy Vite redirige /api vers :8000)
```

## Tests

```bash
cd backend && pytest -q        # nécessite un MongoDB sur MONGODB_URI (défaut : mongodb://localhost:27017)
cd frontend && npm test
```
Aucun test n'appelle Internet : le DNS est simulé et les réponses HTTP passent par `httpx.MockTransport`.
Les tests SSRF, du checker et de la sécurité n'ont pas besoin de MongoDB ; les tests d'API et d'incidents, si.

## Sécurité (résumé)

- Mots de passe hachés avec **Argon2id** ; JWT à durée limitée ; chaque requête filtre par `user_id`
  (un monitor d'un autre utilisateur répond **404**, pas 403).
- **Anti-SSRF** (`backend/app/security/ssrf.py`) : http/https uniquement, ports restreints, pas d'identifiants dans l'URL,
  résolution DNS faite par le serveur, **toutes** les IP doivent être publiques (loopback, privées, link-local dont
  `169.254.169.254`, multicast, réservées refusées), connexion à l'IP validée (anti DNS rebinding), redirections suivies
  manuellement et revalidées à chaque saut, corps de réponse jamais téléchargé.
- Rate limiting (slowapi) sur register, login et vérification manuelle ; CORS restreint ; aucun secret dans le code.
- Compromis connu : le JWT est stocké dans `localStorage` (simple, mais exposé en cas de XSS). Amélioration possible :
  cookie httpOnly + protection CSRF.

## Choix de conception à connaître

- Un incident s'ouvre dès qu'une vérification est DOWN et qu'aucun incident n'est ouvert (y compris le premier check
  d'un monitor), et se ferme à la première vérification UP. Un index unique partiel garantit un seul incident OPEN par monitor.
- Le temps de réponse moyen ne compte que les vérifications UP.
- Les résultats expirent après 30 jours (index TTL) pour rester dans le palier gratuit d'Atlas.
- Intervalle minimum : 30 s ; 20 monitors maximum par utilisateur (modifiable dans `.env`).

## Pas encore implémenté

Notifications e-mail (les champs `notified_down` / `notified_recovery` sont déjà dans les incidents pour éviter les
doublons), nouvelle tentative avant de déclarer DOWN, en-têtes/corps personnalisés, pages de statut publiques.

## Déploiement Azure

Voir `docs/AZURE.md`. **Rien n'est créé automatiquement** : le workflow `deploy-azure.yml` est manuel et inactif
tant que vous n'avez pas créé les ressources et validé les coûts.
