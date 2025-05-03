import streamlit as st

def show_hf_type_summary(hf_type):
    st.subheader("🫀 Understanding Your Type of Heart Failure")

    if hf_type == "Ischemic Heart Failure":
        col1, col2, col3 = st.columns(3)

        with col1:
            st.image("C:/Users/reema/OneDrive/Desktop/Illustrations/HF types/IHF_1.png", caption="What causes plaque?")
            st.markdown("Unhealthy diet, smoking, no exercise, and high salt intake can damage your arteries over time.")

        with col2:
            st.image("C:/Users/reema/OneDrive/Desktop/Illustrations/HF types/IHF_3.png", caption="Plaque buildup in arteries")
            st.markdown("Fat and cholesterol deposits narrow your arteries, reducing blood flow to the heart.")

        with col3:
            st.image("C:/Users/reema/OneDrive/Desktop/Illustrations/HF types/IHF_2.png", caption="Heart structure in IHF")
            st.markdown("Blocked arteries weaken the heart muscle by limiting its oxygen supply.")

    elif hf_type == "Dilated Cardiomyopathy (DCM)":
        st.image("C:/Users/reema/OneDrive/Desktop/Illustrations/HF types/DCM.png", caption="Dilated Cardiomyopathy")
        st.markdown("The heart muscle becomes stretched and weak, making it harder to pump blood. This can lead to fatigue and fluid buildup.")

    elif hf_type == "Hypertrophic Cardiomyopathy (HCM)":
        st.image("C:/Users/reema/OneDrive/Desktop/Illustrations/HF types/HCM.png", caption="Hypertrophic Cardiomyopathy")
        st.markdown("The heart muscle becomes abnormally thick, making it harder for the heart to fill and pump efficiently.")

    elif hf_type == "Valvular Heart Disease":
        st.image("C:/Users/reema/OneDrive/Desktop/Illustrations/HF types/VHD.png", caption="Valvular Heart Disease")
        st.markdown("A damaged valve may not open or close properly, forcing the heart to work harder and eventually weakening it.")

    elif hf_type == "Genetic Cardiomyopathy":
        st.image("C:/Users/reema/OneDrive/Desktop/Illustrations/HF types/GCM.png", caption="Genetic Cardiomyopathy")
        st.markdown("Some heart conditions are inherited. These can affect how thick or strong the heart walls are, leading to symptoms over time.")

    else:
        st.info("No heart failure type selected or type is unknown.")
