import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Streamlit Config ---
st.set_page_config(page_title="Radiation Dosimetry Toolkit", layout="centered")

# --- Session State Navigation ---
if "page" not in st.session_state:
    st.session_state.page = "home"

def go_to(page_name):
    st.session_state.page = page_name

# --- HOMEPAGE ---
if st.session_state.page == "home":
    st.title("🧮 Radiation Dosimetry Toolkit")
    st.markdown("Choose a calculator:")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📟 MU Calculator", use_container_width=True):
            go_to("mu")
    with col2:
        if st.button("💡 TMR Lookup", use_container_width=True):
            go_to("tmr")

    st.divider()
    st.caption("More calculators coming soon: CI/HI, Gradient Index, Coverage...")

# --- MU CALCULATOR ---
elif st.session_state.page == "mu":
    st.title("📟 MU Calculator")
    st.button("⬅ Back to Home", on_click=lambda: go_to("home"))

    # --- Constants ---
    SAD_DEFAULT = 100.0  # cm

    # --- Lookup Tables ---
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

    # --- Helper functions ---
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
        lower_fs = max([fs for fs in fs_list if fs <= field_size], default=fs_list[0])
        upper_fs = min([fs for fs in fs_list if fs >= field_size], default=fs_list[-1])
        lower_dd = interpolate_lookup(depth, percent_depth_dose[energy][lower_fs])
        upper_dd = interpolate_lookup(depth, percent_depth_dose[energy][upper_fs])
        if lower_fs == upper_fs:
            return lower_dd
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

    # --- Geometry and Energy ---
    st.subheader("Geometry & Energy Setup")
    geometry = st.radio("Select Geometry Setup", ["SAD (Isocentric)", "SSD (Fixed SSD)"])
    geometry_short = "SSD" if "SSD" in geometry else "SAD"

    SSD_input = None
    if geometry_short == "SSD":
        SSD_input = st.number_input("SSD (cm)", value=95.0, step=0.5)

    st.write(f"**SAD (fixed):** {SAD_DEFAULT} cm")
    energy = st.selectbox("Beam Energy", list(percent_depth_dose.keys()))

    # --- Input Parameters ---
    st.subheader("Input Parameters")
    dose = st.number_input("Prescribed Dose (cGy)", value=200.0, step=5.0)
    field_size = st.number_input("Field Size (cm)", value=10.0, step=0.5)
    mu_rate = st.number_input("MU Rate", value=100.0, step=5.0)
    depth = st.number_input("Depth (cm)", value=5.0, step=0.5)
    wf = st.number_input("Wedge Factor", value=1.0, step=0.01)
    isf = st.number_input("Inverse Square Factor", value=1.0, step=0.01)
    tf = st.number_input("Tray Factor", value=1.0, step=0.01)

    # --- Calculations ---
    percent_dd_display = lookup_percent_dd(energy, field_size, depth)
    tmr = calc_tmr(percent_dd_display, depth, geometry_short, SSD_input)
    mu = calc_mu(dose, field_size, mu_rate, tmr, wf, isf, tf)

    # --- Results ---
    st.markdown("---")
    st.subheader("Dose Calculation Parameters")
    st.write(f"**SSD:** {SSD_input:.1f} cm" if geometry_short == "SSD" else "**SSD:** Not applicable")
    st.write(f"**SAD:** {SAD_DEFAULT} cm")
    st.write(f"**Percent Depth Dose (%DD):** {percent_dd_display:.1f}% at {depth:.1f} cm for {energy} and {field_size:.1f}×{field_size:.1f} cm field")

    if mu is None:
        st.error("Invalid input values for MU calculation.")
    else:
        st.success(f"### Calculated MU: {mu:.2f}")

# --- TMR Lookup Tool Placeholder ---
elif st.session_state.page == "tmr":
    st.title("💡 TMR Lookup Tool")
    st.button("⬅ Back to Home", on_click=lambda: go_to("home"))
    st.info("This tool is coming soon.")
