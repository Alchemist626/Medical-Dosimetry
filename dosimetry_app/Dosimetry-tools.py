import streamlit as st
import numpy as np

st.title("Monitor Unit (MU) Calculator with %DD Lookup")

st.markdown("""
### MU Calculation Formula

$$
MU = \\frac{Dose \\, (cGy)}{Output \\times MU_{Rate} \\times TMR \\times WF \\times ISF \\times TF}
$$

Where \( TMR = \\frac{\\%DD}{100} \) (simplified for SSD)

---
""")

# === Output Factor Lookup Table ===
output_factor_table = {
    5: 0.95,
    7.5: 0.98,
    10: 1.00,
    15: 1.05,
    20: 1.10,
}

# === Percent Depth Dose Table ===
percent_depth_dose = {
    "6 MV": {
        0: 100, 1: 99, 3: 89, 5: 83, 10: 67,
        15: 52, 20: 40, 25: 30, 30: 22
    },
    "10 MV": {
        0: 100, 1: 99.5, 3: 93, 5: 89, 10: 76,
        15: 63, 20: 52, 25: 42, 30: 33
    }
}

def interpolate_lookup(x, table):
    keys = sorted(table.keys())
    values = [table[k] for k in keys]
    if x in table:
        return table[x]
    elif x < keys[0]:
        return values[0]
    elif x > keys[-1]:
        return values[-1]
    else:
        idx = np.searchsorted(keys, x)
        x0, x1 = keys[idx - 1], keys[idx]
        y0, y1 = table[x0], table[x1]
        return y0 + (x - x0) * (y1 - y0) / (x1 - y0)

def lookup_output_factor(field_size):
    return interpolate_lookup(field_size, output_factor_table)

def lookup_percent_dd(energy, depth):
    return interpolate_lookup(depth, percent_depth_dose[energy])

# === User Inputs ===
dose = st.number_input("Prescribed Dose (cGy)", value=200.0, step=1.0)
field_size = st.number_input("Field Size (cm)", value=10.0, step=0.1)
mu_rate = st.number_input("Machine Output Rate (cGy/MU)", value=100.0, step=1.0)

energy = st.selectbox("Beam Energy", list(percent_depth_dose.keys()))
depth = st.number_input("Depth (cm)", value=5.0, step=0.1)

wf = st.number_input("Wedge Factor (WF)", value=1.0, step=0.01)
isf = st.number_input("Inverse Square Factor (ISF)", value=1.0, step=0.01)
tf = st.number_input("Tray Factor (TF)", value=1.0, step=0.01)

# === Lookups ===
output_factor = lookup_output_factor(field_size)
percent_dd = lookup_percent_dd(energy, depth)
tmr = percent_dd / 100

# === Calculation ===
if mu_rate * tmr * wf * isf * tf * output_factor == 0:
    st.error("One or more values are zero. Cannot calculate MU.")
else:
    mu = dose / (output_factor * mu_rate * tmr * wf * isf * tf)
    st.success(f"### Calculated MU: {mu:.2f}")

# === Diagnostics ===
st.write("---")
st.subheader("Lookup Values Used")
st.write(f"**Output Factor (interpolated):** {output_factor:.3f}")
st.write(f"**%DD at {depth} cm for {energy}:** {percent_dd:.1f}%")
st.write(f"**Converted TMR:** {tmr:.3f}")
