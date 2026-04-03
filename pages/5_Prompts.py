"""Page 5: Prompts - Manage and customize AI prompts."""

import json
import streamlit as st

from core.prompts import (
    DEFAULT_PROMPTS,
    get_all_prompts,
    save_prompts_to_config,
    reload_prompts
)


def initialize_page_state():
    """Initialize session state for prompts page."""
    if "prompts_loaded" not in st.session_state:
        st.session_state.prompts_loaded = False
    if "edited_prompts" not in st.session_state:
        st.session_state.edited_prompts = None


def load_current_prompts():
    """Load current prompts into session state."""
    st.session_state.edited_prompts = get_all_prompts()
    st.session_state.prompts_loaded = True


def main():
    """Main page content."""
    initialize_page_state()

    st.title("⚙️ Prompt Management")
    st.markdown("Customize the AI prompts used for product description generation")

    st.info("""
    **Tips:**
    - Edit any prompt below and click "Save Prompts" to update the configuration
    - Changes take effect after restarting the app or clicking "Reload Prompts"
    - Click "Reset to Defaults" to restore original prompts
    - Use "Export Prompts" to backup your configuration
    """)

    # Load prompts if not already loaded
    if not st.session_state.prompts_loaded:
        load_current_prompts()

    # Navigation buttons at top
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🔄 Reload Prompts", use_container_width=True):
            reload_prompts()
            load_current_prompts()
            st.success("Prompts reloaded from config!")
            st.rerun()

    with col2:
        if st.button("📥 Export Prompts", use_container_width=True):
            prompts_json = json.dumps(get_all_prompts(), indent=2)
            st.download_button(
                label="Download JSON",
                data=prompts_json,
                file_name="prompts_export.json",
                mime="application/json"
            )

    with col3:
        if st.button("↩️ Reset to Defaults", use_container_width=True):
            st.session_state.edited_prompts = DEFAULT_PROMPTS.copy()
            st.session_state.prompts_loaded = True
            st.warning("Defaults loaded. Click 'Save Prompts' to apply.")

    st.markdown("---")

    # Tabbed interface for different prompt categories
    tabs = st.tabs([
        "Tone Prompts",
        "Generation Prompts",
        "Quality Prompts",
        "Validator Prompt"
    ])

    edited = st.session_state.edited_prompts

    # Tab 1: Tone Prompts
    with tabs[0]:
        st.markdown("### Tone-Specific Prompts")
        st.markdown("These prompts define the writing style for different tone options")

        tone_cols = st.columns(2)
        for idx, (tone_name, tone_prompt) in enumerate(edited["tone_prompts"].items()):
            with tone_cols[idx % 2]:
                edited["tone_prompts"][tone_name] = st.text_area(
                    f"{tone_name} Tone",
                    value=tone_prompt,
                    height=200,
                    key=f"tone_{tone_name}"
                )

    # Tab 2: Generation Prompts
    with tabs[1]:
        st.markdown("### Generation Prompts")
        st.markdown("Prompts used in the description generation pipeline")

        edited["usp_extraction_prompt"] = st.text_area(
            "USP Extraction Prompt",
            value=edited["usp_extraction_prompt"],
            height=250,
            key="usp_prompt",
            help="Extracts 3 unique selling points from product info"
        )

        edited["description_writer_prompt"] = st.text_area(
            "Description Writer Prompt",
            value=edited["description_writer_prompt"],
            height=300,
            key="desc_prompt",
            help="Writes the main product description paragraph"
        )

        edited["conversion_hook_prompt"] = st.text_area(
            "Conversion Hook Prompt",
            value=edited["conversion_hook_prompt"],
            height=200,
            key="hook_prompt",
            help="Creates attention-grabbing opening sentence"
        )

        edited["bullet_variant_prompt"] = st.text_area(
            "Bullet Variant Prompt",
            value=edited["bullet_variant_prompt"],
            height=200,
            key="bullet_prompt",
            help="Converts description to 5 bullet points"
        )

        edited["seo_enricher_prompt"] = st.text_area(
            "SEO Enricher Prompt",
            value=edited["seo_enricher_prompt"],
            height=250,
            key="seo_prompt",
            help="Adds SEO keywords to description"
        )

        edited["brand_voice_prompt"] = st.text_area(
            "Brand Voice Prompt",
            value=edited["brand_voice_prompt"],
            height=300,
            key="brand_prompt",
            help="Analyzes sample text to extract brand voice"
        )

        edited["consistency_checker_prompt"] = st.text_area(
            "Consistency Checker Prompt",
            value=edited["consistency_checker_prompt"],
            height=300,
            key="consistency_prompt",
            help="Checks tone consistency across batch"
        )

    # Tab 3: Quality Prompts
    with tabs[2]:
        st.markdown("### Quality Prompts")
        st.markdown("Prompts used for quality evaluation")

        edited["quality_judge_prompt"] = st.text_area(
            "Quality Judge Prompt",
            value=edited["quality_judge_prompt"],
            height=350,
            key="judge_prompt",
            help="Evaluates description quality and provides score 1-10"
        )

    # Tab 4: Validator Prompt
    with tabs[3]:
        st.markdown("### LLM Validator Prompt")
        st.markdown("Prompt used to validate descriptions before approval")

        edited["validator_prompt"] = st.text_area(
            "Validator Prompt",
            value=edited["validator_prompt"],
            height=400,
            key="validator_prompt",
            help="Checks grammar, tone, and quality before saving to DB"
        )

    st.markdown("---")

    # Save button
    st.markdown("### Save Changes")
    save_col1, save_col2 = st.columns([1, 3])

    with save_col1:
        if st.button("💾 Save Prompts", use_container_width=True, type="primary"):
            # Build the config dict
            config_to_save = {
                "tone_prompts": edited["tone_prompts"],
                "usp_extraction_prompt": edited["usp_extraction_prompt"],
                "description_writer_prompt": edited["description_writer_prompt"],
                "conversion_hook_prompt": edited["conversion_hook_prompt"],
                "seo_enricher_prompt": edited["seo_enricher_prompt"],
                "quality_judge_prompt": edited["quality_judge_prompt"],
                "consistency_checker_prompt": edited["consistency_checker_prompt"],
                "brand_voice_prompt": edited["brand_voice_prompt"],
                "bullet_variant_prompt": edited["bullet_variant_prompt"],
                "validator_prompt": edited["validator_prompt"]
            }

            if save_prompts_to_config(config_to_save):
                st.success("Prompts saved to prompts_config.json!")
                st.info("Restart the app or click 'Reload Prompts' to apply changes.")
            else:
                st.error("Failed to save prompts. Check file permissions.")

    # Footer
    st.markdown("---")
    st.markdown("""
    **Prompt Variables:**
    - `{product_json}` - Product data as JSON
    - `{usps}` - Unique selling points list
    - `{tone_prompt}` - Selected tone prompt
    - `{brand_voice_guidance}` - Brand voice guide (if provided)
    - `{product_details}` - Formatted product information
    - `{description}` - Description text to process
    - `{keywords}` - SEO keywords list
    - `{product_name}`, `{category}`, `{primary_benefit}` - Product attributes
    - `{descriptions_json}` - Multiple descriptions for consistency check
    - `{sample_description}` - Sample text for brand voice analysis
    - `{tone}` - Current tone name
    """)


if __name__ == "__main__":
    main()
