import pandas as pd
import matplotlib.pyplot as plt

st.write("---")
st.subheader("Visualize MU Sensitivity")

# Let user select a variable to explore
var_to_plot = st.selectbox("Choose a variable to vary", [
    "dose", "field_size", "mu_rate", "depth", "wf", "isf", "tf"
])

# Define plotting range for each variable
plot_ranges = {
    "dose": np.linspace(100, 300, 50),
    "field_size": np.linspace(5, 20, 50),
    "mu_rate": np.linspace(50, 150, 50),
    "depth": np.linspace(0, 30, 50),
    "wf": np.linspace(0.5, 1.5, 50),
    "isf": np.linspace(0.7, 1.3, 50),
    "tf": np.linspace(0.7, 1.3, 50),
}

x_vals = plot_ranges[var_to_plot]
mu_vals = []

# Copy user inputs for reuse
inputs = user_inputs.copy()

for val in x_vals:
    inputs[var_to_plot] = val
    mu = calc_mu(
        inputs["dose"], inputs["field_size"], inputs["mu_rate"], inputs["energy"],
        inputs["depth"], inputs["wf"], inputs["isf"], inputs["tf"]
    )
    mu_vals.append(mu if mu is not None else np.nan)

# Convert to DataFrame for clean plotting
df = pd.DataFrame({
    var_to_plot: x_vals,
    "MU": mu_vals
})

# Plot the curve
st.line_chart(df.set_index(var_to_plot))

# Show nearest MU at current input
current_val = user_inputs[var_to_plot]
nearest_idx = (np.abs(x_vals - current_val)).argmin()
current_mu = mu_vals[nearest_idx]
st.caption(f"At current {var_to_plot} = {current_val}, MU ≈ {current_mu:.2f}")
