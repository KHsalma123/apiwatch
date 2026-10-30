# Déploiement sur Azure (Azure for Students, 100 $ de crédit)

> Rien n'est provisionné automatiquement. Ce document décrit les options et les coûts attendus ;
> **validez un choix avant de créer la moindre ressource payante.**
> Les prix ci-dessous sont des ordres de grandeur : vérifiez-les dans le *Azure Pricing Calculator* avant de décider,
> ils changent et dépendent de la région.

## Ce qu'il faut héberger

| Composant | Particularité |
|---|---|
| Frontend (fichiers statiques) | Aucun serveur nécessaire |
| API FastAPI | Doit répondre à tout moment |
| **Worker** | Doit tourner **24 h/24** : c'est lui qui vérifie les API. Il ne peut pas « s'endormir ». |
| MongoDB | **Atlas M0 gratuit** (512 Mo), hors Azure : 0 $ |

Le worker est la contrainte de coût : les offres « scale to zero » ne conviennent pas à ce composant.

## Option A (recommandée pour démarrer) : une petite VM + Docker Compose

- 1 VM Linux **B1s** (ou B1ms) avec Docker, qui exécute `docker compose` (backend + worker + frontend/nginx).
- MongoDB : Atlas M0 (mettre l'URI dans `.env` sur la VM, jamais dans Git).
- Coût estimé : **environ 8 à 15 $/mois** pour la VM (+ disque, quelques dollars), soit 3 à 6 mois de crédit étudiant.
  Si votre abonnement inclut des heures B1s gratuites, ce sera moins.
- Avantage : le plus simple à comprendre et à déboguer, même configuration qu'en local.
- Inconvénients : vous gérez le serveur (mises à jour, pare-feu) ; HTTPS demande un reverse proxy (Caddy ou nginx + Let's Encrypt) et un nom de domaine.

## Option B : services managés

- **Frontend : Azure Static Web Apps, plan Free** (0 $). Définir `VITE_API_URL` au build vers l'URL publique de l'API.
- **API et worker : Azure Container Apps** (2 apps, même image `apiwatch-backend`, commande différente pour le worker).
  - API : peut tomber à 0 réplica, donc coût proche de 0 si peu de trafic.
  - Worker : **1 réplica permanent** (0,25 vCPU / 0,5 Gio) ; le quota gratuit mensuel peut ne pas suffire pour une
    charge 24 h/24, comptez **quelques dollars à une dizaine de dollars par mois**.
  - Registre d'images : Azure Container Registry *Basic* ≈ 5 $/mois (ou utiliser GitHub Container Registry, gratuit, pour économiser).
- Avantages : HTTPS et certificats gérés, pas de serveur à administrer. Inconvénient : plus de services à configurer.
- Ne pas oublier : `CORS_ORIGINS` doit contenir l'URL du frontend.

## Ce que je recommande

Commencer par l'**Option A** (la moins chère et la plus simple), puis passer à l'Option B si vous voulez
montrer une architecture cloud « managée » dans votre portfolio.

## Configuration commune

1. Atlas : cluster M0, utilisateur dédié avec droits limités à la base `apiwatch`, liste d'IP autorisées
   (l'IP sortante de la VM / des Container Apps).
2. Générer un `JWT_SECRET` fort (≥ 48 caractères aléatoires).
3. Secrets : variables d'environnement de la VM, ou *secrets* Container Apps ; jamais dans le dépôt.
4. Alerte de budget : créer une alerte de coût (par ex. 20 $) dans *Cost Management* avant tout déploiement.
5. Supprimer le groupe de ressources quand vous n'en avez plus besoin (`az group delete`).

## CI/CD

`.github/workflows/ci.yml` (tests + build) tourne à chaque push.
`.github/workflows/deploy-azure.yml` est **manuel** et prévu pour l'Option B (login OIDC, pas de mot de passe stocké).
Secrets GitHub à créer le moment venu : `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`,
`AZURE_RESOURCE_GROUP`, `ACR_LOGIN_SERVER`. Pour l'Option A, un simple `git pull && docker compose up -d --build` sur la VM suffit.
