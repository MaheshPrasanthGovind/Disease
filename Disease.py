import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
from io import BytesIO
import base64

# Page configuration
st.set_page_config(
    page_title="SymptoGen: Symptom & Genetic Disease Insight Tool",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .feature-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .risk-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 5px;
    }
    .risk-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 5px;
    }
    .risk-low {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 5px;
    }
    .ethics-box {
        background-color: #fff8e1;
        border: 2px solid #ffc107;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# Sample data - Symptom to Disease Mapping
@st.cache_data
def load_symptom_disease_data():
    symptom_disease_data = {
        'Disease': [
            'COVID-19', 'Influenza', 'Dengue Fever', 'Malaria', 'Common Cold',
            'Pneumonia', 'Bronchitis', 'Gastroenteritis', 'Migraine', 'Hypertension',
            'Diabetes Type 2', 'Asthma', 'Allergic Rhinitis', 'Food Poisoning', 'Anxiety Disorder'
        ],
        'Primary_Symptoms': [
            ['fever', 'cough', 'fatigue', 'loss_of_taste'],
            ['fever', 'cough', 'muscle_aches', 'fatigue'],
            ['fever', 'headache', 'muscle_pain', 'rash'],
            ['fever', 'chills', 'headache', 'nausea'],
            ['runny_nose', 'sneezing', 'sore_throat', 'mild_cough'],
            ['fever', 'cough', 'chest_pain', 'difficulty_breathing'],
            ['cough', 'chest_pain', 'fatigue', 'mild_fever'],
            ['nausea', 'vomiting', 'diarrhea', 'abdominal_pain'],
            ['headache', 'nausea', 'sensitivity_to_light', 'visual_disturbances'],
            ['headache', 'dizziness', 'chest_pain', 'shortness_of_breath'],
            ['frequent_urination', 'excessive_thirst', 'fatigue', 'blurred_vision'],
            ['difficulty_breathing', 'wheezing', 'chest_tightness', 'cough'],
            ['runny_nose', 'sneezing', 'itchy_eyes', 'nasal_congestion'],
            ['nausea', 'vomiting', 'diarrhea', 'abdominal_cramps'],
            ['restlessness', 'fatigue', 'difficulty_concentrating', 'muscle_tension']
        ],
        'Severity': ['High', 'Medium', 'High', 'High', 'Low', 'High', 'Medium', 'Medium', 'Medium', 'High', 'High', 'Medium', 'Low', 'Medium', 'Medium']
    }
    
    return pd.DataFrame(symptom_disease_data)

# Sample genetic data - Gene to Disease Mapping
@st.cache_data
def load_genetic_disease_data():
    genetic_data = {
        'Gene': ['BRCA1', 'BRCA2', 'APOE', 'CFTR', 'HTT', 'LDLR', 'HFE', 'F5', 'MTHFR', 'CYP2D6'],
        'Associated_Disease': [
            'Breast Cancer', 'Breast Cancer', 'Alzheimer Disease', 'Cystic Fibrosis',
            'Huntington Disease', 'Familial Hypercholesterolemia', 'Hemochromatosis',
            'Factor V Leiden Thrombophilia', 'Hyperhomocysteinemia', 'Drug Metabolism Variants'
        ],
        'Risk_Level': ['High', 'High', 'Medium', 'High', 'High', 'Medium', 'Medium', 'Medium', 'Low', 'Low'],
        'Prevalence': ['1 in 400', '1 in 800', '1 in 4', '1 in 2500', '1 in 10000', '1 in 500', '1 in 200', '1 in 20', '1 in 10', '1 in 4'],
        'Description': [
            'Increased risk of breast and ovarian cancer',
            'Increased risk of breast and ovarian cancer',
            'Associated with late-onset Alzheimer disease',
            'Causes cystic fibrosis when both copies are mutated',
            'Causes Huntington disease (dominant inheritance)',
            'Causes high cholesterol levels',
            'Causes iron overload in the body',
            'Increases blood clotting risk',
            'Affects folate metabolism',
            'Affects drug metabolism, particularly antidepressants'
        ]
    }
    
    return pd.DataFrame(genetic_data)

# Available symptoms list
AVAILABLE_SYMPTOMS = [
    'fever', 'cough', 'fatigue', 'headache', 'muscle_aches', 'sore_throat',
    'runny_nose', 'sneezing', 'nausea', 'vomiting', 'diarrhea', 'abdominal_pain',
    'chest_pain', 'difficulty_breathing', 'dizziness', 'rash', 'joint_pain',
    'loss_of_taste', 'loss_of_smell', 'chills', 'sweating', 'blurred_vision',
    'frequent_urination', 'excessive_thirst', 'weight_loss', 'weight_gain',
    'restlessness', 'anxiety', 'depression', 'insomnia', 'muscle_weakness',
    'numbness', 'tingling', 'sensitivity_to_light', 'visual_disturbances',
    'wheezing', 'chest_tightness', 'itchy_eyes', 'nasal_congestion',
    'abdominal_cramps', 'muscle_tension', 'difficulty_concentrating',
    'shortness_of_breath', 'mild_cough', 'mild_fever'
]

def calculate_symptom_match_score(user_symptoms, disease_symptoms):
    """Calculate matching score between user symptoms and disease symptoms"""
    if not user_symptoms or not disease_symptoms:
        return 0
    
    user_set = set(user_symptoms)
    disease_set = set(disease_symptoms)
    
    intersection = len(user_set.intersection(disease_set))
    union = len(user_set.union(disease_set))
    
    # Jaccard similarity with bonus for exact matches
    jaccard_score = intersection / union if union > 0 else 0
    match_bonus = intersection / len(disease_set) if len(disease_set) > 0 else 0
    
    return (jaccard_score * 0.6 + match_bonus * 0.4) * 100

def analyze_symptoms(user_symptoms):
    """Analyze user symptoms and return predicted diseases"""
    symptom_data = load_symptom_disease_data()
    results = []
    
    for _, row in symptom_data.iterrows():
        score = calculate_symptom_match_score(user_symptoms, row['Primary_Symptoms'])
        if score > 0:
            results.append({
                'Disease': row['Disease'],
                'Confidence': score,
                'Severity': row['Severity'],
                'Matched_Symptoms': list(set(user_symptoms).intersection(set(row['Primary_Symptoms'])))
            })
    
    # Sort by confidence score
    results = sorted(results, key=lambda x: x['Confidence'], reverse=True)
    return results[:10]  # Return top 10 matches

def analyze_genetic_markers(genetic_input):
    """Analyze genetic markers and return associated risks"""
    genetic_data = load_genetic_disease_data()
    results = []
    
    # Simple pattern matching for gene names
    genes_found = []
    for _, row in genetic_data.iterrows():
        if row['Gene'].upper() in genetic_input.upper():
            genes_found.append(row['Gene'])
            results.append({
                'Gene': row['Gene'],
                'Disease': row['Associated_Disease'],
                'Risk_Level': row['Risk_Level'],
                'Prevalence': row['Prevalence'],
                'Description': row['Description']
            })
    
    return results, genes_found

def generate_report(symptom_results, genetic_results, user_symptoms, genetic_input):
    """Generate a comprehensive report"""
    report = f"""
# SymptoGen Analysis Report
**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Symptom Analysis
**Symptoms Analyzed:** {', '.join(user_symptoms) if user_symptoms else 'None'}

### Top Disease Predictions:
"""
    
    if symptom_results:
        for i, result in enumerate(symptom_results[:5], 1):
            report += f"""
{i}. **{result['Disease']}** (Confidence: {result['Confidence']:.1f}%)
   - Severity: {result['Severity']}
   - Matched Symptoms: {', '.join(result['Matched_Symptoms'])}
"""
    else:
        report += "No significant disease matches found based on provided symptoms.\n"
    
    report += f"""
## Genetic Analysis
**Genetic Input:** {genetic_input if genetic_input else 'None provided'}

### Genetic Risk Factors:
"""
    
    if genetic_results:
        for result in genetic_results:
            report += f"""
- **{result['Gene']}**: {result['Disease']}
  - Risk Level: {result['Risk_Level']}
  - Prevalence: {result['Prevalence']}
  - Description: {result['Description']}
"""
    else:
        report += "No genetic risk factors identified.\n"
    
    report += f"""
## Important Disclaimers
⚠️ **This analysis is for educational purposes only and should not be used as a substitute for professional medical advice.**

- Consult with healthcare professionals for proper diagnosis and treatment
- Genetic risk predictions are based on current scientific knowledge and may change
- Individual risk factors may vary significantly
- This tool does not account for family history, lifestyle factors, or other important variables

## Recommendations
1. Discuss these findings with your healthcare provider
2. Consider professional genetic counseling if genetic risks are identified
3. Maintain regular health check-ups
4. Follow evidence-based preventive care guidelines
"""
    
    return report

# Main App Interface
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧬 SymptoGen: Symptom & Genetic Disease Insight Tool</h1>
        <p>AI-powered symptom analysis and genetic risk assessment</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("🔬 Analysis Tools")
    analysis_type = st.sidebar.selectbox(
        "Choose Analysis Type",
        ["Comprehensive Analysis", "Symptom Analysis Only", "Genetic Analysis Only"]
    )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Symptom Input Section
        if analysis_type in ["Comprehensive Analysis", "Symptom Analysis Only"]:
            st.markdown('<div class="feature-box">', unsafe_allow_html=True)
            st.subheader("🩺 Symptom Input")
            
            # Symptom input method selection
            input_method = st.radio(
                "How would you like to input symptoms?",
                ["Select from checklist", "Enter manually"]
            )
            
            user_symptoms = []
            
            if input_method == "Select from checklist":
                st.write("Select all symptoms you're experiencing:")
                
                # Create columns for better layout
                cols = st.columns(3)
                selected_symptoms = []
                
                for i, symptom in enumerate(AVAILABLE_SYMPTOMS):
                    col_idx = i % 3
                    with cols[col_idx]:
                        if st.checkbox(symptom.replace('_', ' ').title(), key=f"symptom_{symptom}"):
                            selected_symptoms.append(symptom)
                
                user_symptoms = selected_symptoms
            
            else:  # Manual input
                manual_symptoms = st.text_area(
                    "Enter symptoms (comma-separated):",
                    placeholder="e.g., fever, cough, headache, fatigue"
                )
                if manual_symptoms:
                    user_symptoms = [s.strip().lower().replace(' ', '_') for s in manual_symptoms.split(',')]
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Genetic Input Section
        if analysis_type in ["Comprehensive Analysis", "Genetic Analysis Only"]:
            st.markdown('<div class="feature-box">', unsafe_allow_html=True)
            st.subheader("🧬 Genetic Data Input")
            
            genetic_input_method = st.radio(
                "Choose genetic input method:",
                ["Enter gene names", "Paste DNA sequence (simulated)"]
            )
            
            genetic_input = ""
            
            if genetic_input_method == "Enter gene names":
                genetic_input = st.text_area(
                    "Enter known gene variants or mutations:",
                    placeholder="e.g., BRCA1, BRCA2, APOE, rs123456"
                )
            else:
                genetic_input = st.text_area(
                    "Paste DNA sequence (this is simulated analysis):",
                    placeholder="e.g., ATCGATCGATCG... (any sequence for demonstration)"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Analysis button and quick stats
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        st.subheader("📊 Quick Stats")
        
        symptom_data = load_symptom_disease_data()
        genetic_data = load_genetic_disease_data()
        
        st.metric("Diseases in Database", len(symptom_data))
        st.metric("Genetic Markers", len(genetic_data))
        st.metric("Available Symptoms", len(AVAILABLE_SYMPTOMS))
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Analysis button
        if st.button("🔍 Run Analysis", type="primary", use_container_width=True):
            if (analysis_type == "Symptom Analysis Only" and not user_symptoms) or \
               (analysis_type == "Genetic Analysis Only" and not genetic_input) or \
               (analysis_type == "Comprehensive Analysis" and not user_symptoms and not genetic_input):
                st.error("Please provide at least one input for analysis!")
            else:
                with st.spinner("Analyzing your data..."):
                    # Perform analysis
                    symptom_results = []
                    genetic_results = []
                    
                    if analysis_type in ["Comprehensive Analysis", "Symptom Analysis Only"] and user_symptoms:
                        symptom_results = analyze_symptoms(user_symptoms)
                    
                    if analysis_type in ["Comprehensive Analysis", "Genetic Analysis Only"] and genetic_input:
                        genetic_results, genes_found = analyze_genetic_markers(genetic_input)
                    
                    # Store results in session state
                    st.session_state.analysis_results = {
                        'symptom_results': symptom_results,
                        'genetic_results': genetic_results,
                        'user_symptoms': user_symptoms,
                        'genetic_input': genetic_input
                    }
                
                st.success("Analysis complete! Results shown below.")
    
    # Results Section
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        st.markdown("---")
        st.header("📋 Analysis Results")
        
        # Create tabs for different result views
        tab1, tab2, tab3, tab4 = st.tabs(["🩺 Disease Predictions", "🧬 Genetic Risks", "📊 Visualizations", "📄 Full Report"])
        
        with tab1:
            if results['symptom_results']:
                st.subheader("Top Disease Predictions")
                
                for i, result in enumerate(results['symptom_results'][:5], 1):
                    severity_class = f"risk-{result['Severity'].lower()}"
                    st.markdown(f"""
                    <div class="{severity_class}">
                        <h4>{i}. {result['Disease']} ({result['Confidence']:.1f}% confidence)</h4>
                        <p><strong>Severity:</strong> {result['Severity']}</p>
                        <p><strong>Matched Symptoms:</strong> {', '.join(result['Matched_Symptoms'])}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No symptom analysis performed or no matches found.")
        
        with tab2:
            if results['genetic_results']:
                st.subheader("Genetic Risk Assessment")
                
                for result in results['genetic_results']:
                    risk_class = f"risk-{result['Risk_Level'].lower()}"
                    st.markdown(f"""
                    <div class="{risk_class}">
                        <h4>{result['Gene']} - {result['Disease']}</h4>
                        <p><strong>Risk Level:</strong> {result['Risk_Level']}</p>
                        <p><strong>Prevalence:</strong> {result['Prevalence']}</p>
                        <p><strong>Description:</strong> {result['Description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No genetic analysis performed or no risk factors identified.")
        
        with tab3:
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                if results['symptom_results']:
                    st.subheader("Disease Prediction Confidence")
                    
                    # Create bar chart
                    diseases = [r['Disease'] for r in results['symptom_results'][:8]]
                    confidences = [r['Confidence'] for r in results['symptom_results'][:8]]
                    
                    fig = px.bar(
                        x=confidences,
                        y=diseases,
                        orientation='h',
                        title="Disease Prediction Confidence Scores",
                        labels={'x': 'Confidence (%)', 'y': 'Disease'},
                        color=confidences,
                        color_continuous_scale='Viridis'
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if results['genetic_results']:
                    st.subheader("Genetic Risk Distribution")
                    
                    # Risk level pie chart
                    risk_counts = {}
                    for result in results['genetic_results']:
                        risk_level = result['Risk_Level']
                        risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
                    
                    fig = px.pie(
                        values=list(risk_counts.values()),
                        names=list(risk_counts.keys()),
                        title="Genetic Risk Level Distribution",
                        color_discrete_map={
                            'High': '#ff4444',
                            'Medium': '#ffaa00',
                            'Low': '#44ff44'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.subheader("Comprehensive Analysis Report")
            
            # Generate and display report
            report = generate_report(
                results['symptom_results'],
                results['genetic_results'],
                results['user_symptoms'],
                results['genetic_input']
            )
            
            st.markdown(report)
            
            # Download options
            st.subheader("📥 Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Text download
                st.download_button(
                    label="📄 Download as Text",
                    data=report,
                    file_name=f"symptogen_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            
            with col2:
                # Create a simple HTML version for better formatting
                html_report = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>SymptoGen Analysis Report</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        h1, h2, h3 {{ color: #333; }}
                        .disclaimer {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    {report.replace('⚠️', '').replace('🧬', '').replace('🩺', '').replace('📊', '').replace('📄', '')}
                </body>
                </html>
                """
                
                st.download_button(
                    label="🌐 Download as HTML",
                    data=html_report,
                    file_name=f"symptogen_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html"
                )
    
    # Bioethics and Disclaimer Section
    st.markdown("---")
    st.markdown("""
    <div class="ethics-box">
        <h3>⚠️ Important Bioethical Considerations & Disclaimers</h3>
        
        <p><strong>This tool is for educational and informational purposes only.</strong></p>
        
        <h4>Medical Disclaimers:</h4>
        <ul>
            <li>AI-based symptom analysis is <strong>NOT</strong> a substitute for professional medical advice, diagnosis, or treatment</li>
            <li>Always consult with qualified healthcare professionals for medical concerns</li>
            <li>This tool should not be used for emergency medical situations</li>
            <li>The predictions are based on limited data and may not reflect your actual condition</li>
        </ul>
        
        <h4>Genetic Information Ethics:</h4>
        <ul>
            <li><strong>Genetic risk is not destiny</strong> - having a genetic variant doesn't guarantee disease development</li>
            <li>Consult a certified genetic counselor for professional genetic risk assessment</li>
            <li>Consider privacy implications before sharing genetic data</li>
            <li>Be aware of potential psychological impacts of genetic risk information</li>
            <li>Understand that genetic testing should be performed by accredited laboratories</li>
        </ul>
        
        <h4>Data Privacy:</h4>
        <ul>
            <li>This demo tool does not store or transmit your personal health data</li>
            <li>For real applications, ensure proper data encryption and privacy protections</li>
            <li>Be cautious about sharing sensitive health information online</li>
        </ul>
        
        <p><strong>If you are experiencing a medical emergency, contact emergency services immediately.</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9em;">
        <p>SymptoGen v1.0 | Built with Streamlit | For Educational Purposes Only</p>
        <p>Always consult healthcare professionals for medical advice</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
