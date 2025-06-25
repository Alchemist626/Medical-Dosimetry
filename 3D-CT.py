import streamlit as st
import zipfile
import os
import tempfile
import numpy as np
import pydicom
import matplotlib.pyplot as plt

st.title("CT Slice Viewer + HU Histogram")

uploaded_file = st.file_uploader("Upload ZIP file containing CT DICOMs", type="zip")

if uploaded_file:
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Save uploaded zip file to temp folder
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
            # Sort slices by InstanceNumber or ImagePositionPatient[2] if available
            if hasattr(ct_slices[0], "ImagePositionPatient"):
                ct_slices.sort(key=lambda x: x.ImagePositionPatient[2])
            else:
                ct_slices.sort(key=lambda x: int(x.InstanceNumber))

            # Convert to HU
            pixel_arrays = []
            for s in ct_slices:
                slope = getattr(s, 'RescaleSlope', 1)
                intercept = getattr(s, 'RescaleIntercept', 0)
                hu_slice = s.pixel_array.astype(np.float32) * slope + intercept
                pixel_arrays.append(hu_slice)

            volume = np.stack(pixel_arrays)

            # === Add slice slider ===
            slice_idx = st.slider("Select axial slice", 0, volume.shape[0] - 1, value=volume.shape[0] // 2)
            st.write(f"Displaying axial slice #{slice_idx}")

            # Show selected slice
            fig1, ax1 = plt.subplots()
            ax1.imshow(volume[slice_idx], cmap='gray', vmin=-1000, vmax=400)
            ax1.axis('off')
            st.pyplot(fig1)

            # Plot HU histogram
            fig2, ax2 = plt.subplots()
            ax2.hist(volume.ravel(), bins=200, range=(-1000, 2000), color='gray')
            ax2.set_title('Histogram of Hounsfield Units (HU)')
            ax2.set_xlabel('HU')
            ax2.set_ylabel('Voxel Count')
            ax2.grid(True)
            st.pyplot(fig2)
