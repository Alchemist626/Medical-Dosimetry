import streamlit as st
import zipfile
import os
import tempfile
import numpy as np
import pydicom
import matplotlib.pyplot as plt

# Sidebar: app selection
app_mode = st.sidebar.selectbox(
    "Choose App",
    ["MU Calculator", "3D CT Slice Viewer + HU Histogram"]
)

if app_mode == "MU Calculator":
    st.title("Medical Dosimetry MU Calculator with Alarms")

    # User inputs
    dose = st.number_input("Prescribed Dose (cGy)", min_value=1.0, value=200.0, step=1.0)
    field_size = st.number_input("Field Size (cm)", min_value=0.1, value=7.5, step=0.1)
    depth = st.number_input("Depth (cm)", min_value=0.0, value=8.0, step=0.1)
    ssd = st.number_input("SSD (cm)", min_value=50.0, value=100.0, step=0.1)
    cal_factor = st.number_input("Calibration Factor (cGy/MU)", min_value=0.01, value=1.0, step=0.01)

    # Typical clinical limits
    field_size_limits = (1, 40)
    depth_limits = (0, 30)
    ssd_limits = (80, 120)
    mu_limits = (0, 1000)

    # Lookup tables (simplified)
    output_factor_table = {6: 0.97, 10: 1.00}
    pdd_table = {5: 0.85, 10: 0.70}

    def linear_interpolate(x, x0, y0, x1, y1):
        return y0 + (x - x0) / (x1 - x0) * (y1 - y0)

    def interpolate_table(x, table):
        keys = sorted(table.keys())
        if x <= keys[0]:
            return table[keys[0]]
        if x >= keys[-1]:
            return table[keys[-1]]
        for i in range(len(keys) - 1):
            if keys[i] <= x <= keys[i+1]:
                return linear_interpolate(x, keys[i], table[keys[i]], keys[i+1], table[keys[i+1]])
        return None

    of = interpolate_table(field_size, output_factor_table)
    pdd = interpolate_table(depth, pdd_table)
    dmax = 1.5
    isf = ((ssd + dmax) / (ssd + depth)) ** 2

    mu = dose / (of * pdd * cal_factor * isf)

    # Alerts
    if not (field_size_limits[0] <= field_size <= field_size_limits[1]):
        st.warning(f"⚠️ Field size {field_size} cm outside typical clinical range {field_size_limits} cm.")
    if not (depth_limits[0] <= depth <= depth_limits[1]):
        st.warning(f"⚠️ Depth {depth} cm outside typical clinical range {depth_limits} cm.")
    if not (ssd_limits[0] <= ssd <= ssd_limits[1]):
        st.warning(f"⚠️ SSD {ssd} cm outside typical clinical range {ssd_limits} cm.")
    if not (mu_limits[0] < mu < mu_limits[1]):
        st.error(f"❌ Calculated MU {mu:.1f} outside expected range {mu_limits}!")

    st.markdown(f"### Calculated MU: {mu:.1f}")
    st.info("Ensure inputs are accurate and within clinical norms.")

elif app_mode == "3D CT Slice Viewer + HU Histogram":
    st.title("CT Slice Viewer + HU Histogram")

    uploaded_file = st.file_uploader("Upload ZIP file containing CT DICOMs", type="zip")

    if uploaded_file:
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Save uploaded zip file
            zip_path = os.path.join(tmpdirname, "uploaded.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)

            # Find CT DICOM files
            ct_slices = []
            for root, _, files in os.walk(tmpdirname):
                for filename in files:
                    if filename.lower().endswith('.dcm'):
                        ds = pydicom.dcmread(os.path.join(root, filename))
                        if ds.Modality.upper() == 'CT' and hasattr(ds, 'InstanceNumber'):
                            ct_slices.append(ds)

            if len(ct_slices) == 0:
                st.error("No CT DICOM slices found in uploaded ZIP.")
            else:
                # Sort slices by ImagePositionPatient[2] if available else InstanceNumber
                if hasattr(ct_slices[0], "ImagePositionPatient"):
                    ct_slices.sort(key=lambda x: x.ImagePositionPatient[2])
                else:
                    ct_slices.sort(key=lambda x: int(x.InstanceNumber))

                # Convert to HU volume
                pixel_arrays = []
                for s in ct_slices:
                    slope = getattr(s, 'RescaleSlope', 1)
                    intercept = getattr(s, 'RescaleIntercept', 0)
                    hu_slice = s.pixel_array.astype(np.float32) * slope + intercept
                    pixel_arrays.append(hu_slice)

                volume = np.stack(pixel_arrays)

                # Slice slider
                slice_idx = st.slider("Select axial slice", 0, volume.shape[0] - 1, value=volume.shape[0] // 2)
                st.write(f"Displaying axial slice #{slice_idx}")

                # Display slice
                fig1, ax1 = plt.subplots()
                ax1.imshow(volume[slice_idx], cmap='gray', vmin=-1000, vmax=400)
                ax1.axis('off')
                st.pyplot(fig1)

                # HU histogram
                fig2, ax2 = plt.subplots()
                ax2.hist(volume.ravel(), bins=200, range=(-1000, 2000), color='gray')
                ax2.set_title('Histogram of Hounsfield Units (HU)')
                ax2.set_xlabel('HU')
                ax2.set_ylabel('Voxel Count')
                ax2.grid(True)
                st.pyplot(fig2)
