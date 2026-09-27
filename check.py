"""Selbstcheck: rechnet eine Referenzration mit den offiziellen Gruber-Werten durch.

    .venv/bin/python check.py
"""
from streamlit.testing.v1 import AppTest

# Referenzration: 20 kg Grassilage, 20 kg Maissilage, 4 kg Gerste, 3 kg Rapsextr.schrot, 70 g Viehsalz
RATION = {"2014": 20.0, "2226": 20.0, "4025": 4.0, "6425": 3.0, "4945": 0.07}
SOLL = {
    "Gesamt TS-Aufnahme": "20.26 kg",
    "Energie (MEₚₖ)": "236.8 MJ",
    "Dünndarmprotein (sidP)": "2025 g",
    "Rohprotein (CP)": "3078 g",
    "Natrium": "1.6 g/kg TS",
}

at = AppTest.from_file("app.py", default_timeout=60).run()
assert not at.exception, at.exception
assert len([n for n in at.number_input if str(n.key).isdigit()]) == 96   # 96 Futtermittel laut CSV
assert [s.value for s in at.subheader[:4]] == [
    "🌿 Grundfutterration", "🌾 Ausgleichskraftfutter", "💪 Leistungskraftfutter",
    "🧂 Mineral und Spezialfutter"]

for num, menge in RATION.items():
    at.number_input(key=num).set_value(menge)
at.run()
assert not at.exception, at.exception

ist = {m.label: m.value for m in at.metric}
for label, erwartet in SOLL.items():
    assert ist[label] == erwartet, f"{label}: {ist[label]} != {erwartet}"

# Bedarfsdeckung 650 kg / 25 kg Milch / 4,0 % Fett / 3,4 % Eiweiß (GfE 2023, Tab. 14)
assert at.metric[1].delta == "117.0% gedeckt", at.metric[1].delta   # 236,8 / (82,4 + 25x4,8)
assert at.metric[2].delta == "113.8% gedeckt", at.metric[2].delta
assert any("RMD" in w.value for w in at.warning) is False          # 1,0 g/kg TS liegt im Ziel
assert any("Natrium" in w.value for w in at.warning) is False     # Viehsalz schliesst die Na-Lücke

print("check.py ok - Ration deckt 117% Energie, 114% sidP, RMD 1,2 g/kg TS, Na 1,6 g/kg TS")
