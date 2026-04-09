"""Page 1: Generate - Batch description generation."""

import json
from typing import Dict, Any

import pandas as pd
import streamlit as st

from core.preprocessor import preprocess
from core.synthetic_data import generate_synthetic_catalog, load_catalog
from core.pipeline import run_batch, check_batch_consistency, analyze_brand_voice, set_cache_enabled, get_cache_stats
from core.prompts import TONE_PROMPTS


def initialize_page_state():
    """Ensure required session state exists."""
    if "catalog_df" not in st.session_state:
        st.session_state.catalog_df = None
    if "results" not in st.session_state:
        st.session_state.results = None
    if "brand_voice_guide" not in st.session_state:
        st.session_state.brand_voice_guide = None
    if "selected_tone" not in st.session_state:
        st.session_state.selected_tone = "Professional"
    if "validation_report" not in st.session_state:
        st.session_state.validation_report = None
    if "quality_threshold" not in st.session_state:
        st.session_state.quality_threshold = 7
    if "consistency_warnings" not in st.session_state:
        st.session_state.consistency_warnings = []


def render_upload_tab() -> bool:
    """Render the file upload tab. Returns True if data was successfully loaded."""
    uploaded_file = st.file_uploader(
        "Upload your product catalog",
        type=["csv", "json"],
        help="Upload a CSV or JSON file with product data"
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_json(uploaded_file)

            # Preprocess
            cleaned_df, validation_report = preprocess(df)

            st.session_state.catalog_df = cleaned_df
            st.session_state.validation_report = validation_report

            # Show validation report
            st.success(f"Loaded {validation_report['total']} products!")

            # Metrics row
            col1, col2, col3 = st.columns(3)
            col1.metric("Total SKUs", validation_report["total"])
            col2.metric("Valid", validation_report["valid"])

            flagged_count = validation_report["total"] - validation_report["valid"]
            col3.metric("Flagged", flagged_count, delta_color="inverse" if flagged_count > 0 else "normal")

            # Show flagged issues in expander
            if validation_report["flagged"]:
                with st.expander(f"View {len(validation_report['flagged'])} flagged issues"):
                    for issue in validation_report["flagged"]:
                        if "sku_id" in issue:
                            st.warning(f"**{issue['sku_id']}**: {', '.join(issue.get('issues', []))}")
                        else:
                            st.error(issue.get("message", "Unknown issue"))

            # Preview
            st.markdown("### Preview (first 5 rows)")
            st.dataframe(cleaned_df.head(5), use_container_width=True)

            return True

        except Exception as e:
            st.error(f"Error loading file: {e}")
            return False

    return False


def render_synthetic_tab() -> bool:
    """Render the synthetic data tab. Returns True if data was generated."""
    n_products = st.slider(
        "Number of products to generate",
        min_value=10,
        max_value=100,
        value=50,
        step=5
    )

    if st.button("Generate Catalog", type="primary"):
        with st.spinner("Generating synthetic product catalog..."):
            try:
                df = generate_synthetic_catalog(n_products)
                cleaned_df, validation_report = preprocess(df)

                st.session_state.catalog_df = cleaned_df
                st.session_state.validation_report = validation_report

                st.success(f"Generated {validation_report['total']} synthetic products!")

                # Metrics
                col1, col2 = st.columns(2)
                col1.metric("Products Generated", validation_report["total"])
                col2.metric("Categories", cleaned_df["category"].nunique())

                # Show distribution
                st.markdown("### Category Distribution")
                st.bar_chart(cleaned_df["category"].value_counts())

                # Preview
                st.markdown("### Preview (first 5 rows)")
                st.dataframe(cleaned_df.head(5), use_container_width=True)

                return True

            except Exception as e:
                st.error(f"Error generating catalog: {e}")
                return False

    return False


def render_manual_tab() -> bool:
    """Render the manual entry tab. Returns True if product was added."""
    st.markdown("### Add a Single Product")

    with st.form("manual_product_form"):
        col1, col2 = st.columns(2)

        with col1:
            product_name = st.text_input("Product Name *")
            category = st.selectbox(
                "Category *",
                ["Electronics", "Apparel", "Home & Kitchen", "Sports & Fitness"]
            )
            brand = st.text_input("Brand *")
            price = st.number_input("Price ($)", min_value=0.0, step=0.01)

        with col2:
            target_audience = st.text_input("Target Audience")
            keywords = st.text_input("Keywords (comma-separated)")
            features_text = st.text_area(
                "Features (comma-separated)",
                placeholder="Feature 1, Feature 2, Feature 3"
            )
            specs_text = st.text_area(
                "Specifications (key:value per line)",
                placeholder="weight: 200g\ndimensions: 10x5x3 cm"
            )

        submitted = st.form_submit_button("Add Product", type="primary")

        if submitted:
            if not product_name or not brand:
                st.error("Product Name and Brand are required!")
                return False

            # Parse features
            features = [f.strip() for f in features_text.split(",") if f.strip()] if features_text else []

            # Parse specs
            specs = {}
            if specs_text:
                for line in specs_text.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        specs[key.strip()] = value.strip()

            # Parse keywords
            keywords_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []

            # Create new row
            new_row = {
                "sku_id": f"SKU-MANUAL-{len(st.session_state.catalog_df) + 1 if st.session_state.catalog_df is not None else 1:03d}",
                "product_name": product_name.strip().title(),
                "category": category,
                "brand": brand,
                "price": price,
                "features": features,
                "specs": specs,
                "target_audience": target_audience or "General audience",
                "keywords": keywords_list,
                "_flagged": False
            }

            # Add to session state
            if st.session_state.catalog_df is None:
                st.session_state.catalog_df = pd.DataFrame([new_row])
            else:
                new_df = pd.DataFrame([new_row])
                st.session_state.catalog_df = pd.concat(
                    [st.session_state.catalog_df, new_df],
                    ignore_index=True
                )

            st.success(f"Added '{product_name}' to catalog!")
            return True

    return False


def render_brand_voice_section():
    """Render the brand voice configuration section."""
    with st.expander("Brand Voice Configuration (optional)"):
        st.markdown("""
        **Analyze your brand's writing style** by pasting an existing product description.
        The AI will extract your tone, sentence style, and formality to match future generations.
        """)

        sample_description = st.text_area(
            "Paste a sample product description from your brand",
            height=150,
            placeholder="Paste your existing product description here..."
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Analyze Brand Voice", disabled=not sample_description):
                with st.spinner("Analyzing your brand voice..."):
                    try:
                        brand_voice = analyze_brand_voice(sample_description)
                        st.session_state.brand_voice_guide = brand_voice

                        st.success("Brand voice analyzed!")

                        # Display as table
                        voice_df = pd.DataFrame([
                            {"Attribute": "Tone", "Value": brand_voice.get("tone", "N/A")},
                            {"Attribute": "Sentence Style", "Value": brand_voice.get("sentence_style", "N/A")},
                            {"Attribute": "Avg Sentence Length", "Value": brand_voice.get("avg_sentence_length", "N/A")},
                            {"Attribute": "Adjective Density", "Value": brand_voice.get("adjective_density", "N/A")},
                            {"Attribute": "Formality", "Value": brand_voice.get("formality", "N/A")}
                        ])
                        st.table(voice_df)

                    except Exception as e:
                        st.error(f"Error analyzing brand voice: {e}")

        if st.session_state.brand_voice_guide:
            with col2:
                st.info("✓ Brand voice guide is configured and will be applied to generations")


def render_generation_config():
    """Render the generation configuration section."""
    st.markdown("### Generation Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        tone = st.selectbox(
            "Select Tone",
            options=list(TONE_PROMPTS.keys()),
            index=0,
            help="Choose the writing style for your product descriptions"
        )
        st.session_state.selected_tone = tone

    with col2:
        quality_threshold = st.slider(
            "Quality Threshold",
            min_value=5,
            max_value=9,
            value=7,
            help="Minimum quality score before retrying generation (higher = stricter)"
        )
        st.session_state.quality_threshold = quality_threshold

    with col3:
        concurrency = st.slider(
            "Parallel Processing",
            min_value=1,
            max_value=10,
            value=5,
            help="Number of products to generate in parallel"
        )

    # Cache toggle
    cache_stats = get_cache_stats()
    col_cache1, col_cache2 = st.columns([3, 1])
    with col_cache1:
        enable_cache = st.checkbox(
            "Enable Response Cache",
            value=True,
            help="Cache LLM responses to avoid redundant calls (faster for similar products)"
        )
        set_cache_enabled(enable_cache)
    with col_cache2:
        if cache_stats["size"] > 0:
            st.info(f"Cache: {cache_stats['size']} entries")

    # Generate button
    if st.button("Generate All Descriptions", type="primary", disabled=st.session_state.catalog_df is None):
        run_generation(tone, quality_threshold, concurrency)


def run_generation(tone: str, quality_threshold: int, concurrency: int = 5):
    """Run the batch generation process."""
    df = st.session_state.catalog_df

    if df is None or len(df) == 0:
        st.error("No product data available. Please upload or generate a catalog first.")
        return

    # Progress container
    progress_container = st.container()
    status_container = st.container()

    with progress_container:
        progress_bar = st.progress(0)
        progress_text = st.empty()

    with status_container:
        status = st.status("Starting generation...", expanded=True)

    # Callback for progress updates
    def progress_callback(current: int, total: int, product_name: str):
        progress = (current + 1) / total
        progress_bar.progress(progress)
        progress_text.text(f"Processing: {product_name} ({current + 1}/{total})")
        status.write(f"✓ Generated: {product_name}")

    try:
        # Run batch generation with concurrency
        results = run_batch(
            df=df,
            tone=tone,
            brand_voice_guide=st.session_state.brand_voice_guide,
            progress_callback=progress_callback,
            concurrency=concurrency
        )

        # Check consistency
        status.write("Checking consistency across descriptions...")
        consistency_warnings = check_batch_consistency(results, tone)
        st.session_state.consistency_warnings = consistency_warnings

        # Save results
        st.session_state.results = results

        status.update(label="Generation complete!", state="complete", expanded=False)
        progress_bar.progress(1.0)
        progress_text.text("Generation complete!")

        # Show summary
        st.success("Generation completed successfully!")

        # Summary metrics
        total = len(results)
        avg_quality = sum(r["quality_score"] for r in results) / total if total > 0 else 0
        avg_time = sum(r["generation_time_ms"] for r in results) / total if total > 0 else 0
        total_retries = sum(r["retry_count"] for r in results)
        cache_stats = get_cache_stats()

        st.markdown("### Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Generated", total)
        col2.metric("Avg Quality Score", f"{avg_quality:.1f}/10")
        col3.metric("Avg Time/SKU", f"{avg_time:.0f}ms")
        col4.metric("Consistency Warnings", len(consistency_warnings))

        if cache_stats["size"] > 0:
            st.info(f"📦 Cache populated with {cache_stats['size']} responses")

        if total_retries > 0:
            st.info(f"Total retries across all products: {total_retries}")

        if consistency_warnings:
            with st.expander("View Consistency Warnings"):
                for warning in consistency_warnings:
                    st.warning(f"**{warning.get('sku_id', 'Unknown')}**: {warning.get('reason', 'No reason')}")

        # Navigate to Review
        st.markdown("---")
        st.info("🎉 Ready to review! Navigate to **Review** in the sidebar to see your results.")

    except Exception as e:
        status.update(label="Generation failed", state="error", expanded=True)
        st.error(f"Error during generation: {e}")


def main():
    """Main page content."""
    initialize_page_state()

    st.title("📦 Generate Descriptions")
    st.markdown("Upload your product catalog and generate AI-powered descriptions")

    # Section A: Data Input
    st.markdown("### Section A: Data Input")

    tab1, tab2, tab3 = st.tabs(["Upload File", "Use Synthetic Data", "Manual Entry"])

    with tab1:
        render_upload_tab()

    with tab2:
        render_synthetic_tab()

    with tab3:
        render_manual_tab()

    # Show current catalog status
    if st.session_state.catalog_df is not None:
        st.markdown("---")
        st.info(f"📊 Current catalog: {len(st.session_state.catalog_df)} products ready for generation")

    # Section B: Brand Voice
    st.markdown("---")
    st.markdown("### Section B: Brand Voice")
    render_brand_voice_section()

    # Section C: Generation Config
    st.markdown("---")
    render_generation_config()


if __name__ == "__main__":
    main()
