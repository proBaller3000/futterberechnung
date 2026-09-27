import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Futtermittelrechner (Gruber Tabelle)", layout="wide")

st.title("🌾 Futtermittel-Rationsrechner (Python & Streamlit)")
st.markdown("Berechnung basierend auf den Richtwerten der **Gruber Tabelle**.")

# 1. Beispieldaten für die Gruber-Tabelle & Futtermittel erstellen
@st.cache_data
def load_sample_data():
    # Beispielhafte Futtermitteldaten (TS, Energie, Protein, Calcium, Phosphor)
    # NEL = Netto-Energie-Laktation (für Milchkühe), nXP = nutzbares Rohprotein, RNB = Ruminale Stickstoffbilanz
    data = {
        "Futtermittel": ["Grassilage (mittlere Qualität)", "Maissilage (33% TS)", "Heu (normal)", "Gerstenschrot", "Rapsextraktionsschrot", "Körnermais"],
        "TS_g_kg": [350, 330, 880, 880, 890, 880], # Trockensubstanz g/kg Frischmasse
        "NEL_MJ_kg_TS": [6.0, 6.5, 5.4, 8.2, 7.2, 8.4],
        "nXP_g_kg_TS": [135, 125, 110, 145, 230, 150],
        "RNB_g_kg_TS": [2, -8, 1, -4, 30, -5],
        "Ca_g_kg_TS": [6.5, 2.5, 6.0, 0.8, 8.0, 0.4],
        "P_g_kg_TS": [3.2, 2.2, 2.5, 3.8, 11.0, 3.0]
    }
    return pd.DataFrame(data)

df_futtermittel = load_sample_data()

# Sidebar: Tierdaten & Bedarf (nach Gruber Tabelle vereinfacht)
st.sidebar.header("🐄 Tierdaten & Bedarf")
tierart = st.sidebar.selectbox("Tierkategorie", ["Milchkuh", "Mastbulle (coming soon)"])

if tierart == "Milchkuh":
    gewicht = st.sidebar.number_input("Lebendgewicht (kg)", min_value=400, max_value=900, value=650, step=50)
    milchmenge = st.sidebar.number_input("Tägliche Milchleistung (kg)", min_value=0, max_value=60, value=25, step=1)
    fett = st.sidebar.number_input("Milchfettgehalt (%)", min_value=2.0, max_value=6.0, value=4.0, step=0.1)
    eiweiss = st.sidebar.number_input("Milcheiweißgehalt (%)", min_value=2.0, max_value=5.0, value=3.4, step=0.1)
    
    # Bedarfsberechnung nach Gruber Tabelle (Näherungsformeln)
    # Erhaltungsbedarf + Leistungsbedarf
    bedarf_nel = (0.293 * (gewicht ** 0.75)) + (milchmenge * (0.4 * 0.15 * fett))
    # Leistungsbedarf nXP: ~25 g nXP je 1% Milcheiweiß je kg Milch (≈85 g bei 3,4%)
    bedarf_nxp = (gewicht * 0.7) + (milchmenge * eiweiss * 25)
    bedarf_ts = 0.02 * gewicht + 0.3 * milchmenge # Schätzung der TS-Aufnahmekapazität
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Berechneter Bedarf / Tag:")
    st.sidebar.write(f"**Energie (NEL):** {bedarf_nel:.1f} MJ")
    st.sidebar.write(f"**Protein (nXP):** {bedarf_nxp:.0f} g")
    st.sidebar.write(f"**Soll-TS-Aufnahme:** ~{bedarf_ts:.1f} kg")

# Hauptbereich: Rationsgestaltung
st.header("📋 Rationsgestaltung (Frischmasse pro Tag)")
st.write("Trage hier ein, wie viel kg Frischmasse (FM) das Tier pro Futtermittel fressen soll:")

ration_inputs = {}
cols = st.columns(3)

for idx, row in df_futtermittel.iterrows():
    with cols[idx % 3]:
        # Erstelle ein Eingabefeld für jedes Futtermittel
        ration_inputs[row["Futtermittel"]] = st.number_input(
            f"{row['Futtermittel']} (kg FM)", 
            min_value=0.0, 
            max_value=50.0, 
            value=0.0, 
            step=0.5,
            key=row["Futtermittel"]
        )

# Berechnung der gelieferten Nährstoffe
gesamt_ts = 0.0
gesamt_nel = 0.0
gesamt_nxp = 0.0
gesamt_rnb = 0.0

detaillierte_liste = []

for idx, row in df_futtermittel.iterrows():
    fm_menge = ration_inputs[row["Futtermittel"]]
    if fm_menge > 0:
        ts_menge = fm_menge * (row["TS_g_kg"] / 1000.0)
        nel_geliefert = ts_menge * row["NEL_MJ_kg_TS"]
        nxp_geliefert = ts_menge * row["nXP_g_kg_TS"]
        rnb_geliefert = ts_menge * row["RNB_g_kg_TS"]
        
        gesamt_ts += ts_menge
        gesamt_nel += nel_geliefert
        gesamt_nxp += nxp_geliefert
        gesamt_rnb += rnb_geliefert
        
        detaillierte_liste.append({
            "Futtermittel": row["Futtermittel"],
            "FM (kg)": fm_menge,
            "TS (kg)": round(ts_menge, 2),
            "NEL (MJ)": round(nel_geliefert, 1),
            "nXP (g)": round(nxp_geliefert, 0),
            "RNB (g)": round(rnb_geliefert, 0)
        })

# Auswertung anzeigen
st.header("📊 Rations-Auswertung")

if gesamt_ts > 0:
    df_res = pd.DataFrame(detaillierte_liste)
    st.dataframe(df_res, use_container_width=True)
    
    # Vergleich Soll vs. Ist
    st.subheader("⚖️ Bedarfsdeckung")
    
    deckung_nel = (gesamt_nel / bedarf_nel) * 100
    deckung_nxp = (gesamt_nxp / bedarf_nxp) * 100
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gesamt TS-Aufnahme", f"{gesamt_ts:.2f} kg", f"Ziel: {bedarf_ts:.1f} kg", delta_color="off")
    c2.metric("Energie (NEL)", f"{gesamt_nel:.1f} MJ", f"{deckung_nel:.1f}% gedeckt")
    c3.metric("Protein (nXP)", f"{gesamt_nxp:.0f} g", f"{deckung_nxp:.1f}% gedeckt")
    c4.metric("Gesamt RNB", f"{gesamt_rnb:.0f} g", "Ziel: leicht positiv / 0", delta_color="normal")
    
    # Optische Warnungen
    if deckung_nel < 95 or deckung_nel > 105:
        st.warning(f"⚠️ Die Energieversorgung liegt bei {deckung_nel:.1f}% (Optimal: 95-105%).")
    else:
        st.success("✅ Energieversorgung ist optimal!")
        
    if deckung_nxp < 95 or deckung_nxp > 105:
        st.warning(f"⚠️ Die Proteinversorgung (nXP) liegt bei {deckung_nxp:.1f}% (Optimal: 95-105%).")
    else:
        st.success("✅ Proteinversorgung (nXP) ist optimal!")
        
    if gesamt_rnb < 0:
        st.error("❌ Achtung: Die RNB ist negativ! Es könnte ein Stickstoffmangel im Pansen vorliegen.")
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
