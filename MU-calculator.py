import streamlit as st

st.title("MU Sanity Check Calculator")

st.markdown("""
Calculate the Monitor Units (MU) needed to deliver a prescribed dose given field size, depth, SSD, and machine calibration.
""")

# User inputs
prescribed_dose = st.number_input("Prescribed Dose (cGy)", min_value=0.0, value=200.0, step=1.0)
field_size = st.number_input("Field Size (cm, single dimension)", min_value=1.0, value=10.0, step=0.1)
depth = st.number_input("Depth in patient (cm)", min_value=0.0, value=10.0, step=0.1)
ssd = st.number_input("Source to Surface Distance (SSD) (cm)", min_value=50.0, value=100.0, step=0.1)
calibration_factor = st.number_input("Calibration Factor (cGy/MU)", min_value=0.01, value=1.0, step=0.01)

# Lookup tables (simple linear interpolation functions)
def get_output_factor(field_size_cm):
    of_table = {
        4: 0.95,
        6: 0.97,
        10: 1.00,
        15: 1.03,
        20: 1.05,
    }
    sizes = sorted(of_table.keys())
    if field_size_cm <= sizes[0]:
        return of_table[sizes[0]]
    if field_size_cm >= sizes[-1]:
        return of_table[sizes[-1]]
    for i in range(len(sizes)-1):
        if sizes[i] <= field_size_cm <= sizes[i+1]:
            f1, f2 = sizes[i], sizes[i+1]
            of1, of2 = of_table[f1], of_table[f2]
            return of1 + (field_size_cm - f1) * (of2 - of1) / (f2 - f1)

def get_pdd(depth_cm):
    pdd_table = {
        1: 0.98,
        5: 0.85,
        10: 0.70,
        15: 0.55,
        20: 0.43,
    }
    depths = sorted(pdd_table.keys())
    if depth_cm <= depths[0]:
        return pdd_table[depths[0]]
    if depth_cm >= depths[-1]:
        return pdd_table[depths[-1]]
    for i in range(len(depths)-1):
        if depths[i] <= depth_cm <= depths[i+1]:
            d1, d2 = depths[i], depths[i+1]
            pdd1, pdd2 = pdd_table[d1], pdd_table[d2]
            return pdd1 + (depth_cm - d1) * (pdd2 - pdd1) / (d2 - d1)

def inverse_square_factor(ssd, depth, dmax=1.5):
    return ((ssd + dmax) / (ssd + depth)) ** 2

# Calculate MU
of = get_output_factor(field_size)
pdd = get_pdd(depth)
isf = inverse_square_factor(ssd, depth)
mu = prescribed_dose / (of * pdd * calibration_factor * isf)

st.markdown("---")
st.write(f"### Results")
st.write(f"Output Factor (OF): {of:.3f}")
st.write(f"Percent Depth Dose (PDD): {pdd:.3f}")
st.write(f"Inverse Square Factor (ISF): {isf:.3f}")
st.write(f"Estimated Monitor Units (MU): {mu:.2f}")
