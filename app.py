import streamlit as st
import io
from agent import generate_competitor_and_keyword_analysis, generate_usa_baseline_from_brainstorm, translate_aso_metadata, generate_play_baseline_from_brainstorm, translate_play_metadata, COMMON_RULES, PLAY_STORE_RULES

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
    
    selected_platform = st.radio(
        "Target Platform",
        options=["Apple App Store", "Google Play Store"]
    )
    
    st.divider()
    with st.expander("Advanced Prompt Settings"):
        st.markdown("<small>Edit the instructions used for keyword generation.</small>", unsafe_allow_html=True)
        custom_common_rules = st.text_area("App Store Instructions", value=COMMON_RULES, height=300)
        custom_play_rules = st.text_area("Google Play Instructions", value=PLAY_STORE_RULES, height=300)


# Main input field
app_concept = st.text_area("App Concept / Short Description", placeholder="e.g. Pegasus Game - A flying horse simulation where you grow and survive...", height=100)

st.divider()
st.subheader("Step 1: Brainstorming")
st.markdown("Analyze competitors and brainstorm a 50-keyword Word Bank.")

step1_btn = st.button("1. Generate Competitors & Keywords", type="primary")

# Session state to store the result so it persists across re-renders (like download clicks)
if "generated_metadata" not in st.session_state:
    st.session_state.generated_metadata = None
if "cot_text" not in st.session_state:
    st.session_state.cot_text = None

from validator import validate_aso_text, batch_check_keywords
import time

if step1_btn:
    if not app_concept:
        st.error("Please provide an App Concept.")
    else:
        with st.status("Brainstorming ASO Concepts...", expanded=True) as status_box:
            try:
                status_box.write("⚙️ Connecting to Gemini for Step 1 & 2 analysis...")
                brainstorm_result = generate_competitor_and_keyword_analysis(app_concept=app_concept, custom_rules=custom_common_rules)
                
                st.session_state.cot_text = brainstorm_result
                st.session_state.generated_metadata = None # Clear any old output
                st.session_state.warnings = []
                st.session_state.feasibility_report = {}
                st.session_state.target_platform = selected_platform # Lock in the platform choice for this session
                
                status_box.update(label="Brainstorming complete!", state="complete", expanded=False)
            except Exception as e:
                status_box.update(label=f"An error occurred: {e}", state="error")                
# Display CoT Reasoning if available
if st.session_state.get("cot_text"):
    st.subheader("Step 2: Generate ASO Metadata")
    st.markdown("Review and edit the Word Bank before finalizing the USA metadata. **Only words left in this box will be used.**")
    
    # Editable text area combining steps 1 and 2
    editable_cot_text = st.text_area("🧠 Competitive Analysis & Keyword Brainstorming", value=st.session_state.cot_text, height=300)
    
    step2_btn = st.button("2. Generate Final USA Baseline & Analyze", type="primary")
    
    if step2_btn:
        with st.status("Building USA Baseline Metadata...", expanded=True) as status_box:
            try:
                # 1. Generate final text using the edited word bank
                status_box.write("⚙️ Forcing Gemini to use the strict Word Bank logic...")
                
                if st.session_state.get("target_platform") == "Google Play Store":
                    result = generate_play_baseline_from_brainstorm(
                        app_concept=app_concept,
                        brainstormed_text=editable_cot_text,
                        custom_play_rules=custom_play_rules
                    )
                else:
                    result = generate_usa_baseline_from_brainstorm(
                        app_concept=app_concept,
                        brainstormed_text=editable_cot_text,
                        custom_rules=custom_common_rules
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
                        # Extract words from Title and Sub Title / Short Description
                        title_words = [w.lower() for w in re.findall(r'\b\w+\b', data.get('Title', ''))]
                        subtitle_words = [w.lower() for w in re.findall(r'\b\w+\b', data.get('Sub Title', ''))]
                        short_desc_words = [w.lower() for w in re.findall(r'\b\w+\b', data.get('Short Description', ''))]
                        
                        explicit_kws = [k.strip().lower() for k in data.get('Keywords', '').split(',') if k.strip()]
                        
                        # Combine them and remove duplicates while preserving order
                        combined_kws = title_words + subtitle_words + short_desc_words + explicit_kws
                        seen = set()
                        usa_keywords = [x for x in combined_kws if not (x in seen or seen.add(x))]
                        
                        if usa_keywords:
                            kw_results = batch_check_keywords(usa_keywords, 'us')
                            feasibility_report["USA"] = kw_results
                        break # Only process USA
                        
                st.session_state.feasibility_report = feasibility_report
                
                status_box.update(label="Metadata generated and validated successfully!", state="complete", expanded=False)
                st.rerun()
            except Exception as e:
                status_box.update(label=f"An error occurred: {e}", state="error")

# Display Warnings if any
if st.session_state.get("warnings"):
    st.warning("⚠️ App Store Guideline Warnings Detected in Generated Text:")
    for w in st.session_state.warnings:
        st.markdown(f"- {w}")

# Display results if available
if st.session_state.generated_metadata:
    st.subheader("Generated Metadata (Text File):")
    
    # Text area for viewing/editing
    text_content = st.text_area("You can review and aggressively edit the USA Baseline here before generating translations:", value=st.session_state.generated_metadata, height=400)
    
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
    
    # ---------------- TRANSLATION SECTION ----------------
    translation_targets = [l for l in selected_locales if l.upper() != "USA"]
    if translation_targets:
        st.divider()
        st.subheader("Global Localization")
        st.markdown("Use the optimized USA Baseline to natively localize metadata for the other selected regions.")
        
        translate_btn = st.button(f"🌍 Translate to {len(translation_targets)} Locales", type="secondary")
        if translate_btn:
            with st.status(f"Localizing for {len(translation_targets)} regions...", expanded=True) as t_status:
                try:
                    t_status.write("⚙️ Connecting to Gemini for native localization...")
                    # 1. Generate translation using the USER'S EDITED text
                    if st.session_state.get("target_platform") == "Google Play Store":
                        trans_result = translate_play_metadata(text_content, translation_targets, custom_play_rules=custom_play_rules)
                    else:
                        trans_result = translate_aso_metadata(text_content, translation_targets, custom_rules=custom_common_rules)
                    
                    # 2. Append to current result
                    new_full_text = text_content + "\n\n" + trans_result
                    st.session_state.generated_metadata = new_full_text
                    
                    # 3. Re-run validation for all locales to catch warnings in the new languages
                    t_status.write("📏 Validating App Store limits for new locales...")
                    locales_data, warnings = validate_aso_text(new_full_text)
                    st.session_state.warnings = warnings
                    
                    t_status.update(label="Translations appended successfully!", state="complete", expanded=False)
                    st.rerun() # Refresh the page immediately so the text area updates with new text
                except Exception as e:
                    t_status.update(label=f"An error occurred: {e}", state="error")

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
                            # Extract words from Title and Sub Title / Short Description
                            title_words = [w.lower() for w in re.findall(r'\b\w+\b', data.get('Title', ''))]
                            subtitle_words = [w.lower() for w in re.findall(r'\b\w+\b', data.get('Sub Title', ''))]
                            short_desc_words = [w.lower() for w in re.findall(r'\b\w+\b', data.get('Short Description', ''))]
                            
                            explicit_kws = [k.strip().lower() for k in data.get('Keywords', '').split(',') if k.strip()]
                            
                            # Combine them and remove duplicates
                            combined_kws = title_words + subtitle_words + short_desc_words + explicit_kws
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
            
            if st.session_state.get("target_platform") == "Google Play Store":
                sd_len = len(usa_data.get('Short Description', ''))
                ld_len = len(usa_data.get('Long Description', ''))
                
                st.info(f"**USA Google Play Character Counts:**\n"
                        f"* **Title:** {t_len}/30 chars\n"
                        f"* **Short Description:** {sd_len}/80 chars\n"
                        f"* **Long Description:** {ld_len}/4000 chars\n"
                        f"*(Play Store ranking weights keywords organically inside these fields)*")
            else:
                s_len = len(usa_data.get('Sub Title', ''))
                k_len = len(usa_data.get('Keywords', ''))
                
                st.info(f"**USA App Store Character Counts:**\n"
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
