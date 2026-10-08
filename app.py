import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.title("🏃‍♂️ Suivi de Consommation à l'Effort")

DB_PRODUITS = "produits.csv"
DB_HISTORIQUE = "historique.csv"

# Charger les produits
if os.path.exists(DB_PRODUITS):
    df_produits = pd.read_csv(DB_PRODUITS)
else:
    df_produits = pd.DataFrame(columns=["Nom", "Glucides (g)", "Sodium (mg)"])

# Charger l'historique
if os.path.exists(DB_HISTORIQUE):
    df_historique = pd.read_csv(DB_HISTORIQUE)
else:
    df_historique = pd.DataFrame(columns=["Date", "Nom Sortie", "Durée (h)", "Glucides (g)", "Sodium (mg)", "Glucides/h", "Sodium/h", "Détail"])

tab1, tab2, tab3 = st.tabs(["📊 Enregistrer une Sortie", "📜 Historique", "⚙️ Gérer les Produits"])

# --- ONGLET 1 : Enregistrer une sortie ---
with tab1:
    st.header("Nouvelle Sortie")
    
    if df_produits.empty:
        st.warning("Aucun produit enregistré. Allez dans l'onglet 'Gérer les Produits' pour commencer.")
    else:
        # Informations générales sur la sortie
        col_info1, col_info2, col_info3 = st.columns([2, 1, 1])
        with col_info1:
            nom_sortie = st.text_input("Nom / Type de sortie", value="Sortie Longue")
        with col_info2:
            date_sortie = st.date_input("Date", value=datetime.now())
        with col_info3:
            duree_heures = st.number_input("Durée (heures)", min_value=0.1, value=2.0, step=0.5)

        st.divider()
        st.subheader("Produits consommés")
        
        quantites = {}
        for index, row in df_produits.iterrows():
            nom_p = row["Nom"]
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{nom_p}** ({row['Glucides (g)']}g carbs, {row['Sodium (mg)']}mg sodium)")
            with c2:
                quantites[nom_p] = st.number_input("Qté", min_value=0, value=0, step=1, key=f"qte_{nom_p}")

        produits_consommes = []
        total_glucides = 0.0
        total_sodium = 0.0
        detail_list = []

        for index, row in df_produits.iterrows():
            nom = row["Nom"]
            qte = quantites[nom]
            if qte > 0:
                g_tot = row["Glucides (g)"] * qte
                s_tot = row["Sodium (mg)"] * qte
                total_glucides += g_tot
                total_sodium += s_tot
                produits_consommes.append({
                    "Produit": nom,
                    "Quantité": qte,
                    "Glucides (g)": g_tot,
                    "Sodium (mg)": s_tot
                })
                detail_list.append(f"{qte}x {nom}")

        st.divider()

        if produits_consommes:
            st.subheader("Récapitulatif & Métriques Horaires")
            df_recap = pd.DataFrame(produits_consommes)
            st.dataframe(df_recap, use_container_width=True)

            # Calculs horaires
            g_par_heure = total_glucides / duree_heures
            s_par_heure = total_sodium / duree_heures

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Glucides Total", f"{total_glucides:.1f} g")
            m2.metric("Glucides / heure", f"{g_par_heure:.1f} g/h")
            m3.metric("Sodium Total", f"{total_sodium:.0f} mg")
            m4.metric("Sodium / heure", f"{s_par_heure:.0f} mg/h")

            # Bouton de sauvegarde
            if st.button("💾 Sauvegarder dans l'historique", type="primary"):
                nouvelle_entree = pd.DataFrame([{
                    "Date": date_sortie.strftime("%Y-%m-%d"),
                    "Nom Sortie": nom_sortie,
                    "Durée (h)": duree_heures,
                    "Glucides (g)": round(total_glucides, 1),
                    "Sodium (mg)": round(total_sodium, 0),
                    "Glucides/h": round(g_par_heure, 1),
                    "Sodium/h": round(s_par_heure, 0),
                    "Détail": ", ".join(detail_list)
                }])

                df_historique = pd.concat([df_historique, nouvelle_entree], ignore_index=True)
                df_historique.to_csv(DB_HISTORIQUE, index=False)
                st.success("Sortie enregistrée dans l'historique !")
                st.rerun()

# --- ONGLET 2 : Consulter l'historique ---
with tab3 if False else tab2:
    st.header("Historique des Sorties")
    
    if os.path.exists(DB_HISTORIQUE) and not pd.read_csv(DB_HISTORIQUE).empty:
        df_hist = pd.read_csv(DB_HISTORIQUE)
        st.dataframe(df_hist, use_container_width=True)
        
        # Effacer l'historique si besoin
        if st.button("🗑️ Effacer l'historique complet"):
            os.remove(DB_HISTORIQUE)
            st.warning("Historique effacé.")
            st.rerun()
    else:
        st.info("Aucune sortie n'a encore été enregistrée.")

# --- ONGLET 3 : Gestion des produits ---
with tab3:
    st.header("Gestion du catalogue de produits")
    subtab_add, subtab_edit = st.tabs(["➕ Ajouter", "✏️ Modifier / Supprimer"])

    with subtab_add:
        with st.form("form_produit_ajout", clear_on_submit=True):
            nom = st.text_input("Nom du produit")
            glucides = st.number_input("Glucides par portion (g)", min_value=0.0, step=0.5)
            sodium = st.number_input("Sodium par portion (mg)", min_value=0.0, step=10.0)
            if st.form_submit_button("Enregistrer"):
                if nom.strip() != "":
                    nouveau = pd.DataFrame([{"Nom": nom, "Glucides (g)": glucides, "Sodium (mg)": sodium}])
                    df_produits = pd.concat([df_produits, nouveau], ignore_index=True)
                    df_produits.to_csv(DB_PRODUITS, index=False)
                    st.success("Produit ajouté !")
                    st.rerun()

    with subtab_edit:
        if not df_produits.empty:
            produit_a_modifier = st.selectbox("Produit à modifier :", options=df_produits["Nom"].tolist())
            idx = df_produits[df_produits["Nom"] == produit_a_modifier].index[0]
            prod = df_produits.loc[idx]

            with st.form("form_produit_modif"):
                n_nom = st.text_input("Nom", value=prod["Nom"])
                n_g = st.number_input("Glucides (g)", min_value=0.0, value=float(prod["Glucides (g)"]))
                n_s = st.number_input("Sodium (mg)", min_value=0.0, value=float(prod["Sodium (mg)"]))
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.form_submit_button("💾 Enregistrer"):
                    df_produits.loc[idx] = [n_nom, n_g, n_s]
                    df_produits.to_csv(DB_PRODUITS, index=False)
                    st.rerun()
                if c_btn2.form_submit_button("🗑️ Supprimer"):
                    df_produits = df_produits.drop(idx).reset_index(drop=True)
                    df_produits.to_csv(DB_PRODUITS, index=False)
                    st.rerun()

    st.divider()
    st.dataframe(df_produits, use_container_width=True)