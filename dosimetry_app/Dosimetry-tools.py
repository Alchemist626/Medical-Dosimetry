import streamlit as st

st.title("MU Calculator - Geometry Setup Inline")

# Geometry selection radio buttons in main page
geometry = st.radio(
    "Select Geometry Setup",
    ["SAD (Isocentric)", "SSD (Fixed SSD)"]
)

# Conditionally show SSD input inline
SSD_input = None
if "SSD" in geometry:
    SSD_input = st.number_input("SSD (cm)", value=95.0, step=0.5)

# Show SAD info (fixed)
st.write("**SAD (fixed):** 100 cm")

# Display selections
st.write(f"Geometry selected: {geometry}")
if SSD_input is not None:
    st.write(f"SSD value: {SSD_input} cm")
else:
    st.write("SSD not applicable")
