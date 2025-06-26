import streamlit as st
import numpy as np

st.title("Monitor Unit (MU) Calculator with Step-by-Step Output")

# === MU Formula ===
st.markdown(r"""
### MU Calculation Formula

$$
MU = \frac{Dose \, (cGy)}{Output \, Factor \times MU_{Rate} \times TMR \times WF \times ISF \times TF}
$$

Where:
- \( \text{Dose} \) = Prescribed dose in cGy  
- \( \text{Output Factor} \) = Based on field size (lookup + interpolation)  
- \( \text{MU Rate} \) = Machine output rate in cGy/MU  
- \( \text{TMR} \) = Tissue Maximum Ratio  
- \( \text{WF} \) = Wedge Factor  
- \( \text{ISF} \) = Inverse Square Factor  
- \( \text{TF} \) = Tray Factor  
""")

# === Output Factor Lookup Table ===
output_factor_table = {
    5: 0.95,
    7.5: 0.98,
    10: 1.00,
    15: 1.05,
    20: 1.10,
}

def interpolate_output_factor(field_size):
    sizes = np.array(sorted(output_factor_table.keys()))
    factors = np.array([output_factor_table[size] for size in sizes])
    if field_size in output_factor_table:
        return output_factor_table[field_size], f"Exact match for {field_size} cm"
    elif field_size < sizes[0]:
        return factors[0], f"Below minimum field size, using {sizes[0]} cm: {factors[0]}"
    elif field_size > sizes[-1]:
        return factors[-1], f"Above maximum field size, using {sizes[-1]} cm: {factors[-1]}"
    else:
        idx = np.searchsorted(sizes, field_size)
        x0, x1 = sizes[idx - 1], sizes[idx]
        y0, y1 = factors[idx - 1], factors[idx]
        interp = y0 + (field_size - x0) * (y1 - y0) / (x1 - x0)
        debug = f"Interpolated between {x0}cm ({y0}) and {x1}cm ({y1}) → {interp:.4f}"
        return interp, debug

# === User Inputs ===
st.sidebar.header("Input Parameters")

dose = st.sidebar.number_input("Prescribed Dose (cGy)", value=200.0, step=1.0)
field_size = st.sidebar.number_input("Field Size (cm)", value=7.5, step=0.1, format="%.2f")
mu_rate = st.sidebar.number_input("Machine Output Rate (cGy/MU)", value=100.0, step=1.0)
tmr = st.sidebar.number_input("Tissue Maximum Ratio (TMR)", value=1.0, step=0.01, format="%.3f")
wf = st.sidebar.number_input("Wedge Factor (WF)", value=1.0, step=0.01, format="%.3f")
isf = st.sidebar.number_input("Inverse Square Factor (ISF)", value=1.0, step=0.01, format="%.3f")
tf = st.sidebar.number_input("Tray Factor (TF)", value=1.0, step=0.01, format="%.3f")

# === Lookup Output Factor ===
output_factor, interp_debug = interpolate_output_factor(field_size)

# === Display Inputs and Debug Info ===
st.markdown("### Step-by-Step Breakdown")
st.write(f"**Prescribed Dose:** {dose:.2f} cGy")
st.write(f"**Field Size:** {field_size:.2f} cm")
st.write(f"**Output Factor:** {output_factor:.4f} ({interp_debug})")
st.write(f"**Machine Output Rate:** {mu_rate:.2f} cGy/MU")
st.write(f"**TMR:** {tmr:.3f}")
st.write(f"**WF:** {wf:.3f}")
st.write(f"**ISF:** {isf:.3f}")
st.write(f"**TF:** {tf:.3f}")

denominator = output_factor * mu_rate * tmr * wf * isf * tf

if denominator == 0:
    st.error("One or more input factors are zero — cannot calculate MU.")
else:
    mu = dose / denominator
    st.success(f"### Calculated MU: {mu:.2f}")
    st.caption(f"Calculation: MU = {dose:.2f} / ({denominator:.4f})")
