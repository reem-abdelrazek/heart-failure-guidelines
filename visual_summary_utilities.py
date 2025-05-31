import streamlit as st

# --- HF Type Visualization ---


def show_hf_type_summary(hf_type):
    st.subheader("🫀 Understanding Your Type of Heart Failure")

    if hf_type == "Ischemic Heart Failure":
        col1, col2 = st.columns(2)

        with col1:
            st.image(
                "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/IHF_1.png",
                caption="What causes plaque?"
            )
            st.markdown(
                "Fat and cholesterol deposits narrow your arteries, reducing blood flow to the heart."
            )

        with col2:
            st.image(
                "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/IHF_2.png",
                caption="Plaque buildup in arteries"
            )
            st.markdown(
                "Blocked arteries weaken the heart muscle by limiting its oxygen supply."
            )

    elif hf_type == "Dilated Cardiomyopathy (DCM)":
        st.image(
            "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/DCM.png",
            caption="Dilated Cardiomyopathy"
        )
        st.markdown(
            "The heart muscle becomes stretched and weak, making it harder to pump blood. This can lead to fatigue and fluid buildup."
        )

    elif hf_type == "Hypertrophic Cardiomyopathy (HCM)":
        st.image(
            "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/HCM.png",
            caption="Hypertrophic Cardiomyopathy"
        )
        st.markdown(
            "The heart muscle becomes abnormally thick, making it harder for the heart to fill and pump efficiently."
        )

    elif hf_type == "Valvular Heart Disease":
        st.image(
            "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/VHD.png",
            caption="Valvular Heart Disease"
        )
        st.markdown(
            "A damaged valve may not open or close properly, forcing the heart to work harder and eventually weakening it."
        )

    elif hf_type == "Genetic Cardiomyopathy":
        st.image(
            "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/GCM.png",
            caption="Genetic Cardiomyopathy"
        )
        st.markdown(
            "Some heart conditions are inherited. These can affect how thick or strong the heart walls are, leading to symptoms over time."
        )

    else:
        st.info("No heart failure type selected or type is unknown.")


# --- Symptoms Visualization ---

def show_symptoms_summary(symptoms):
    if not symptoms:
        return

    st.subheader("🫁 Understanding Your Symptoms")

    # Mapping of symptom names to their image paths and descriptions
    symptom_info = {
        "Dyspnea (shortness of breath)": {
            "image": "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/Dyspnea.png",
            "description": "Difficulty breathing or feeling like you can't get enough air. This often worsens with physical activity or when lying down."
        },
        "Orthopnea": {
            "image": "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/Orthopnea.png",
            "description": "Shortness of breath that occurs when lying flat, often requiring you to sleep with extra pillows or in a sitting position."
        },
        "Paroxysmal Nocturnal Dyspnea (PND)": {
            "image": "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/PND.png",
            "description": "Sudden episodes of severe shortness of breath that wake you from sleep, often accompanied by coughing or wheezing."
        },
        "Fatigue or weakness": {
            "image": "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/Fatigue.png",
            "description": "Feeling unusually tired or weak, even after rest. This can make daily activities more difficult than usual."
        },
        "Peripheral edema": {
            "image": "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/Peripheral_Edema.png",
            "description": "Swelling in the feet, ankles, and legs caused by fluid buildup. The swelling may leave an indentation when pressed."
        },
        "Exercise intolerance": {
            "image": "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/Exercise_Intolenace.png",
            "description": "Difficulty performing physical activities that you could do before. You may feel tired or short of breath more quickly."
        },
        "Abdominal discomfort or bloating": {
            "image": "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/Abdominal_discomfort or bloating.png",
            "description": "Feeling of fullness, bloating, or discomfort in the abdomen, often due to fluid buildup in the liver or digestive system."
        }
    }

    # Filter symptoms that have illustrations
    symptoms_with_illustrations = [s for s in symptoms if s in symptom_info]

    if not symptoms_with_illustrations:
        return

    # Display symptoms in two columns
    for i in range(0, len(symptoms_with_illustrations), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(symptoms_with_illustrations):
                symptom = symptoms_with_illustrations[i + j]
                with cols[j]:
                    st.markdown(f"### {symptom}")
                    info = symptom_info[symptom]
                    st.image(info["image"], caption=symptom)
                    st.markdown(info["description"])


# --- Comorbidities Visualization ---

def show_comorbidities_summary(comorbidities):
    if not comorbidities:
        return

    st.subheader("🍽️ Understanding Your Risk Factors")

    # Mapping of comorbidity names to their image paths and descriptions
    comorbidity_info = {
        "Hypertension": {
            "image": "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/Hypertension.png",
            "description": "_Description will be added here_"
        },
        "Diabetes": {
            "image": "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/Diabetes.png",
            "description": "_Description will be added here_"
        },
        "Dyslipidemia": {
            "image": "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/Dyslipidemia.png",
            "description": "_Description will be added here_"
        },
        "Kidney Disease": {
            "image": "C:/Users/reema/OneDrive/Desktop/thesis/heart-failure-guidelines/Illustrations/Kidney_disease.png",
            "description": "_Description will be added here_"
        }
    }

    # Normalize comorbidities input to list
    if isinstance(comorbidities, dict):
        comorbidities = [k for k, v in comorbidities.items() if v]
    elif isinstance(comorbidities, str):
        comorbidities = [c.strip() for c in comorbidities.split(',')]

    # Filter comorbidities that have illustrations
    comorbidities_with_illustrations = [
        c for c in comorbidities if c in comorbidity_info]

    # Display comorbidities in two columns
    for i in range(0, len(comorbidities_with_illustrations), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(comorbidities_with_illustrations):
                comorbidity = comorbidities_with_illustrations[i + j]
                with cols[j]:
                    st.markdown(f"### {comorbidity}")
                    info = comorbidity_info[comorbidity]
                    st.image(info["image"], caption=comorbidity)
                    st.markdown(info["description"])


# --- Main Visual Summary ---

def show_visual_summary(hf_types=None, symptoms=None, comorbidities=None):
    # 1️⃣ HF Type Section
    if hf_types:
        st.subheader("🩺 Type of Heart Failure")
        selected_types = hf_types.split(
            ",") if isinstance(hf_types, str) else hf_types
        for hf in selected_types:
            show_hf_type_summary(hf.strip())

    # 2️⃣ Symptom Visualization
    if symptoms:
        show_symptoms_summary(symptoms)

    # 3️⃣ Comorbidities Visualization
    if comorbidities:
        show_comorbidities_summary(comorbidities)
