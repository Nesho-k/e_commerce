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
| **Data Engineering** | Pipeline ETL toutes les 15 min, orchestration Airflow, simulation temps réel, déploiement AWS (RDS + EC2 + ALB), CI/CD GitHub Actions |

---

## Architecture

```
FastAPI (simulation commandes)
        │
        ▼
Apache Airflow (orchestration toutes les 15 min)
        │
        ├── Extract  → appel API, insertion dans PostgreSQL (raw)
        ├── Transform → nettoyage SQL (couche clean)
        └── Load     → calcul des KPIs (couche analytics)
                │
                ▼
        PostgreSQL (AWS RDS)
        ├── raw       : données brutes Olist + commandes simulées
        ├── clean     : données nettoyées et enrichies
        └── analytics : KPIs business + segments clients
                │
                ├── Streamlit (dashboard temps réel)
                └── Power BI  (dashboard statique)

FastAPI (simulation commandes)
        │
        ▼
Apache Airflow : DAG quotidien ML
        │
        └── RFM Segmentation
                ├── Calcul Recency / Frequency / Monetary
                ├── K-Means (4 clusters) + Silhouette score
                ├── MLflow (tracking des runs)
                └── analytics.customer_segments
```

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

```
raw/
├── raw_orders              Commandes brutes
├── raw_order_items         Articles commandés
├── raw_order_payments      Paiements
├── raw_order_reviews       Avis clients
├── raw_customers           Clients
├── raw_products            Produits
├── raw_sellers             Vendeurs
└── raw_product_category_translation

clean/
├── orders                  Commandes nettoyées + délais calculés
├── order_items             Articles enrichis avec catégories traduites
├── payments                Paiements agrégés (1 ligne par commande)
├── customers               Clients normalisés
├── products                Produits nettoyés
├── sellers                 Vendeurs
└── reviews                 Avis clients

analytics/
├── daily_revenue           Chiffre d'affaires journalier
├── monthly_revenue         Chiffre d'affaires mensuel + croissance
├── top_products            Top catégories par revenue
├── top_categories          Détail par catégorie
├── customer_lifetime_value CLV, panier moyen, taux de réachat
├── seller_performance      Performance vendeurs (revenue, notes, délais)
├── geo_analysis            Analyse géographique par état brésilien
├── payment_analysis        Répartition des modes de paiement
├── cohort_retention        Rétention clients par cohorte mensuelle
├── kpi_summary             Tableau de bord global
└── customer_segments       Segments RFM (généré par K-Means)
```

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

```
AWS RDS (PostgreSQL)     → base de données managée
AWS EC2 (t3.medium)      → FastAPI + Airflow + Streamlit (Docker)
AWS ALB                  → load balancer (port 80)
GitHub Actions           → CI/CD automatique à chaque git push
```

---

## Structure du projet

```
e-commerce/
├── api/
│   ├── main.py               API FastAPI (endpoints + lifecycle)
│   ├── models.py             Modèles Pydantic
│   └── data_generator.py     Générateur de commandes réalistes
├── airflow/
│   └── dags/
│       ├── ecommerce_pipeline.py   DAG ETL (extract/transform/load, toutes les 15 min)
│       └── rfm_pipeline.py         DAG segmentation RFM + K-Means (quotidien)
├── sql/
│   ├── clean/                Scripts SQL couche clean (7 fichiers)
│   └── analytics/            Scripts SQL couche analytics (8 fichiers)
├── scripts/
│   ├── load_historical_data.py     Chargement dataset Olist
│   ├── run_sql_layer.py            Exécution couches SQL
│   └── rfm_segmentation.py         Segmentation RFM + K-Means + MLflow
├── docker/
│   ├── Dockerfile.api
│   └── Dockerfile.streamlit
├── data/raw/                 Dataset Olist (non versionné)
├── streamlit_app.py          Dashboard temps réel
├── docker-compose.yml        Orchestration Docker
├── .github/workflows/
│   └── deploy.yml            CI/CD GitHub Actions
└── .env.example              Template variables d'environnement
```

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
