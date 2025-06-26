import streamlit as st
import numpy as np

st.set_page_config(page_title="MU Calculator with Sensitivity", layout="centered")

st.title("Monitor Unit (MU) Calculator with Sensitivity Preview")

# === Lookup Tables ===
output_factor_table = {
    5: 0.95,
    7.5: 0.98,
    10: 1.00,
    15: 1.05,
    20: 1.10,
}

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

# === Baseline values for sensitivity ===
baseline_inputs = {
    "dose": 200.0,
    "field_size": 10.0,
    "mu_rate": 100.0,
    "energy": "6 MV",
    "depth": 5.0,
    "wf": 1.0,
    "isf": 1.0,
    "tf": 1.0
}

def sensitivity_for_var(var_name, baseline_inputs, percent_change=0.1):
    baseline_mu = calc_mu(**baseline_inputs)
    if baseline_mu is None:
        return None, None

    perturbed_up = baseline_inputs.copy()
    perturbed_down = baseline_inputs.copy()

    perturbed_up[var_name] = baseline_inputs[var_name] * (1 + percent_change)
    perturbed_down[var_name] = baseline_inputs[var_name] * (1 - percent_change)

    mu_up = calc_mu(**perturbed_up)
    mu_down = calc_mu(**perturbed_down)

    def pct_change(val):
        if val is None:
            return None
        return 100 * (val - baseline_mu) / baseline_mu

    return pct_change(mu_up), pct_change(mu_down)

# === UI Inputs with inline sensitivity ===

variables = [
    ("dose", "Prescribed Dose (cGy)", 1.0),
    ("field_size", "Field Size (cm)", 0.1),
    ("mu_rate", "Machine Output Rate (cGy/MU)", 1.0),
    ("depth", "Depth (cm)", 0.1),
    ("wf", "Wedge Factor (WF)", 0.01),
    ("isf", "Inverse Square Factor (ISF)", 0.01),
    ("tf", "Tray Factor (TF)", 0.01),
]

user_inputs = {}

for var_key, var_label, step_val in variables:
    up_chg, down_chg = sensitivity_for_var(var_key, baseline_inputs)
    if up_chg is not None and down_chg is not None:
        sensitivity_msg = (
            f"Changing this ±10% changes MU by about +{up_chg:.1f}% / {down_chg:.1f}%"
        )
    else:
        sensitivity_msg = "Sensitivity data not available."

    user_val = st.number_input(
        var_label,
        value=baseline_inputs[var_key],
        step=step_val,
        help=sensitivity_msg
    )
    user_inputs[var_key] = user_val

energy = st.selectbox(
    "Beam Energy",
    list(percent_depth_dose.keys()),
    index=list(percent_depth_dose.keys()).index(baseline_inputs["energy"]),
    help="Energy affects percent depth dose and beam penetration."
)

user_inputs["energy"] = energy

# === Perform calculation ===
result_mu = calc_mu(
    user_inputs["dose"],
    user_inputs["field_size"],
    user_inputs["mu_rate"],
    user_inputs["energy"],
    user_inputs["depth"],
    user_inputs["wf"],
    user_inputs["isf"],
    user_inputs["tf"]
)

if result_mu is None:
    st.error("One or more input values resulted in division by zero. Please adjust inputs.")
else:
    st.success(f"### Calculated MU: {result_mu:.2f}")

# === Show lookup values for reference ===
st.write("---")
st.subheader("Lookup Values Used")
output_factor_val = lookup_output_factor(user_inputs["field_size"])
percent_dd_val = lookup_percent_dd(user_inputs["energy"], user_inputs["depth"])
tmr_val = percent_dd_val / 100

st.write(f"**Output Factor:** {output_factor_val:.3f}")
st.write(f"**%DD at {user_inputs['depth']} cm for {user_inputs['energy']}:** {percent_dd_val:.1f}%")
st.write(f"**Converted TMR:** {tmr_val:.3f}")
