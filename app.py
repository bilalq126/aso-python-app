import streamlit as st
import io
from agent import generate_aso_metadata

# Set page config
st.set_page_config(page_title="ASO Metadata Generator", page_icon="📈", layout="wide")

st.title("ASO Metadata Generator")
st.markdown("Generate localized App Store metadata (Titles, Subtitles, Keywords) using AI.")

# Default Locales from the original fish_iq file
DEFAULT_LOCALES = [
    "USA", "Brazil", "Spain", "Sweden", "Thailand", 
    "Vietnam", "Greece", "Turkey", "Russia", "France", 
    "Germany", "Japan"
]

# Sidebar for configuration
with st.sidebar:
    st.header("Settings")
    
    selected_locales = st.multiselect(
        "Select Target Locales",
        options=["USA", "Brazil", "Spain", "Sweden", "Thailand", "Vietnam", "Greece", "Turkey", "Russia", "France", "Germany", "Japan", "Italy", "China", "Korea", "India", "Indonesia", "Arabia"],
        default=DEFAULT_LOCALES
    )

# Main input field
app_concept = st.text_area("App Concept / Short Description", placeholder="e.g. Pegasus Game - A flying horse simulation where you grow and survive...", height=100)

generate_btn = st.button("Generate Localized ASO Metadata", type="primary")

st.divider()

# Session state to store the result so it persists across re-renders (like download clicks)
if "generated_metadata" not in st.session_state:
    st.session_state.generated_metadata = None

from validator import validate_aso_text, batch_check_keywords
import time

if generate_btn:
    if not app_concept or not selected_locales:
        st.error("Please provide an App Concept and select at least one locale.")
    else:
        with st.status("Generating ASO Metadata...", expanded=True) as status_box:
            try:
                # 1. Generate text
                status_box.write("⚙️ Connecting to Gemini to translate...")
                result = generate_aso_metadata(
                    app_concept=app_concept,
                    locales=selected_locales
                )
                st.session_state.generated_metadata = result
                status_box.write("✅ Text generation complete.")
                
                # 2. Validate Guidelines & Extract Data
                status_box.write("📏 Validating App Store limits...")
                locales_data, warnings = validate_aso_text(result)
                st.session_state.warnings = warnings
                
                # 3. Check Keyword Feasibility
                status_box.write("🔍 Fetching live iTunes search data for USA keywords (including Title & Sub Title)...")
                
                import re
                feasibility_report = {}
                
                for locale, data in locales_data.items():
                    if locale.upper() == "USA":
                        # Extract words from Title and Sub Title
                        title_words = [w.lower() for w in re.findall(r'\b\w+\b', data.get('Title', ''))]
                        subtitle_words = [w.lower() for w in re.findall(r'\b\w+\b', data.get('Sub Title', ''))]
                        explicit_kws = [k.strip().lower() for k in data.get('Keywords', '').split(',') if k.strip()]
                        
                        # Combine them and remove duplicates while preserving order
                        combined_kws = title_words + subtitle_words + explicit_kws
                        seen = set()
                        usa_keywords = [x for x in combined_kws if not (x in seen or seen.add(x))]
                        
                        if usa_keywords:
                            kw_results = batch_check_keywords(usa_keywords, 'us')
                            feasibility_report["USA"] = kw_results
                        break # Only process USA
                        
                st.session_state.feasibility_report = feasibility_report
                
                status_box.update(label="Metadata generated and validated successfully!", state="complete", expanded=False)
            except Exception as e:
                status_box.update(label=f"An error occurred: {e}", state="error")

# Display Warnings if any
if st.session_state.get("warnings"):
    st.warning("⚠️ App Store Guideline Warnings Detected in Generated Text:")
    for w in st.session_state.warnings:
        st.markdown(f"- {w}")

# Display results if available
if st.session_state.generated_metadata:
    st.subheader("Generated Output:")
    
    # Text area for viewing/editing
    text_content = st.text_area("You can copy the text below:", value=st.session_state.generated_metadata, height=400)
    
    # Download button
    bytes_data = text_content.encode('utf-8')
    # Use the first few words of the concept for the filename
    safe_app_name = "".join([c for c in app_concept[:30] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    download_filename = f"{safe_app_name.replace(' ', '_').lower()}_aso.txt" if safe_app_name else "generated_aso.txt"
    
    st.download_button(
        label="Download as .txt File",
        data=bytes_data,
        file_name=download_filename,
        mime="text/plain"
    )

# Display Feasibility Report
if st.session_state.get("feasibility_report") or st.session_state.generated_metadata:
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Keyword Feasibility Report")
    with col2:
        # Give users a way to retry the iTunes fetch if it timed out, without regenerating the AI text
        if st.session_state.generated_metadata:
            retry_btn = st.button("🔄 Retry iTunes Fetch")
            if retry_btn:
                with st.spinner("Fetching live iTunes search data..."):
                    locales_data, _ = validate_aso_text(st.session_state.generated_metadata)
                    
                    import re
                    new_report = {}
                    for locale, data in locales_data.items():
                        if locale.upper() == "USA":
                            # Extract words from Title and Sub Title
                            title_words = [w.lower() for w in re.findall(r'\b\w+\b', data.get('Title', ''))]
                            subtitle_words = [w.lower() for w in re.findall(r'\b\w+\b', data.get('Sub Title', ''))]
                            explicit_kws = [k.strip().lower() for k in data.get('Keywords', '').split(',') if k.strip()]
                            
                            # Combine them and remove duplicates
                            combined_kws = title_words + subtitle_words + explicit_kws
                            seen = set()
                            usa_keywords = [x for x in combined_kws if not (x in seen or seen.add(x))]
                            
                            if usa_keywords:
                                kw_results = batch_check_keywords(usa_keywords, 'us')
                                new_report["USA"] = kw_results
                            break 
                            
                    st.session_state.feasibility_report = new_report
            
    st.markdown("Metrics fetched live from the **iTunes App Store Search API**. Scores are 0-10 (higher means more traffic / harder difficulty).")
    
    # --- Character Count Report for USA ---
    if st.session_state.generated_metadata:
        locales_data, _ = validate_aso_text(st.session_state.generated_metadata)
        usa_data = locales_data.get("Usa") or locales_data.get("USA") # ensure we get the key regardless of capitalization
        if usa_data:
            t_len = len(usa_data.get('Title', ''))
            s_len = len(usa_data.get('Sub Title', ''))
            k_len = len(usa_data.get('Keywords', ''))
            
            st.info(f"**USA Metadata Character Counts:**\n"
                    f"* **Title:** {t_len}/30 chars\n"
                    f"* **Sub Title:** {s_len}/30 chars\n"
                    f"* **Keywords:** {k_len}/100 chars")
    
    if st.session_state.get("feasibility_report"):
        for locale, kw_data in st.session_state.feasibility_report.items():
            with st.expander(f"📍 {locale} Feasibility", expanded=True):
                if not kw_data:
                    st.write("No keywords parsed for this locale.")
                    continue
                    
                # Convert dicts to table format for Streamlit
                table_data = []
                for kw in kw_data:
                    err = kw.get('error')
                    if err:
                        table_data.append({"Keyword": kw['keyword'], "Traffic Score": f"Error: {err}", "Difficulty Score": "N/A"})
                    else:
                        table_data.append({"Keyword": kw['keyword'], "Traffic /10": kw['trafficScore'], "Difficulty /10": kw['difficultyScore']})
                
                st.table(table_data)
