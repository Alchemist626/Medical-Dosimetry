import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="MU Calculator with Field Size in %DD", layout="centered")

st.title("Monitor Unit (MU) Calculator")

st.markdown(r"""
### MU Calculation Formula

$$
MU = \frac{Dose \ (cGy)}{Output \times MU_{Rate} \times TMR \times WF \times ISF \times TF}
$$

Where

$$
TMR = \frac{\%DD}{100} \times \left(\frac{SSD + d}{SAD}\right)^2 \quad \text{(if SSD geometry)}
$$

or

$$
TMR = \frac{\%DD}{100} \quad \text{(if SAD geometry)}
$$
---
""")

# Constants
SAD_DEFAULT = 100.0  # cm

# Lookup Tables
output_factor_table = {
    5: 0.95, 7.5: 0.98, 10: 1.00, 15: 1.05, 20: 1.10,
}

# %DD table indexed by energy -> field size -> depth (cm)
percent_depth_dose = {
    "6 MV": {
        5: {0: 100, 1: 98, 3: 88, 5: 82, 10: 65, 15: 50, 20: 40},
        10: {0: 100, 1: 99, 3: 89, 5: 83, 10: 67, 15: 52, 20: 40},
        20: {0: 100, 1: 100, 3: 90, 5: 85, 10: 70, 15: 55, 20: 45},
    },
    "10 MV": {
        5: {0: 100, 1: 99, 3: 92, 5: 86, 10: 75, 15: 60, 20: 50},
        10: {0: 100, 1: 99.5, 3: 93, 5: 89, 10: 76, 15: 63, 20: 52},
        20: {0: 100, 1: 100, 3: 95, 5: 90, 10: 80, 15: 68, 20: 58},
    }
}

# Helper functions
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

def lookup_percent_dd(energy, field_size, depth):
    fs_list = sorted(percent_depth_dose[energy].keys())
    # Clamp field size within table bounds
    if field_size <= fs_list[0]:
        lower_fs = upper_fs = fs_list[0]
    elif field_size >= fs_list[-1]:
        lower_fs = upper_fs = fs_list[-1]
    else:
        for i in range(1, len(fs_list)):
            if field_size < fs_list[i]:
                lower_fs, upper_fs = fs_list[i-1], fs_list[i]
                break
    
    # Interpolate %DD for depth at both field sizes
    lower_dd = interpolate_lookup(depth, percent_depth_dose[energy][lower_fs])
    upper_dd = interpolate_lookup(depth, percent_depth_dose[energy][upper_fs])
    
    # Interpolate over field size
    if lower_fs == upper_fs:
        return lower_dd
    else:
        return lower_dd + (field_size - lower_fs) * (upper_dd - lower_dd) / (upper_fs - lower_fs)

def lookup_output_factor(field_size):
    return interpolate_lookup(field_size, output_factor_table)

def calc_tmr(percent_dd, depth, geometry, SSD_input, SAD=SAD_DEFAULT):
    if geometry == "SSD":
        return (percent_dd / 100) * ((SSD_input + depth) / SAD) ** 2
    return percent_dd / 100

def calc_mu(dose, field_size, mu_rate, tmr, wf, isf, tf):
    denom = lookup_output_factor(field_size) * mu_rate * tmr * wf * isf * tf
    if denom == 0:
        return None
    return dose / denom

# Geometry and energy setup
st.subheader("Geometry & Energy Setup")

geometry = st.radio("Select Geometry Setup", ["SAD (Isocentric)", "SSD (Fixed SSD)"])
geometry_short = "SSD" if "SSD" in geometry else "SAD"

SSD_input = None
if geometry_short == "SSD":
    SSD_input = st.number_input("SSD (cm)", value=95.0, step=0.5)

st.write(f"**SAD (fixed):** {SAD_DEFAULT} cm")

energy = st.selectbox("Beam Energy", list(percent_depth_dose.keys()))

# Input parameters
st.subheader("Input Parameters")

baseline_inputs = {
    "dose": 200.0,
    "field_size": 10.0,
    "mu_rate": 100.0,
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

def sensitivity(var_name, inputs, inc, energy, geometry, SSD_input):
    percent_dd = lookup_percent_dd(energy, inputs["field_size"], inputs["depth"])
    tmr = calc_tmr(percent_dd, inputs["depth"], geometry, SSD_input)
    base_mu = calc_mu(inputs["dose"], inputs["field_size"], inputs["mu_rate"], tmr,
                      inputs["wf"], inputs["isf"], inputs["tf"])
    if not base_mu:
        return None, None
    up, down = inputs.copy(), inputs.copy()
    up[var_name] += inc
    down[var_name] = max(0.01, inputs[var_name] - inc)
    for d in [up, down]:
        percent_dd = lookup_percent_dd(energy, d["field_size"], d["depth"])
        tmr_d = calc_tmr(percent_dd, d["depth"], geometry, SSD_input)
        d["mu"] = calc_mu(d["dose"], d["field_size"], d["mu_rate"], tmr_d,
                          d["wf"], d["isf"], d["tf"])
    return ((up["mu"] - base_mu) / base_mu) * 100, ((down["mu"] - base_mu) / base_mu) * 100

user_inputs = {}
for key in baseline_inputs:
    inc = increments[key]
    up_pct, down_pct = sensitivity(key, baseline_inputs, inc, energy, geometry_short, SSD_input)
    help_text = f"Increase by {inc} → MU {up_pct:+.1f}%, decrease by {inc} → MU {down_pct:+.1f}%" if up_pct else "N/A"
    user_inputs[key] = st.number_input(
        key.replace("_", " ").capitalize(),
        value=baseline_inputs[key],
        step=inc / 10,
        help=help_text
    )

# Display calculation parameters
st.markdown("---")
st.subheader("Dose Calculation Parameters")

if geometry_short == "SSD":
    st.write(f"**SSD:** {SSD_input:.1f} cm")
else:
    st.write("**SSD:** Not applicable (using SAD geometry)")

st.write(f"**SAD:** {SAD_DEFAULT} cm (fixed)")

percent_dd_display = lookup_percent_dd(energy, user_inputs["field_size"], user_inputs["depth"])
st.write(f"**Percent Depth Dose (%DD) at {user_inputs['depth']:.1f} cm for {energy} with field size {user_inputs['field_size']:.1f} cm:** {percent_dd_display:.1f}%")

tmr = calc_tmr(percent_dd_display, user_inputs["depth"], geometry_short, SSD_input)
mu = calc_mu(user_inputs["dose"], user_inputs["field_size"], user_inputs["mu_rate"], tmr,
             user_inputs["wf"], user_inputs["isf"], user_inputs["tf"])

st.markdown("---")
if mu is None:
    st.error("Invalid parameters for MU calculation.")
else:
    st.success(f"### Calculated MU: {mu:.2f}")

# Sensitivity plot
st.markdown("---")
st.subheader("MU Sensitivity Plot")

var_to_plot = st.selectbox("Plot MU vs", list(baseline_inputs.keys()))
plot_range = {
    "dose": np.linspace(100, 300, 50),
    "field_size": np.linspace(5, 20, 50),
    "mu_rate": np.linspace(50, 150, 50),
    "depth": np.linspace(0, 30, 50),
    "wf": np.linspace(0.5, 1.5, 50),
    "isf": np.linspace(0.7, 1.3, 50),
    "tf": np.linspace(0.7, 1.3, 50),
}[var_to_plot]

mu_vals = []
for val in plot_range:
    trial = user_inputs.copy()
    trial[var_to_plot] = val
    percent_dd = lookup_percent_dd(energy, trial["field_size"], trial["depth"])
    tmr = calc_tmr(percent_dd, trial["depth"], geometry_short, SSD_input)
    mu_trial = calc_mu(trial["dose"], trial["field_size"], trial["mu_rate"], tmr,
                       trial["wf"], trial["isf"], trial["tf"])
    mu_vals.append(mu_trial if mu_trial else np.nan)

# Display actual values used for the sensitivity plot
st.markdown("#### Parameters Used for Sensitivity Plot")
st.code(
    "\n".join([
        f"{k.replace('_',' ').capitalize()}: {v:.2f}" if k != var_to_plot else f"{k.replace('_',' ').capitalize()}: varied"
        for k, v in user_inputs.items()
    ]) + (
        f"\nGeometry: {geometry_short}\n"
        + (f"SSD: {SSD_input:.1f} cm" if geometry_short == "SSD" else "SSD: N/A") + 
        f"\nEnergy: {energy}"
    ),
    language="yaml"
)

fig, ax = plt.subplots()
ax.plot(plot_range, mu_vals, label="MU", color='blue')
ax.set_title(f"MU Sensitivity vs {var_to_plot.replace('_', ' ').capitalize()}", fontsize=14)
ax.set_xlabel(f"{var_to_plot.replace('_', ' ').capitalize()}", fontsize=12)
ax.set_ylabel("Monitor Units (MU)", fontsize=12)
ax.grid(True)
st.pyplot(fig)
