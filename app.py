import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Futtermittelrechner (Gruber Tabelle)", layout="wide")

st.title("🌾 Futtermittel-Rationsrechner")
st.markdown("Nährwerte nach **LFL/Gruber Tabelle, Kapitel 9** (MEₚₖ-System, GfE 2023).")

# 1. Offizielle Nährwerttabelle (Kapitel 9 der Gruber Tabelle)
# ponytail: kein @st.cache_data - die CSV ist 20 kB, und der Cache serviert sonst
# nach jeder Datenänderung die alte Datei, bis der Server neu startet.
df_futtermittel = pd.read_csv("gruber_naehrstoffe.csv")

# Bedarfswerte nach GfE 2023 (Gruber Tab. 14 Erhaltung bei 21 kg TM, Tab. 17/19 Konzentrationen)
KOEGEWICHT = [600, 650, 700, 750, 800]
SIDP_ERHALTUNG = [640, 654, 667, 681, 694]          # g sidP/Tag
ME_ERHALTUNG = [77.6, 82.4, 87.1, 91.7, 96.3]       # MJ ME WK2023/Tag
EIWEISS_STUFEN = [3.2, 3.4, 3.6]
SIDP_PRO_KG_MILCH = [43, 45, 48]                    # g sidP je kg Milch
ME_FETT_STUFEN = [3.5, 4.0, 4.5]
ME_BASIS_32 = [4.4, 4.7, 5.0]                       # MJ je kg Milch bei 3,2 % Eiweiß
ME_EIWEISS_ZUSCHLAG = [0.0, 0.1, 0.2]               # + MJ je 0,2 % Eiweiß
MILCH_STUFEN = [10, 15, 20, 25, 30, 35, 40, 45, 50]
TM_AUFNAHME = [14.7, 16.1, 17.5, 18.9, 20.3, 21.7, 23.1, 24.5, 25.9]  # kg TM/Tag
CA_ZIEL = [3.7, 4.3, 4.8, 5.2, 5.6, 5.9, 6.2, 6.5, 6.7]   # g/kg TM
P_ZIEL = [2.1, 2.4, 2.6, 2.8, 3.0, 3.2, 3.3, 3.5, 3.6]    # g/kg TM
NA_ZIEL = [1.3, 1.4, 1.5, 1.6, 1.6, 1.7, 1.7, 1.8, 1.8]   # g/kg TM

# Sidebar: Tierdaten & Bedarf
st.sidebar.header("🐄 Tierdaten & Bedarf")
tierart = st.sidebar.selectbox("Tierkategorie", ["Milchkuh", "Mastbulle (coming soon)"])

if tierart == "Milchkuh":
    gewicht = st.sidebar.number_input("Lebendgewicht (kg)", min_value=400, max_value=900, value=650, step=50)
    milchmenge = st.sidebar.number_input("Tägliche Milchleistung (kg)", min_value=0, max_value=50, value=25, step=1)
    fett = st.sidebar.number_input("Milchfettgehalt (%)", min_value=2.0, max_value=6.0, value=4.0, step=0.1)
    eiweiss = st.sidebar.number_input("Milcheiweißgehalt (%)", min_value=2.0, max_value=5.0, value=3.4, step=0.1)

    # Bedarf = Erhaltung + Leistung (GfE 2023, Gruber Tab. 14)
    # ponytail: np.interp klemmt ausserhalb der Tabellenschritte (Fett > 4,5 %, Eiweiss < 3,2 %)
    # statt zu extrapolieren; volle Tabelle je Tabellenblatt, wenn das öfter vorkommt.
    bedarf_sidp = np.interp(gewicht, KOEGEWICHT, SIDP_ERHALTUNG) + milchmenge * np.interp(eiweiss, EIWEISS_STUFEN, SIDP_PRO_KG_MILCH)
    bedarf_me = np.interp(gewicht, KOEGEWICHT, ME_ERHALTUNG) + milchmenge * (
        np.interp(fett, ME_FETT_STUFEN, ME_BASIS_32) + np.interp(eiweiss, EIWEISS_STUFEN, ME_EIWEISS_ZUSCHLAG)
    )
    bedarf_ts = np.interp(milchmenge, MILCH_STUFEN, TM_AUFNAHME)
    ziel_ca = np.interp(milchmenge, MILCH_STUFEN, CA_ZIEL)
    ziel_p = np.interp(milchmenge, MILCH_STUFEN, P_ZIEL)
    ziel_na = np.interp(milchmenge, MILCH_STUFEN, NA_ZIEL)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Berechneter Bedarf / Tag:")
    st.sidebar.write(f"**Energie (MEₚₖ):** {bedarf_me:.1f} MJ")
    st.sidebar.write(f"**Dünndarmprotein (sidP):** {bedarf_sidp:.0f} g")
    st.sidebar.write(f"**Soll-TS-Aufnahme:** ~{bedarf_ts:.1f} kg")
    st.sidebar.write(f"**Zielkonzentration:** Ca {ziel_ca:.1f} / P {ziel_p:.1f} / Na {ziel_na:.1f} g je kg TS")

# Hauptbereich: Rationsgestaltung
st.header("📋 Rationsgestaltung (Frischmasse pro Tag)")
st.write("Trage hier ein, wie viel kg Frischmasse (FM) das Tier pro Futtermittel fressen soll:")

# Reihenfolge = Gliederung der Gruber-Tabelle: Kapitel 9.1-9.3, 9.4-9.9, 9.10, 9.11
KATEGORIEN = ["Grundfutterration", "Ausgleichskraftfutter", "Leistungskraftfutter", "Mineral und Spezialfutter"]
SYMBOL = {"Grundfutterration": "🌿", "Ausgleichskraftfutter": "🌾", "Leistungskraftfutter": "💪",
          "Mineral und Spezialfutter": "🧂"}

ration_inputs = {}
for kategorie in KATEGORIEN:
    st.subheader(f"{SYMBOL[kategorie]} {kategorie}")
    mittel = df_futtermittel[df_futtermittel["Kategorie"] == kategorie]
    cols = st.columns(3)
    for i, (_, row) in enumerate(mittel.iterrows()):
        with cols[i % 3]:
            if kategorie == "Mineral und Spezialfutter":
                ration_inputs[row["Num"]] = st.slider(
                    f"{row['Futtermittel']} (g FM)", 0.0, 2000.0, 0.0, 10.0, key=row["Num"]
                )
            else:
                ration_inputs[row["Num"]] = st.slider(
                    f"{row['Futtermittel']} (kg FM)", 0.0, 50.0, 0.0, 0.1, key=row["Num"]
                )

# Berechnung der gelieferten Nährstoffe
summen = {k: 0.0 for k in ["TS", "ME", "CP", "sidP", "RMD", "Ca", "P", "Na"]}
detaillierte_liste = []

for _, row in df_futtermittel.iterrows():
    fm_menge = ration_inputs.get(row["Num"], 0.0)
    if fm_menge > 0:
        if row["Kategorie"] == "Mineral und Spezialfutter":
            fm_kg = fm_menge / 1000.0
        else:
            fm_kg = fm_menge
        ts_menge = fm_kg * (row["TM_g_kg_FM"] / 1000.0)
        werte = {
            "TS": ts_menge,
            "ME": ts_menge * row["ME_MJ_kg_TM"],
            "CP": ts_menge * row["CP_g_kg_TM"],
            "sidP": ts_menge * row["sidP_g_kg_TM"],
            "RMD": ts_menge * row["RMD_g_kg_TM"],
            "Ca": ts_menge * row["Ca_g_kg_TM"],
            "P": ts_menge * row["P_g_kg_TM"],
            "Na": ts_menge * row["Na_g_kg_TM"],
        }
        for k, v in werte.items():
            summen[k] += v

        detaillierte_liste.append({
            "Futtermittel": row["Futtermittel"],
            "FM": f"{fm_menge:.0f} g" if row["Kategorie"] == "Mineral und Spezialfutter" else f"{fm_menge:.2f} kg",
            "TS (kg)": round(ts_menge, 2),
            "MEₚₖ (MJ)": round(werte["ME"], 1),
            "Rohprotein (g)": round(werte["CP"], 0),
            "sidP (g)": round(werte["sidP"], 0),
            "RMD (g)": round(werte["RMD"], 0),
            "Ca (g)": round(werte["Ca"], 1),
            "P (g)": round(werte["P"], 1)
        })

# Auswertung anzeigen
st.header("📊 Rations-Auswertung")

if summen["TS"] > 0:
    st.dataframe(pd.DataFrame(detaillierte_liste), use_container_width=True)

    deckung_me = (summen["ME"] / bedarf_me) * 100 if bedarf_me > 0 else 0
    deckung_sidp = (summen["sidP"] / bedarf_sidp) * 100 if bedarf_sidp > 0 else 0

    st.subheader("⚖️ Bedarfsdeckung")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gesamt TS-Aufnahme", f"{summen['TS']:.2f} kg", f"Ziel: {bedarf_ts:.1f} kg", delta_color="off")
    c2.metric("Energie (MEₚₖ)", f"{summen['ME']:.1f} MJ", f"{deckung_me:.1f}% gedeckt")
    c3.metric("Dünndarmprotein (sidP)", f"{summen['sidP']:.0f} g", f"{deckung_sidp:.1f}% gedeckt")
    c4.metric("Rohprotein (CP)", f"{summen['CP']:.0f} g", f"{summen['CP']/summen['TS']:.0f} g/kg TS", delta_color="off")

    ca_konz = summen["Ca"] / summen["TS"]
    p_konz = summen["P"] / summen["TS"]
    na_konz = summen["Na"] / summen["TS"]
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Rumenale Mikrobielle Differenz", f"{summen['RMD']:.0f} g", "Ziel: 0 bis +2 g/kg TS", delta_color="off")
    c6.metric("Calcium", f"{ca_konz:.1f} g/kg TS", f"Ziel: {ziel_ca:.1f} g/kg TS", delta_color="off")
    c7.metric("Phosphor", f"{p_konz:.1f} g/kg TS", f"Ziel: {ziel_p:.1f} g/kg TS", delta_color="off")
    c8.metric("Natrium", f"{na_konz:.1f} g/kg TS", f"Ziel: {ziel_na:.1f} g/kg TS", delta_color="off")

    # Optische Warnungen
    if deckung_me < 95 or deckung_me > 105:
        st.warning(f"⚠️ Die Energieversorgung liegt bei {deckung_me:.1f}% (Optimal: 95-105%).")
    else:
        st.success("✅ Energieversorgung ist optimal!")

    if deckung_sidp < 95 or deckung_sidp > 105:
        st.warning(f"⚠️ Die sidP-Versorgung liegt bei {deckung_sidp:.1f}% (Optimal: 95-105%).")
    else:
        st.success("✅ sidP-Versorgung ist optimal!")

    rmd_konz = summen["RMD"] / summen["TS"]
    if rmd_konz < 0:
        st.error("❌ RMD negativ: pansenstabiles Protein (UDP) fehlt, Ration proteinärmer füttern oder UDP ergänzen.")
    elif rmd_konz > 2:
        st.warning("⚠️ RMD über +2 g/kg TS: zu viel pansenstabiles Protein, pansenunverdaulichen Anteil senken.")

    if ca_konz < ziel_ca:
        st.warning(f"⚠️ Calcium liegt bei {ca_konz:.1f} g/kg TS, Zielwert ist {ziel_ca:.1f} g/kg TS.")
    if p_konz < ziel_p:
        st.warning(f"⚠️ Phosphor liegt bei {p_konz:.1f} g/kg TS, Zielwert ist {ziel_p:.1f} g/kg TS.")
    if na_konz < ziel_na:
        st.warning(f"⚠️ Natrium liegt bei {na_konz:.1f} g/kg TS, Zielwert ist {ziel_na:.1f} g/kg TS - Viehsalz fehlt.")
else:
    st.info("💡 Bitte trage oben Futtermengen ein, um die Berechnung zu starten.")

# Upload-Möglichkeit für eigene Excel-Dateien
st.markdown("---")
st.subheader("📁 Eigene Futtermittel-Excel hochladen")
uploaded_file = st.file_uploader("Lade hier deine eigene Excel-Tabelle hoch (Spalten müssen mit dem Beispiel übereinstimmen):", type=["xlsx"])
if uploaded_file:
    try:
        df_custom = pd.read_excel(uploaded_file)
        st.success("Excel erfolgreich geladen!")
        st.dataframe(df_custom.head(2))
        st.info("Hinweis: Um diese Tabelle voll zu integrieren, passen wir den Code im nächsten Schritt an deine genauen Spaltennamen an.")
    except Exception as e:
        st.error(f"Fehler beim Lesen der Datei: {e}")
