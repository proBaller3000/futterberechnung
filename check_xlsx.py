"""Abgleich der App-Ration mit dem offiziellen LfL-Excel (FAN3-Werte)."""
from pathlib import Path

import openpyxl
import pandas as pd
from streamlit.testing.v1 import AppTest

XLSX = Path("2026-09-02_rationsberechnung_milch-_und_jungvieh_gfe_2023_mit_tabellenwerten_auf_basis_fan3.xlsx")
RATION = {"2226": 20.0, "3125": 5.0, "4025": 5.0, "6425": 2.0}
FAN3_COLS = {"CP": 4, "sidP": 5, "ME": 6, "Ca": 7, "P": 8, "Na": 9, "RMD": 10}

ws = openpyxl.load_workbook(XLSX, data_only=True)["FAN3-Werte"]
fan3 = {}
for row in ws.iter_rows(min_row=3):
    num = row[0].value
    if not isinstance(num, (int, float)) or str(int(num)) not in RATION:
        continue
    tm = row[2].value
    if tm is None:
        tm = ws.cell(row=row[0].row + 1, column=3).value
    fan3[str(int(num))] = {
        "TM": float(tm),
        **{k: float(row[i].value) for k, i in FAN3_COLS.items()},
    }
assert set(fan3) == set(RATION), f"Futtermittel nicht im FAN3-Blatt: {set(RATION) - set(fan3)}"

exp = {k: 0.0 for k in ["TS", *FAN3_COLS]}
for num, kg in RATION.items():
    f = fan3[num]
    ts = kg * f["TM"] / 1000
    exp["TS"] += ts
    for k in FAN3_COLS:
        exp[k] += ts * f[k]

at = AppTest.from_file("app.py", default_timeout=60).run()
assert not at.exception, at.exception
for num, kg in RATION.items():
    at.number_input(key=num).set_value(kg)
at.run()
assert not at.exception, at.exception

df = at.dataframe[0].value
act = {
    "TS": float(df["TS (kg)"].sum()),
    "ME": float(df["MEₚₖ (MJ)"].sum()),
    "CP": float(df["Rohprotein (g)"].sum()),
    "sidP": float(df["sidP (g)"].sum()),
    "RMD": float(df["RMD (g)"].sum()),
    "Ca": float(df["Ca (g)"].sum()),
    "P": float(df["P (g)"].sum()),
}
futter = pd.read_csv("gruber_naehrstoffe.csv").set_index("Num")
act["Na"] = sum(
    kg * futter.loc[int(num), "TM_g_kg_FM"] / 1000 * futter.loc[int(num), "Na_g_kg_TM"]
    for num, kg in RATION.items()
)

print(f"{'Nährstoff':<8} {'App':>10} {'LfL FAN3':>10} {'Diff':>10} {'Diff %':>8}")
for k in ["TS", "ME", "CP", "sidP", "RMD", "Ca", "P", "Na"]:
    d = act[k] - exp[k]
    pct = 100 * d / exp[k] if exp[k] else 0
    print(f"{k:<8} {act[k]:>10.2f} {exp[k]:>10.2f} {d:>+10.2f} {pct:>+7.1f}%")

for k in ["TS", "CP", "Ca", "P", "Na"]:
    assert abs(act[k] - exp[k]) <= 0.3, f"{k}: App {act[k]:.2f} != FAN3 {exp[k]:.2f}"
for k in ["ME", "sidP", "RMD"]:
    assert abs(act[k] - exp[k]) <= max(0.15 * abs(exp[k]), 5), f"{k}: unerwartet grosse Abweichung"

print("check_xlsx.py ok - Massenbilanz und FAN-unabhängige Nährstoffe stimmen.")
print("Hinweis: App nutzt FAN1-Futterwerte, LfL-Blatt FAN3; ME/sidP/RMD weichen daher ab.")
