# Real-Time E-commerce Analytics Platform

> Pipeline de données complet simulant une plateforme e-commerce en temps réel.

## Architecture

```
Data Source (Olist CSV + API simulée)
        ↓
   FastAPI (génération commandes dynamiques)
        ↓
   Apache Airflow (orchestration ETL)
        ↓
   PostgreSQL (3 couches : raw → clean → analytics)
        ↓
   Power BI (dashboard KPI)
```

## Stack technique

| Composant | Technologie |
|---|---|
| API | FastAPI + Python |
| Orchestration | Apache Airflow |
| Base de données | PostgreSQL |
| Transformation | SQL (pattern Medallion) |
| Visualisation | Power BI |

## Structure du projet

```
├── api/                  # API FastAPI — génération de commandes
├── airflow/dags/         # DAGs Airflow — pipeline ETL
├── sql/
│   ├── raw/              # Données brutes
│   ├── clean/            # Données nettoyées
│   └── analytics/        # KPI et agrégations
├── data/raw/             # Dataset historique (non commité)
├── scripts/              # Scripts utilitaires
├── docker/               # Docker Compose
└── requirements.txt
```

## Installation

```bash
# 1. Cloner le repo
git clone https://github.com/ton-username/ecommerce-analytics-platform.git
cd ecommerce-analytics-platform

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Editer .env avec tes credentials PostgreSQL

# 5. Lancer l'API
uvicorn api.main:app --reload
```

## KPI suivis

- Chiffre d'affaires (journalier, mensuel)
- Top produits par catégorie
- Customer Lifetime Value (CLV)
- Panier moyen
- Taux de livraison dans les délais

## Dataset

Basé sur le dataset public [Olist Brazilian E-commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle).
