import streamlit as st
import os
import datetime
from crew import K8sRcaCrew

# UI Configuration
st.set_page_config(
    page_title="K8s AI RCA Agent",
    page_icon="☸️",
    layout="wide"
)

st.title("☸️ Kubernetes Pod Troubleshooter")
st.markdown("Enter a pod name and namespace, and our Multi-Agent AI will perform a complete Root Cause Analysis.")

# --- NEW: Initialize Session State ---
# This ensures the variables exist even before the form is submitted
if "report_content" not in st.session_state:
    st.session_state.report_content = None
if "analyzed_pod_name" not in st.session_state:
    st.session_state.analyzed_pod_name = ""

# Input Form
with st.form("rca_form"):
    col1, col2 = st.columns(2)
    with col1:
        pod_name = st.text_input("Pod Name", placeholder="e.g., payment-service-7bb5df8...")
    with col2:
        namespace = st.text_input("Namespace", value="default")
        
    user_query = st.text_area(
        "Describe the issue (Optional)", 
        placeholder="e.g., Why is my payment pod crash looping?",
        height=100
    )
    
    submitted = st.form_submit_button("Generate RCA Report")

# Execution Logic
if submitted:
    if not pod_name:
        st.error("Pod Name is required.")
    else:
        st.info("Kickstarting the Multi-Agent Crew... This may take 30-90 seconds.")
        
        with st.spinner('Agents are gathering and analyzing data...'):
            try:
                inputs = {
                    'pod_name': pod_name,
                    'namespace': namespace,
                    'user_query': user_query if user_query else f"Investigate pod {pod_name}."
                }
                
                rca_crew = K8sRcaCrew().crew()
                result = rca_crew.kickoff(inputs=inputs)
                
                # --- NEW: Save the result to Session State ---
                st.session_state.report_content = result.raw
                st.session_state.analyzed_pod_name = pod_name
                
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")

# --- NEW: Display and Download Logic (Outside the form block) ---
# Because this checks session_state, it stays on screen even after clicking Download
if st.session_state.report_content:
    st.success("Analysis Complete!")
    
    st.markdown("---")
    st.markdown(st.session_state.report_content) 
    
    st.markdown("---")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_pod_name = st.session_state.analyzed_pod_name.replace("/", "-").replace("\\", "-")
    export_filename = f"{safe_pod_name}_RCA_{timestamp}.md"
    
    st.download_button(
        label="💾 Download RCA Report (.md)",
        data=st.session_state.report_content,
        file_name=export_filename,
        mime="text/markdown",
        use_container_width=True
    )