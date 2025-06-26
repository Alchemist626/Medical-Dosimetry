import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Set page config
st.set_page_config(page_title="Medical Physics Toolkit", layout="centered")

# Session state setup
if "page" not in st.session_state:
    st.session_state.page = "home"

# ---------- HOME SCREEN ----------
def home_screen():
    st.title("📱 Medical Physics Toolkit")
    st.markdown("### Select a Calculator")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💻 MU Calculator", use_container_width=True):
            st.session_state.page = "mu_calculator"

# ---------- MU CALCULATOR ----------
def mu_calculator():
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
    SAD_DEFAULT = 100.0

    output_factor_table = {
        5: 0.95, 7.5: 0.98, 10: 1.00, 15: 1.05, 20: 1.10,
    }

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

    wedge_factors = {0: 1.00, 15: 0.98, 30: 0.96, 45: 0.94, 60: 0.92}

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
        if field_size <= fs_list[0]:
            lower_fs = upper_fs = fs_list[0]
        elif field_size >= fs_list[-1]:
            lower_fs = upper_fs = fs_list[-1]
        else:
            for i in range(1, len(fs_list)):
                if field_size < fs_list[i]:
                    lower_fs, upper_fs = fs_list[i-1], fs_list[i]
                    break
        lower_dd = interpolate_lookup(depth, percent_depth_dose[energy][lower_fs])
        upper_dd = interpolate_lookup(depth, percent_depth_dose[energy][upper_fs])
        return lower_dd if lower_fs == upper_fs else lower_dd + (field_size - lower_fs) * (upper_dd - lower_dd) / (upper_fs - lower_fs)

    def lookup_output_factor(field_size):
        return interpolate_lookup(field_size, output_factor_table)

    def lookup_wedge_factor(angle):
        return interpolate_lookup(angle, wedge_factors)

    def calc_tmr(percent_dd, depth, geometry, SSD_input, SAD=SAD_DEFAULT):
        if geometry == "SSD":
            return (percent_dd / 100) * ((SSD_input + depth) / SAD) ** 2
        return percent_dd / 100

    def calc_mu(dose, field_size, mu_rate, tmr, wf, isf, tf):
        denom = lookup_output_factor(field_size) * mu_rate * tmr * wf * isf * tf
        return None if denom == 0 else dose / denom

    st.subheader("Geometry & Energy Setup")
    geometry = st.radio("Select Geometry Setup", ["SAD (Isocentric)", "SSD (Fixed SSD)"])
    geometry_short = "SSD" if "SSD" in geometry else "SAD"
    SSD_input = st.number_input("SSD (cm)", value=95.0, step=0.5) if geometry_short == "SSD" else None
    st.write(f"**SAD (fixed):** {SAD_DEFAULT} cm")
    energy = st.selectbox("Beam Energy", list(percent_depth_dose.keys()))

    st.subheader("Optional Corrections")
    wedge_used = st.radio("Apply Wedge?", ["No", "Yes"])
    wedge_angle = 0
    wf = 1.0
    decoupled_wedge = False
    if wedge_used == "Yes":
        col1, col2 = st.columns([3, 3])
        wedge_options = [f"{angle}° ({wedge_factors[angle]:.2f})" for angle in sorted(wedge_factors.keys())]
        with col1:
            wedge_choice = st.selectbox("Wedge Angle (with Factor)", wedge_options)
            wedge_angle = int(wedge_choice.split("°")[0])
        with col2:
            decoupled_wedge = st.checkbox("Decouple Wedge Inputs?")
            wf = st.number_input("Wedge Factor (manual)", min_value=0.5, max_value=1.0, value=lookup_wedge_factor(wedge_angle), step=0.001) if decoupled_wedge else lookup_wedge_factor(wedge_angle)

    bolus_used = st.checkbox("Apply Bolus?")
    bolus_thickness = st.number_input("Bolus Thickness (cm)", min_value=0.0, value=0.5, step=0.1) if bolus_used else 0.0

    st.subheader("Input Parameters")
    baseline_inputs = {
        "dose": 200.0,
        "field_size": 10.0,
        "mu_rate": 100.0,
        "depth": 5.0,
        "isf": 1.0,
        "tf": 1.0,
    }
    increments = {
        "dose": 10.0,
        "field_size": 1.0,
        "mu_rate": 5.0,
        "depth": 0.5,
        "isf": 0.05,
        "tf": 0.05,
    }

    def sensitivity(var, inputs, inc, energy, geometry, SSD_input, bolus, wf):
        eff_depth = inputs["depth"] + bolus
        percent_dd = lookup_percent_dd(energy, inputs["field_size"], eff_depth)
        tmr = calc_tmr(percent_dd, eff_depth, geometry, SSD_input)
        base_mu = calc_mu(inputs["dose"], inputs["field_size"], inputs["mu_rate"], tmr, wf, inputs["isf"], inputs["tf"])
        if not base_mu:
            return None, None
        up, down = inputs.copy(), inputs.copy()
        up[var] += inc
        down[var] = max(0.01, inputs[var] - inc)
        for d in [up, down]:
            eff_d = d["depth"] + bolus
            dd = lookup_percent_dd(energy, d["field_size"], eff_d)
            tmr_d = calc_tmr(dd, eff_d, geometry, SSD_input)
            d["mu"] = calc_mu(d["dose"], d["field_size"], d["mu_rate"], tmr_d, wf, d["isf"], d["tf"])
        return ((up["mu"] - base_mu) / base_mu) * 100, ((down["mu"] - base_mu) / base_mu) * 100

    user_inputs = {}
    for key in baseline_inputs:
        inc = increments[key]
        up_pct, down_pct = sensitivity(key, baseline_inputs, inc, energy, geometry_short, SSD_input, bolus_thickness, wf)
        help_text = f"↑{inc} → MU {up_pct:+.1f}%, ↓{inc} → MU {down_pct:+.1f}%" if up_pct else "N/A"
        user_inputs[key] = st.number_input(
            key.replace("_", " ").capitalize(),
            value=baseline_inputs[key],
            step=inc / 10,
            help=help_text
        )

    st.markdown("---")
    st.subheader("Dose Calculation Parameters")
    effective_depth = user_inputs["depth"] + bolus_thickness
    percent_dd_display = lookup_percent_dd(energy, user_inputs["field_size"], effective_depth)
    st.write(f"**Effective Depth:** {effective_depth:.2f} cm")
    st.write(f"**%DD:** {percent_dd_display:.1f}% at {effective_depth:.1f} cm for {energy}")
    st.write(f"**Wedge Factor:** {wf:.3f}")
    st.write(f"**Bolus Thickness:** {bolus_thickness:.2f} cm")

    tmr = calc_tmr(percent_dd_display, effective_depth, geometry_short, SSD_input)
    mu = calc_mu(user_inputs["dose"], user_inputs["field_size"], user_inputs["mu_rate"], tmr, wf, user_inputs["isf"], user_inputs["tf"])
    st.markdown("---")
    st.success(f"### Calculated MU: {mu:.2f}" if mu else "Invalid parameters.")

    st.markdown("---")
    st.subheader("MU Sensitivity Plot")
    var_to_plot = st.selectbox("Plot MU vs", list(baseline_inputs.keys()))
    plot_range = {
        "dose": np.linspace(100, 300, 50),
        "field_size": np.linspace(5, 20, 50),
        "mu_rate": np.linspace(50, 150, 50),
        "depth": np.linspace(0, 30, 50),
        "isf": np.linspace(0.7, 1.3, 50),
        "tf": np.linspace(0.7, 1.3, 50),
    }[var_to_plot]
    mu_vals = []
    for val in plot_range:
        trial = user_inputs.copy()
        trial[var_to_plot] = val
        eff_depth = trial["depth"] + bolus_thickness
        dd = lookup_percent_dd(energy, trial["field_size"], eff_depth)
        tmr = calc_tmr(dd, eff_depth, geometry_short, SSD_input)
        mu_trial = calc_mu(trial["dose"], trial["field_size"], trial["mu_rate"], tmr, wf, trial["isf"], trial["tf"])
        mu_vals.append(mu_trial if mu_trial else np.nan)
    fig, ax = plt.subplots()
    ax.plot(plot_range, mu_vals, label="MU", color='blue')
    ax.set_title(f"MU Sensitivity vs {var_to_plot.replace('_', ' ').capitalize()}")
    ax.set_xlabel(var_to_plot.replace('_', ' ').capitalize())
    ax.set_ylabel("Monitor Units (MU)")
    ax.grid(True)
    st.pyplot(fig)

    st.markdown("---")
    if st.button("🔙 Back to Home"):
        st.session_state.page = "home"

# ---------- PAGE SELECTOR ----------
if st.session_state.page == "home":
    home_screen()
elif st.session_state.page == "mu_calculator":
    mu_calculator()
