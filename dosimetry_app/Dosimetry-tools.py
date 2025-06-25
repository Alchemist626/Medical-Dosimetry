import streamlit as st
import numpy as np

st.title("Monitor Unit(MU) Calculator")

# Show MU formula with LaTeX
st.markdown("""
### MU Calculation Formula

$$
MU = \\frac{Dose \\, (cGy)}{Output \\, Factor \\, \\times \\, MU_{Rate} \\, \\times \\, TMR \\, \\times \\, WF \\, \\times \\, ISF \\, \\times \\, TF}
$$

Where:
- \( Dose \) = Prescribed dose in cGy  
- \( Output \, Factor \) = Output factor from lookup  
- \( MU_{Rate} \) = Machine output rate (cGy/MU)  
- \( TMR \) = Tissue Maximum Ratio  
- \( WF \) = Wedge Factor  
- \( ISF \) = Inverse Square Factor  
- \( TF \) = Tray Factor  
""")

# Sample lookup table for Output Factor (field size in cm): just example values
output_factor_table = {
    5: 0.95,
    7.5: 0.98,
    10: 1.0,
    15: 1.05,
    20: 1.10,
}

def lookup_output_factor(field_size):
    sizes = np.array(sorted(output_factor_table.keys()))
    factors = np.array([output_factor_table[size] for size in sizes])
    if field_size in output_factor_table:
        return output_factor_table[field_size]
    elif field_size < sizes[0]:
        return factors[0]
    elif field_size > sizes[-1]:
        return factors[-1]
    else:
        # Linear interpolation
        idx = np.searchsorted(sizes, field_size)  # index where field_size would go
        x0, x1 = sizes[idx-1], sizes[idx]
        y0, y1 = factors[idx-1], factors[idx]
        return y0 + (field_size - x0) * (y1 - y0) / (x1 - x0)

# User inputs
dose = st.number_input("Dose (cGy)", value=200.0, step=1.0)
field_size = st.number_input("Field Size (cm)", value=7.5, step=0.1, format="%.2f")
MU_rate = st.number_input("Machine Output Rate (cGy/MU)", value=100.0, step=1.0)
TMR = st.number_input("Tissue Maximum Ratio (TMR)", value=1.0, step=0.01, format="%.3f")
WF = st.number_input("Wedge Factor (WF)", value=1.0, step=0.01, format="%.3f")
ISF = st.number_input("Inverse Square Factor (ISF)", value=1.0, step=0.01, format="%.3f")
TF = st.number_input("Tray Factor (TF)", value=1.0, step=0.01, format="%.3f")

output_factor = lookup_output_factor(field_size)

if MU_rate * TMR * WF * ISF * TF * output_factor == 0:
    st.error("One or more factors are zero, cannot calculate MU.")
else:
    MU = dose / (output_factor * MU_rate * TMR * WF * ISF * TF)
    st.write(f"### Calculated MU: {MU:.2f}")

# Show the output factor used
st.write(f"Using Output Factor (from lookup/interpolation): {output_factor:.3f}")
