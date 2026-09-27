"""Selbstcheck: rechnet eine Referenzration mit den offiziellen Gruber-Werten durch.

    .venv/bin/python check.py
"""
from streamlit.testing.v1 import AppTest

# Referenzration: 20 kg Grassilage, 20 kg Maissilage, 4 kg Gerste, 3 kg Rapsextr.schrot
RATION = {"2014": 20.0, "2226": 20.0, "4025": 4.0, "6425": 3.0}
SOLL = {
    "Gesamt TS-Aufnahme": "20.19 kg",
    "Energie (MEₚₖ)": "227.7 MJ",
    "Dünndarmprotein (sidP)": "1932 g",
    "Rohprotein (CP)": "2916 g",
}

at = AppTest.from_file("app.py", default_timeout=60).run()
assert not at.exception, at.exception
assert len([n for n in at.number_input if str(n.key).isdigit()]) == 31   # 31 Futtermittel laut CSV
assert [s.value for s in at.subheader[:3]] == [
    "🌿 Grundfutterration", "🌾 Ausgleichskraftfutter", "💪 Leistungskraftfutter"]

for num, menge in RATION.items():
    at.number_input(key=num).set_value(menge)
at.run()
assert not at.exception, at.exception

ist = {m.label: m.value for m in at.metric}
for label, erwartet in SOLL.items():
    assert ist[label] == erwartet, f"{label}: {ist[label]} != {erwartet}"

# Bedarfsdeckung 650 kg / 25 kg Milch / 4,0 % Fett / 3,4 % Eiweiß (GfE 2023, Tab. 14)
assert at.metric[1].delta == "112.5% gedeckt", at.metric[1].delta   # 227,7 / (82,4 + 25x4,8)
assert at.metric[2].delta == "108.6% gedeckt", at.metric[2].delta
assert any("RMD" in w.value for w in at.warning) is False          # 1,0 g/kg TS liegt im Ziel

print("check.py ok - Ration deckt 112% Energie, 109% sidP, RMD 1,0 g/kg TS")
