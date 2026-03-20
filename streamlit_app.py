"""
Real-Time E-commerce Analytics Dashboard
Streamlit app connectée à PostgreSQL — actualisation manuelle.
"""

import os
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

load_dotenv()

# ─────────────────────────────────────────
# Palette de couleurs
# ─────────────────────────────────────────
GREEN_DARK   = "#2D6A4F"
GREEN_MID    = "#52B788"
GREEN_LIGHT  = "#74C69D"
RED          = "#E63946"
YELLOW       = "#FFBA08"

# Dégradé vert (bon) → rouge (mauvais)
SCALE_GR    = [GREEN_MID, GREEN_LIGHT, YELLOW, RED]
SCALE_RG    = [RED, YELLOW, GREEN_LIGHT, GREEN_MID]
SCALE_GREEN = [GREEN_LIGHT, GREEN_MID, "#40916C", GREEN_DARK]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    font=dict(family="sans-serif", color="#1C1C1E"),
    title_font=dict(color="#1C1C1E", size=14),
    margin=dict(t=50, b=30, l=20, r=20),
)

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────
st.set_page_config(page_title="E-commerce Analytics", layout="wide")

st.markdown("""
<style>
/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2D6A4F 0%, #40916C 100%);
}
[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] .stRadio label {
    color: #FFFFFF !important;
}

/* Bouton actualiser */
[data-testid="stSidebar"] .stButton button {
    background-color: #1A4731 !important;
    color: #FFFFFF !important;
    border: 2px solid #FFFFFF !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 12px 0 !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background-color: #1A4731 !important;
    color: #FFFFFF !important;
    opacity: 0.85;
}

/* Radio navigation */
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.95rem !important;
    padding: 2px 0 !important;
}

/* Réduire les marges sidebar */
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
}
[data-testid="stSidebar"] h1 {
    font-size: 1.2rem !important;
    margin-bottom: 0.3rem !important;
    margin-top: 0.3rem !important;
}
[data-testid="stSidebar"] hr {
    margin: 0.4rem 0 !important;
}

/* Réduire l'espace en haut du contenu principal */
.block-container {
    padding-top: 1.5rem !important;
}

/* Réduire l'espace en haut de la sidebar */
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #F0F4F1;
    border-left: 4px solid #52B788;
    border-radius: 8px;
    padding: 16px;
}
[data-testid="stMetricValue"] {
    color: #2D6A4F;
    font-size: 1.6rem !important;
    font-weight: 700;
}
[data-testid="stMetricLabel"] {
    color: #555555;
    font-size: 0.85rem !important;
}

/* Titres */
h1 { color: #2D6A4F; font-weight: 700; }
h2, h3 { color: #40916C; }

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
}

/* Séparateur */
hr { border-color: #D8F3DC; }

/* Info box */
[data-testid="stAlert"] {
    border-left: 4px solid #52B788;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)

def query(sql: str) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn)

def apply_layout(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


# ─────────────────────────────────────────
# Sidebar navigation
# ─────────────────────────────────────────
if st.sidebar.button("Actualiser les données", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("E-commerce Analytics")
st.sidebar.markdown("""
<div style='color:#D8F3DC; font-size:0.88rem; line-height:1.5'>
Power BI Service nécessite une passerelle pour se connecter à une base locale,
ce qui le rend incompatible avec notre architecture.
Streamlit se connecte directement à PostgreSQL, se rafraîchit en temps réel
et sera déployé sur AWS avec une URL publique.
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='text-align:center; padding: 4px 0 8px 0;'>
        <a href='https://github.com/Nesho-k/e_commerce' target='_blank'
           style='color:#FFFFFF; font-size:0.85rem; text-decoration:none;
                  background:#2D6A4F; padding:6px 14px; border-radius:6px;
                  display:inline-block;'>
            Code source GitHub
        </a>
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    ["Vue Globale", "Segmentation", "Revenue", "Top Produits", "Géographie", "Clients", "Vendeurs"],
)


# ─────────────────────────────────────────
# PAGE 1 — Vue Globale
# ─────────────────────────────────────────
if page == "Vue Globale":
    st.title("Vue Globale")

    st.markdown("""
<div style='background:#F0F4F1; border-left:4px solid #52B788; border-radius:8px; padding:12px 16px; margin-bottom:16px; color:#2D6A4F; font-size:0.92rem'>
    De nouvelles commandes sont simulées automatiquement <strong>toutes les 15 minutes</strong> via un pipeline Airflow/FastAPI.
    Le volume varie selon la période : pics en novembre (Black Friday) et décembre (Noël),
    creux en janvier-février. Chaque commande suit un cycle de vie réaliste :
    <strong>processing → shipped → delivered</strong>, avec des délais de livraison adaptés à l'état du client.
</div>
""", unsafe_allow_html=True)

    total_revenue = query("SELECT SUM(revenue) AS total_revenue FROM analytics.monthly_revenue").iloc[0, 0]
    kpi = query("""
        SELECT
            COUNT(DISTINCT order_id)                                AS total_orders,
            ROUND(AVG(total_payment)::numeric, 2)                   AS avg_basket,
            ROUND(AVG(delivery_days)::numeric, 1)                   AS avg_delivery_days
        FROM clean.orders o
        JOIN clean.payments p USING (order_id)
        WHERE order_status = 'delivered'
          AND delivery_days IS NOT NULL
          AND delivery_days > 0
    """).iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"{total_revenue:,.0f} R$")
    col2.metric("Total Commandes", f"{int(kpi['total_orders']):,}")
    col3.metric("Panier Moyen", f"{kpi['avg_basket']:,.2f} R$")
    col4.metric("Délai Moyen Livraison", f"{kpi['avg_delivery_days']:.1f} jours")

    st.markdown("---")

    st.subheader("Commandes récentes")
    recent = query("""
        SELECT order_id, customer_id, order_status, order_purchase_timestamp
        FROM raw.raw_orders
        ORDER BY order_purchase_timestamp DESC
        LIMIT 20
    """)
    st.dataframe(recent, use_container_width=True)

    st.subheader("Pipeline des commandes simulées (2026)")
    statuts = query("""
        SELECT order_status, COUNT(*) AS nb_commandes
        FROM raw.raw_orders
        WHERE order_purchase_timestamp::text >= '2026-01-01'
        GROUP BY order_status
        ORDER BY nb_commandes DESC
    """)
    if not statuts.empty:
        fig = px.bar(
            statuts, x="order_status", y="nb_commandes",
            color="order_status",
            color_discrete_map={
                "processing": YELLOW,
                "shipped":    GREEN_LIGHT,
                "delivered":  GREEN_MID,
            },
            labels={"order_status": "Statut", "nb_commandes": "Nombre"},
            title="Répartition des statuts — commandes 2026",
        )
        st.plotly_chart(apply_layout(fig), use_container_width=True)
    else:
        st.info("Aucune commande simulée pour l'instant. Lance le DAG Airflow.")


# ─────────────────────────────────────────
# PAGE 2 — Segmentation RFM
# ─────────────────────────────────────────
elif page == "Segmentation":
    st.title("Segmentation clients — RFM + K-Means")

    st.markdown("""
<div style='background:#F0F4F1; border-left:4px solid #52B788; border-radius:8px; padding:12px 16px; margin-bottom:16px; color:#2D6A4F; font-size:0.92rem'>
    La segmentation RFM analyse chaque client selon trois dimensions : <strong>Recency</strong> (jours depuis le dernier achat),
    <strong>Frequency</strong> (nombre de commandes) et <strong>Monetary</strong> (montant total dépensé).
    Un algorithme K-Means regroupe ensuite les clients en 4 segments. Dans le dataset Olist, 97% des clients
    n'achètent qu'une seule fois — les labels sont donc <strong>relatifs</strong> : "Clients fidèles" désigne les meilleurs
    acheteurs uniques (récents, bon panier), pas nécessairement des clients multi-achats.
</div>
""", unsafe_allow_html=True)

    seg = query("SELECT * FROM analytics.customer_segments")

    if seg.empty:
        st.info("Aucune donnée de segmentation. Lance scripts/rfm_segmentation.py.")
    else:
        SEGMENT_COLORS = {
            "Champions":       GREEN_DARK,
            "Clients fidèles": GREEN_MID,
            "A risque":        YELLOW,
            "Inactifs":        RED,
        }

        summary = seg.groupby("segment").agg(
            nb_clients=("customer_unique_id", "count"),
            recency_med=("recency", "median"),
            frequency_med=("frequency", "median"),
            monetary_med=("monetary", "median"),
        ).reset_index().sort_values("monetary_med", ascending=False)

        col1, col2, col3, col4 = st.columns(4)
        for col, (_, row) in zip([col1, col2, col3, col4], summary.iterrows()):
            col.metric(row["segment"], f"{int(row['nb_clients']):,} clients")

        st.markdown("---")
        st.subheader("Visualisation des clusters K-Means (ACP 2D)")
        st.caption(
            "Les 3 dimensions RFM sont réduites à 2 composantes principales (ACP) pour la visualisation. "
            "Échantillon de 5 000 clients."
        )

        sample = seg.sample(min(5000, len(seg)), random_state=42).copy()

        # Écrêtage des outliers au 99e percentile avant PCA
        for col in ["recency", "frequency", "monetary"]:
            cap = sample[col].quantile(0.99)
            sample[col] = sample[col].clip(upper=cap)

        features_scaled = StandardScaler().fit_transform(sample[["recency", "frequency", "monetary"]])
        pca = PCA(n_components=2, random_state=42)
        pca_coords = pca.fit_transform(features_scaled)
        sample["PC1"] = pca_coords[:, 0]
        sample["PC2"] = pca_coords[:, 1]
        variance_explained = pca.explained_variance_ratio_ * 100

        fig_pca = px.scatter(
            sample,
            x="PC1", y="PC2",
            color="segment",
            color_discrete_map=SEGMENT_COLORS,
            opacity=0.55,
            title="Clusters K-Means projetés sur 2 composantes principales (ACP)",
            labels={
                "PC1": f"PC1 ({variance_explained[0]:.1f}% de variance expliquée)",
                "PC2": f"PC2 ({variance_explained[1]:.1f}% de variance expliquée)",
            },
            height=520,
        )
        fig_pca.update_traces(marker=dict(size=5))
        fig_pca.update_layout(
            legend=dict(
                font=dict(size=14),
                title=dict(text="Segment", font=dict(size=15)),
                itemsizing="constant",
            )
        )
        st.plotly_chart(apply_layout(fig_pca), use_container_width=True)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                summary.sort_values("nb_clients", ascending=False),
                x="segment", y="nb_clients",
                title="Nombre de clients par segment",
                labels={"segment": "Segment", "nb_clients": "Nb clients"},
                color="segment",
                color_discrete_map=SEGMENT_COLORS,
            )
            st.plotly_chart(apply_layout(fig), use_container_width=True)

        with col2:
            fig2 = px.bar(
                summary,
                x="segment", y="monetary_med",
                title="Panier médian par segment (R$)",
                labels={"segment": "Segment", "monetary_med": "Montant médian (R$)"},
                color="segment",
                color_discrete_map=SEGMENT_COLORS,
            )
            st.plotly_chart(apply_layout(fig2), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig3 = px.bar(
                summary.sort_values("recency_med"),
                x="segment", y="recency_med",
                title="Recency médiane — jours depuis le dernier achat",
                labels={"segment": "Segment", "recency_med": "Jours"},
                color="segment",
                color_discrete_map=SEGMENT_COLORS,
            )
            st.plotly_chart(apply_layout(fig3), use_container_width=True)

        with col2:
            fig4 = px.bar(
                summary.sort_values("frequency_med", ascending=False),
                x="segment", y="frequency_med",
                title="Fréquence médiane — nombre de commandes",
                labels={"segment": "Segment", "frequency_med": "Nb commandes"},
                color="segment",
                color_discrete_map=SEGMENT_COLORS,
            )
            st.plotly_chart(apply_layout(fig4), use_container_width=True)

        st.markdown("---")
        st.subheader("Profil détaillé par segment")
        st.dataframe(
            summary.rename(columns={
                "segment": "Segment",
                "nb_clients": "Nb clients",
                "recency_med": "Recency médiane (j)",
                "frequency_med": "Frequency médiane",
                "monetary_med": "Monetary médiane (R$)",
            }),
            use_container_width=True,
        )


# ─────────────────────────────────────────
# PAGE 3 — Revenue
# ─────────────────────────────────────────
elif page == "Revenue":
    st.title("Revenue")

    monthly = query("SELECT * FROM analytics.monthly_revenue ORDER BY month")
    daily   = query("SELECT * FROM analytics.daily_revenue ORDER BY order_date")

    monthly["month"]      = pd.to_datetime(monthly["month"])
    daily["order_date"]   = pd.to_datetime(daily["order_date"])

    monthly_hist = monthly[monthly["month"].dt.year <= 2018]
    monthly_sim  = monthly[monthly["month"].dt.year >= 2026]
    daily_hist   = daily[daily["order_date"].dt.year <= 2018]
    daily_sim    = daily[daily["order_date"].dt.year >= 2026]

    st.subheader("Données historiques Olist (2016-2018)")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(
            monthly_hist, x="month", y="revenue",
            title="Chiffre d'affaires mensuel",
            labels={"month": "Mois", "revenue": "Revenue (R$)"},
            markers=True, color_discrete_sequence=[GREEN_MID],
        )
        st.plotly_chart(apply_layout(fig), use_container_width=True)

    with col2:
        mf = monthly_hist[
            monthly_hist["revenue_growth_pct"].notna() &
            (monthly_hist["revenue_growth_pct"].abs() < 500)
        ]
        fig2 = px.bar(
            mf, x="month", y="revenue_growth_pct",
            title="Croissance mensuelle du CA (%)",
            labels={"month": "Mois", "revenue_growth_pct": "Croissance (%)"},
            color="revenue_growth_pct",
            color_continuous_scale=[RED, YELLOW, GREEN_MID],
            color_continuous_midpoint=0,
        )
        st.plotly_chart(apply_layout(fig2), use_container_width=True)

    st.markdown("---")
    st.subheader("Données simulées (2026+)")

    if monthly_sim.empty:
        st.info("Aucune commande livrée en 2026 pour l'instant. Attends qu'Airflow traite les premières commandes.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fig3 = px.line(
                monthly_sim, x="month", y="revenue",
                title="Chiffre d'affaires mensuel (2026)",
                labels={"month": "Mois", "revenue": "Revenue (R$)"},
                markers=True, color_discrete_sequence=[GREEN_MID],
            )
            st.plotly_chart(apply_layout(fig3), use_container_width=True)
        with col2:
            msf = monthly_sim[
                monthly_sim["revenue_growth_pct"].notna() &
                (monthly_sim["revenue_growth_pct"].abs() < 500)
            ]
            if not msf.empty:
                fig4 = px.bar(
                    msf, x="month", y="revenue_growth_pct",
                    title="Croissance mensuelle du CA % (2026)",
                    labels={"month": "Mois", "revenue_growth_pct": "Croissance (%)"},
                    color="revenue_growth_pct",
                    color_continuous_scale=[RED, "white", GREEN_MID],
                    color_continuous_midpoint=0,
                )
                st.plotly_chart(apply_layout(fig4), use_container_width=True)

    st.markdown("---")
    st.subheader("Revenue journalier")
    col1, col2 = st.columns(2)
    with col1:
        fig5 = px.area(
            daily_hist, x="order_date", y="revenue",
            title="Revenue journalier (2016-2018)",
            labels={"order_date": "Date", "revenue": "Revenue (R$)"},
            color_discrete_sequence=[GREEN_MID],
        )
        fig5.update_traces(fillcolor=GREEN_MID, opacity=0.4)
        st.plotly_chart(apply_layout(fig5), use_container_width=True)
    with col2:
        if daily_sim.empty:
            st.info("Pas encore de données journalières 2026.")
        else:
            fig6 = px.area(
                daily_sim, x="order_date", y="revenue",
                title="Revenue journalier (2026) — données simulées",
                labels={"order_date": "Date", "revenue": "Revenue (R$)"},
                color_discrete_sequence=[GREEN_MID],
            )
            fig6.update_traces(fillcolor=GREEN_LIGHT)
            st.plotly_chart(apply_layout(fig6), use_container_width=True)


# ─────────────────────────────────────────
# PAGE 3 — Top Produits
# ─────────────────────────────────────────
elif page == "Top Produits":
    st.title("Top Produits")

    top = query("SELECT * FROM analytics.top_categories ORDER BY total_revenue DESC")

    min_orders = st.slider("Nombre minimum de commandes", 1, 400, 100)
    top_filtered = top[top["total_orders"] >= min_orders]
    st.caption(f"{len(top_filtered)} catégories affichées sur {len(top)}")

    df_chart = top_filtered.head(20).sort_values("total_revenue", ascending=False)
    fig = px.bar(
        df_chart,
        x="category", y="total_revenue",
        title=f"Top catégories par revenue (min {min_orders} commandes)",
        labels={"total_revenue": "Revenue (R$)", "category": "Catégorie"},
        color_discrete_sequence=[GREEN_MID],
        height=500,
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="sans-serif", color="#1C1C1E"),
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Détail par catégorie")
        st.dataframe(
            top_filtered[["category", "total_orders", "total_revenue", "avg_price"]],
            use_container_width=True,
        )
    with col2:
        fig2 = px.bar(
            top_filtered.head(10).sort_values("avg_price", ascending=False),
            x="category", y="avg_price",
            title="Prix moyen par catégorie — Top 10",
            labels={"category": "Catégorie", "avg_price": "Prix moyen (R$)"},
            color="avg_price",
            color_continuous_scale=SCALE_GREEN,
        )
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(apply_layout(fig2), use_container_width=True)


# ─────────────────────────────────────────
# PAGE 4 — Géographie
# ─────────────────────────────────────────
elif page == "Géographie":
    st.title("Géographie")

    geo = query("SELECT * FROM analytics.geo_analysis ORDER BY total_revenue DESC")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            geo, x="state", y="total_revenue",
            title="Revenue par état",
            labels={"state": "État", "total_revenue": "Revenue (R$)"},
            color="total_revenue",
            color_continuous_scale=SCALE_GREEN,
        )
        st.plotly_chart(apply_layout(fig), use_container_width=True)

    with col2:
        fig2 = px.bar(
            geo.sort_values("on_time_rate_pct", ascending=False),
            x="state", y="on_time_rate_pct",
            title="Taux de livraison à temps par état (%)",
            labels={"state": "État", "on_time_rate_pct": "Taux à temps (%)"},
            color="on_time_rate_pct",
            color_continuous_scale=SCALE_RG,
        )
        st.plotly_chart(apply_layout(fig2), use_container_width=True)

    st.subheader("Tableau détaillé")
    st.dataframe(
        geo[["state", "total_orders", "total_revenue", "avg_delivery_days",
             "on_time_rate_pct", "avg_review_score"]],
        use_container_width=True,
    )


# ─────────────────────────────────────────
# PAGE 5 — Clients
# ─────────────────────────────────────────
elif page == "Clients":
    st.title("Clients")

    clv = query("SELECT * FROM analytics.customer_lifetime_value")

    kpi_clients = query("""
        SELECT
            COUNT(DISTINCT c.customer_unique_id)    AS total_clients,
            ROUND(AVG(p.total_payment)::numeric, 2) AS avg_basket
        FROM clean.customers c
        JOIN clean.orders o   ON c.customer_id = o.customer_id
        JOIN clean.payments p ON o.order_id    = p.order_id
        WHERE o.order_status = 'delivered'
    """)

    total_clients = int(kpi_clients["total_clients"].iloc[0])
    avg_basket    = float(kpi_clients["avg_basket"].iloc[0])
    taux_reachat  = (clv["total_orders"] >= 2).sum() / len(clv) * 100 if len(clv) > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total clients", f"{total_clients:,}")
    col2.metric("Panier moyen", f"{avg_basket:,.2f} R$")
    col3.metric("Taux de réachat", f"{taux_reachat:.1f}%")

    col1, col2 = st.columns(2)

    with col1:
        bins   = [0, 100, 200, 500, 1000, float("inf")]
        labels = ["0-100 R$", "100-200 R$", "200-500 R$", "500-1000 R$", "1000+ R$"]
        clv["spending_range"] = pd.cut(clv["total_spent"], bins=bins, labels=labels)
        dist = clv["spending_range"].value_counts().sort_index().reset_index()
        dist.columns = ["spending_range", "count"]

        fig = px.bar(
            dist, x="spending_range", y="count",
            title="Distribution des dépenses clients",
            labels={"spending_range": "Tranche", "count": "Nombre de clients"},
            color="count",
            color_continuous_scale=SCALE_GREEN,
        )
        st.plotly_chart(apply_layout(fig), use_container_width=True)

    with col2:
        fig2 = px.histogram(
            clv[clv["total_orders"] <= 10],
            x="total_orders",
            title="Distribution du nombre de commandes par client",
            labels={"total_orders": "Nb commandes"},
            color_discrete_sequence=[GREEN_MID],
        )
        st.plotly_chart(apply_layout(fig2), use_container_width=True)


# ─────────────────────────────────────────
# PAGE 7 — Vendeurs
# ─────────────────────────────────────────
elif page == "Vendeurs":
    st.title("Performance Vendeurs")

    sellers = query("""
        SELECT ROW_NUMBER() OVER (ORDER BY total_revenue DESC) AS rank,
               total_revenue, avg_review_score, on_time_rate_pct,
               total_orders, avg_delivery_days
        FROM analytics.seller_performance
        ORDER BY total_revenue DESC
    """)

    col1, col2, col3 = st.columns(3)
    col1.metric("Nb vendeurs", f"{len(sellers):,}")
    col2.metric("Note moyenne", f"{sellers['avg_review_score'].mean():.2f} / 5")
    col3.metric("Taux livraison à temps", f"{sellers['on_time_rate_pct'].mean():.1f}%")

    top_n = st.slider("Afficher le Top N vendeurs", 10, 100, 20)
    sellers_top = sellers.head(top_n)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            sellers_top.sort_values("avg_review_score", ascending=False),
            x="rank", y="avg_review_score",
            title=f"Note moyenne — Top {top_n} vendeurs",
            labels={"rank": "Rang vendeur", "avg_review_score": "Note moyenne"},
            color="avg_review_score",
            color_continuous_scale=SCALE_RG,
        )
        st.plotly_chart(apply_layout(fig), use_container_width=True)

    with col2:
        st.subheader(f"Top {top_n} vendeurs")
        st.dataframe(
            sellers_top[["rank", "total_revenue", "avg_review_score",
                          "on_time_rate_pct", "total_orders"]],
            use_container_width=True,
        )
