import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="MU Calculator with Sensitivity", layout="centered")

# --- Title and Formula ---
st.title("Monitor Unit (MU) Calculator with Sensitivity Analysis")

st.markdown(r"""
### MU Calculation Formula

$$
MU = \frac{Dose \ (cGy)}{Output \times MU_{Rate} \times TMR \times WF \times ISF \times TF}
$$

Where 

$$
TMR = \frac{\%DD}{100}
$$

(simplified for SSD)
---
""")

# --- Lookup Tables ---
output_factor_table = {
    5: 0.95,
    7.5: 0.98,
    10: 1.00,
    15: 1.05,
    20: 1.10,
}

percent_depth_dose = {
    "6 MV": {0: 100, 1: 99, 3: 89, 5: 83, 10: 67, 15: 52, 20: 40, 25: 30, 30: 22},
    "10 MV": {0: 100, 1: 99.5, 3: 93, 5: 89, 10: 76, 15: 63, 20: 52, 25: 42, 30: 33},
}

# --- Helper Functions ---
def interpolate_lookup(x, table):
    keys = sorted(table.keys())
    if x in table:
        return table[x]
    elif x < keys[0]:
        return table[keys[0]]
    elif x > keys[-1]:
        return table[keys[-1]]
    idx = np.searchsorted(keys, x)
    x0, x1 = keys[idx - 1], keys[idx]
    y0, y1 = table[x0], table[x1]
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

def lookup_output_factor(field_size):
    return interpolate_lookup(field_size, output_factor_table)

def lookup_percent_dd(energy, depth):
    return interpolate_lookup(depth, percent_depth_dose[energy])

def calc_mu(dose, field_size, mu_rate, energy, depth, wf, isf, tf):
    output_factor = lookup_output_factor(field_size)
    percent_dd = lookup_percent_dd(energy, depth)
    tmr = percent_dd / 100
    denom = output_factor * mu_rate * tmr * wf * isf * tf
    if denom == 0:
        return None
    return dose / denom

# --- Default Values ---
baseline_inputs = {
    "dose": 200.0,
    "field_size": 10.0,
    "mu_rate": 100.0,
    "energy": "6 MV",
    "depth": 5.0,
    "wf": 1.0,
    "isf": 1.0,
    "tf": 1.0,
}

increments = {
    "dose": 10.0,
    "field_size": 1.0,
    "mu_rate": 5.0,
    "depth": 0.5,
    "wf": 0.05,
    "isf": 0.05,
    "tf": 0.05,
}

def sensitivity_percent_change(var_name, inputs, increment):
    base_mu = calc_mu(**inputs)
    if base_mu is None or base_mu == 0:
        return None, None
    up = inputs.copy()
    down = inputs.copy()
    up[var_name] += increment
    down[var_name] = max(0.01, inputs[var_name] - increment)
    mu_up = calc_mu(**up)
    mu_down = calc_mu(**down)
    if mu_up is None or mu_down is None:
        return None, None
    return 100 * (mu_up - base_mu) / base_mu, 100 * (mu_down - base_mu) / base_mu

# --- User Input UI ---
user_inputs = {}
variables = [
    ("dose", "Prescribed Dose (cGy)", 1.0),
    ("field_size", "Field Size (cm)", 0.1),
    ("mu_rate", "Machine Output Rate (cGy/MU)", 1.0),
    ("depth", "Depth (cm)", 0.1),
    ("wf", "Wedge Factor (WF)", 0.01),
    ("isf", "Inverse Square Factor (ISF)", 0.01),
    ("tf", "Tray Factor (TF)", 0.01),
]

for var_key, label, step in variables:
    inc = increments[var_key]
    up_pct, down_pct = sensitivity_percent_change(var_key, baseline_inputs, inc)
    help_text = (
        f"Increasing by {inc} → MU {up_pct:+.2f}%, "
        f"decreasing by {inc} → MU {down_pct:+.2f}%"
    ) if up_pct is not None else "Sensitivity not available"
    
    user_inputs[var_key] = st.number_input(label, value=baseline_inputs[var_key], step=step, help=help_text)

user_inputs["energy"] = st.selectbox("Beam Energy", list(percent_depth_dose.keys()), help="Affects %DD and TMR.")

# --- MU Calculation ---
mu_result = calc_mu(
    user_inputs["dose"],
    user_inputs["field_size"],
    user_inputs["mu_rate"],
    user_inputs["energy"],
    user_inputs["depth"],
    user_inputs["wf"],
    user_inputs["isf"],
    user_inputs["tf"],
)

st.markdown("---")

if mu_result is None:
    st.error("Invalid inputs. Cannot calculate MU.")
else:
    st.success(f"### Calculated MU: {mu_result:.2f}")

# --- Lookup Diagnostics ---
output_factor = lookup_output_factor(user_inputs["field_size"])
percent_dd = lookup_percent_dd(user_inputs["energy"], user_inputs["depth"])
tmr = percent_dd / 100

st.write("#### Lookup Values Used")
st.write(f"**Output Factor (interpolated):** {output_factor:.3f}")
st.write(f"**%DD at {user_inputs['depth']} cm ({user_inputs['energy']}):** {percent_dd:.1f}%")
st.write(f"**Converted TMR:** {tmr:.3f}")

# --- Sensitivity Chart ---
st.markdown("---")
st.subheader("Visualize MU vs. Single Variable")

var_to_plot = st.selectbox("Choose variable to vary for plotting", list(increments.keys()))
plot_range = {
    "dose": np.linspace(100, 300, 50),
    "field_size": np.linspace(5, 20, 50),
    "mu_rate": np.linspace(50, 150, 50),
    "depth": np.linspace(0, 30, 50),
    "wf": np.linspace(0.5, 1.5, 50),
    "isf": np.linspace(0.7, 1.3, 50),
    "tf": np.linspace(0.7, 1.3, 50),
}[var_to_plot]

plot_inputs = user_inputs.copy()
plot_values = []

for x in plot_range:
    plot_inputs[var_to_plot] = x
    mu_val = calc_mu(
        plot_inputs["dose"],
        plot_inputs["field_size"],
        plot_inputs["mu_rate"],
        plot_inputs["energy"],
        plot_inputs["depth"],
        plot_inputs["wf"],
        plot_inputs["isf"],
        plot_inputs["tf"]
    )
    plot_values.append(mu_val if mu_val else np.nan)

# --- Plotting ---
df_plot = pd.DataFrame({var_to_plot: plot_range, "MU": plot_values}).set_index(var_to_plot)
st.line_chart(df_plot)
