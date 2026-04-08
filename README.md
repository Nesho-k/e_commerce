# Real-Time E-commerce Analytics Platform

Projet de Data Science appliqué à l'e-commerce : segmentation des clients par K-Means (RFM), réduction de dimension par ACP, tracking MLflow, le tout alimenté par un pipeline de données en temps réel (FastAPI, Airflow, PostgreSQL, AWS).

---

## Contexte

Ce projet simule l'infrastructure data d'une vraie entreprise e-commerce.

**Point de départ** : le dataset [Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), une marketplace brésilienne réelle avec 100 000+ commandes historiques (2016-2018). Ces données constituent la base historique de l'entreprise.

**Simulation temps réel** : une API FastAPI génère de nouvelles commandes toutes les 15 minutes, comme si l'entreprise continuait son activité en 2026. Les commandes suivent un cycle de vie réaliste (`processing` → `shipped` → `delivered`), avec des délais de livraison variables selon la région, une saisonnalité simulée (Black Friday, fêtes), et des avis clients générés automatiquement à la livraison.

**Objectif** : construire un projet de Data Science complet, de la donnée brute jusqu'au modèle en production. La partie Machine Learning (segmentation des clients par RFM + K-Means avec visualisation ACP et tracking MLflow) est le cœur du projet. Le pipeline Data Engineering (ETL, Airflow, AWS) est l'infrastructure qui permet de l'alimenter et de le faire tourner automatiquement en production.

---

## Compétences démontrées

| Compétence | Ce qui est fait dans ce projet |
|---|---|
| **Machine Learning** | Segmentation RFM + K-Means, ACP pour la visualisation, Silhouette score, tracking MLflow, déploiement automatisé via Airflow |
| **SQL** | Modélisation 3 couches (raw / clean / analytics), plus de 15 requêtes analytiques (CLV, cohortes, géographie, performance vendeurs...) |
| **Power BI** | Dashboard 6 pages connecté à PostgreSQL via DirectQuery (revenue, top produits, géographie, clients, vendeurs) |
| **Data Engineering** | Pipeline ETL toutes les 15 min, orchestration Airflow, simulation temps réel |
| **Déploiement Cloud** | Déploiement AWS (RDS + EC2 + ALB), CI/CD GitHub Actions |

---

## Architecture

Le projet s'articule autour de deux pipelines Airflow indépendants.

**Pipeline ETL (toutes les 15 minutes)** : FastAPI génère un batch de commandes simulées, Airflow les insère en base (couche raw), les nettoie (couche clean) puis recalcule les KPIs (couche analytics). Les dashboards Streamlit et Power BI se connectent directement à cette couche analytics.

**Pipeline ML (quotidien)** : un second DAG Airflow calcule les scores RFM de chaque client, entraîne le K-Means, track les métriques dans MLflow et sauvegarde les segments dans `analytics.customer_segments`.

---

## Segmentation des clients : RFM + K-Means + ACP

C'est le cœur data science du projet. Un DAG Airflow tourne quotidiennement pour segmenter automatiquement les clients en 4 groupes selon leur comportement d'achat.

**Méthode :**
1. Calcul des métriques RFM sur `clean.orders` + `clean.payments`
   - **Recency** : jours depuis le dernier achat
   - **Frequency** : nombre de commandes
   - **Monetary** : montant total dépensé
2. Standardisation (StandardScaler) + clustering K-Means (4 clusters)
3. Évaluation via Silhouette score (0.78 sur les données de production)
4. Tracking des runs avec MLflow (paramètres, métriques, modèle sérialisé)
5. Sauvegarde dans `analytics.customer_segments`

**Segments identifiés :**

| Segment | Caractéristiques |
|---|---|
| Champions | Multi-achats, montants élevés, récents |
| Clients fidèles | Récents, bon panier, meilleurs acheteurs uniques |
| A risque | Gros panier historique, inactifs depuis longtemps |
| Inactifs | Anciens clients, faible engagement |

> Le segment "Inactifs" représente ~93% des clients, cohérent avec le taux de réachat réel de 2,9% du dataset Olist, caractéristique structurelle du e-commerce brésilien 2016-2018.

**Visualisation ACP :** les 3 dimensions RFM (non visualisables directement) sont projetées en 2D via une Analyse en Composantes Principales pour représenter la séparation des clusters. Les axes affichent le pourcentage de variance expliquée.

---

## Stack technique

| Couche | Technologie |
|---|---|
| Ingestion | Python, FastAPI |
| Orchestration | Apache Airflow |
| Stockage | PostgreSQL (AWS RDS) |
| Transformation | SQL (3 couches : raw / clean / analytics) |
| Machine Learning | scikit-learn (K-Means), MLflow |
| Visualisation | Streamlit, Power BI |
| Déploiement | AWS EC2, Docker, GitHub Actions |

---

## Dataset

- **Source** : [Olist Brazilian E-commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle)
- **Volume** : 100 000+ commandes réelles (2016-2018)
- **Enrichissement** : nouvelles commandes générées dynamiquement via FastAPI avec saisonnalité simulée (Black Friday, fêtes de fin d'année, creux post-fêtes)

---

## Simulation temps réel

Toutes les 15 minutes, Airflow déclenche un cycle complet :

1. **Génération** : 8 à 15 nouvelles commandes avec saisonnalité réaliste
2. **Clients** : chaque commande crée un nouveau client en base
3. **Produits et vendeurs** : piochés dans les vrais IDs Olist
4. **Cycle de vie** : `processing` → `shipped` → `delivered` avec délais réalistes par état brésilien
5. **Avis** : note générée automatiquement à la livraison (distribution réelle Olist)
6. **KPIs** : recalculés automatiquement après chaque cycle

---

## Modélisation SQL (3 couches)

La base de données est organisée en trois couches progressives.

**raw** : données brutes telles qu'elles arrivent — commandes, articles, paiements, avis, clients, produits, vendeurs. Aucune transformation, insertion directe depuis l'API.

**clean** : données nettoyées et enrichies — valeurs nulles traitées, délais de livraison calculés, catégories traduites en anglais, paiements agrégés à la commande. C'est la couche de référence pour les analyses.

**analytics** : KPIs précalculés prêts à être consommés par les dashboards — revenue journalier et mensuel, top catégories, valeur vie client, performance vendeurs, analyse géographique, rétention par cohorte, et segments RFM générés par le K-Means.

---

## KPIs business

| KPI | Description |
|---|---|
| Chiffre d'affaires | Revenue journalier et mensuel avec croissance |
| Panier moyen | Valeur moyenne par commande |
| Customer Lifetime Value | Valeur totale et panier moyen par client |
| Taux de réachat | % de clients avec 2+ commandes |
| Top produits | Revenue et volume par catégorie |
| Performance vendeurs | Revenue, note moyenne, taux de livraison dans les délais |
| Analyse géographique | Revenue et délais par état brésilien |
| Modes de paiement | Répartition carte, boleto, voucher... |
| Rétention par cohorte | Fidélisation clients mois par mois |

---

## Dashboards

### Streamlit : temps réel

Accessible en ligne : [LIEN](http://ecommerce-alb-878817056.eu-north-1.elb.amazonaws.com/)

7 pages interactives connectées directement à PostgreSQL (AWS RDS) :
- **Vue Globale** : KPIs principaux (revenue, commandes, panier moyen, délai livraison)
- **Segmentation clients** : RFM + K-Means, 4 segments avec visualisation ACP 2D
- **Revenue** : évolution mensuelle et croissance du CA
- **Top Produits** : classement des catégories avec filtres
- **Géographie** : performance par état brésilien
- **Clients** : distribution des dépenses, CLV, taux de réachat
- **Vendeurs** : classement et performance des vendeurs

> Streamlit est privilégié pour le dashboard en ligne car il permet une connexion directe à PostgreSQL et une actualisation en temps réel, sans dépendance à un service cloud tiers.

### Power BI : analyse statique

Dashboard 6 pages connecté à PostgreSQL via DirectQuery : vue globale, revenue, top produits, géographie, clients, vendeurs. Utilisé pour la mise en forme orientée reporting et la maîtrise de l'outil BI standard en entreprise.

---

## Déploiement AWS

L'ensemble tourne sur AWS. La base de données est hébergée sur RDS (PostgreSQL managé), les services FastAPI, Airflow et Streamlit sont conteneurisés sur une instance EC2 t3.medium, et un Application Load Balancer expose Streamlit sur une URL publique. Chaque `git push` déclenche automatiquement le redéploiement via GitHub Actions.

---

## Structure du projet

- `api/` : API FastAPI avec générateur de commandes réalistes (saisonnalité, cycle de vie, délais par état)
- `airflow/dags/` : deux DAGs — ETL toutes les 15 min et segmentation RFM quotidienne
- `sql/` : scripts SQL des couches clean (7 fichiers) et analytics (8 fichiers)
- `scripts/` : chargement des données Olist, exécution des couches SQL, segmentation RFM + MLflow
- `docker/` : Dockerfiles pour l'API, Streamlit et Airflow
- `streamlit_app.py` : dashboard 7 pages connecté à PostgreSQL
- `docker-compose.yml` : orchestration de tous les services
- `.github/workflows/deploy.yml` : CI/CD GitHub Actions vers EC2

---

## Installation locale

### Prérequis
- Python 3.11+
- PostgreSQL 16
- Docker Desktop

### Lancement

```bash
# 1. Cloner le repo
git clone https://github.com/Nesho-k/e_commerce.git
cd e_commerce

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Remplir .env avec vos paramètres PostgreSQL

# 5. Charger les données Olist
python scripts/load_historical_data.py

# 6. Créer les couches SQL
python scripts/run_sql_layer.py clean
python scripts/run_sql_layer.py analytics

# 7. Lancer l'API
uvicorn api.main:app --reload --port 8000

# 8. Lancer Airflow (Docker)
docker compose up -d

# 9. Lancer Streamlit
streamlit run streamlit_app.py
```

---

## Auteur

**Nesho Kanthakumar**
Étudiant en Data Science 
[GitHub](https://github.com/Nesho-k) · [LinkedIn](https://www.linkedin.com/in/nesho-kanthakumar-6354512a6/)
