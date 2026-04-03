"""Page 3: Export - Export generated descriptions."""

import json
from io import StringIO

import pandas as pd
import streamlit as st


def initialize_page_state():
    """Ensure required session state exists."""
    if "results" not in st.session_state:
        st.session_state.results = None


def render_summary_stats():
    """Render summary statistics."""
    results = st.session_state.results

    if not results:
        return

    total = len(results)
    avg_quality = sum(r["quality_score"] for r in results) / total if total > 0 else 0
    avg_time = sum(r["generation_time_ms"] for r in results) / total if total > 0 else 0
    total_retries = sum(r["retry_count"] for r in results)

    st.markdown("### Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products", total)
    col2.metric("Avg Quality Score", f"{avg_quality:.1f}/10")
    col3.metric("Avg Generation Time", f"{avg_time:.0f}ms")
    col4.metric("Total Retries", total_retries)


def create_full_results_df(results) -> pd.DataFrame:
    """Create DataFrame with all result fields."""
    rows = []
    for r in results:
        rows.append({
            "sku_id": r.get("sku_id", ""),
            "product_name": r.get("product_name", ""),
            "category": r.get("category", ""),
            "usps": json.dumps(r.get("usps", [])),
            "conversion_hook": r.get("conversion_hook", ""),
            "description_long": r.get("description_long", ""),
            "description_bullets": r.get("description_bullets", ""),
            "quality_score": r.get("quality_score", 0),
            "quality_reason": r.get("quality_reason", ""),
            "generation_time_ms": r.get("generation_time_ms", 0),
            "retry_count": r.get("retry_count", 0),
            "seo_keywords_used": json.dumps(r.get("seo_keywords_used", []))
        })
    return pd.DataFrame(rows)


def create_long_descriptions_only_df(results) -> pd.DataFrame:
    """Create DataFrame with long descriptions only."""
    rows = []
    for r in results:
        rows.append({
            "sku_id": r.get("sku_id", ""),
            "product_name": r.get("product_name", ""),
            "description_long": r.get("description_long", ""),
            "conversion_hook": r.get("conversion_hook", "")
        })
    return pd.DataFrame(rows)


def create_bullets_only_df(results) -> pd.DataFrame:
    """Create DataFrame with bullet descriptions only."""
    rows = []
    for r in results:
        rows.append({
            "sku_id": r.get("sku_id", ""),
            "product_name": r.get("product_name", ""),
            "description_bullets": r.get("description_bullets", "")
        })
    return pd.DataFrame(rows)


def df_to_csv(df: pd.DataFrame) -> str:
    """Convert DataFrame to CSV string."""
    return df.to_csv(index=False)


def render_export_options():
    """Render the export options section."""
    results = st.session_state.results

    if not results:
        return

    st.markdown("### Export Options")
    st.markdown("Choose your preferred export format:")

    col1, col2, col3 = st.columns(3)

    # Column 1: Full results
    with col1:
        st.markdown("#### 📊 Full Results (CSV)")
        st.markdown("All fields including USPs, both description variants, quality scores, and metadata")

        full_df = create_full_results_df(results)
        full_csv = df_to_csv(full_df)

        st.download_button(
            label="Download Full CSV",
            data=full_csv,
            file_name="product_descriptions_full.csv",
            mime="text/csv",
            key="download_full"
        )

        with st.expander("Preview columns"):
            st.write(list(full_df.columns))

    # Column 2: Long descriptions only
    with col2:
        st.markdown("#### 📝 Long Descriptions Only")
        st.markdown("SKU, product name, paragraph description, and conversion hook")

        long_df = create_long_descriptions_only_df(results)
        long_csv = df_to_csv(long_df)

        st.download_button(
            label="Download Long Descriptions CSV",
            data=long_csv,
            file_name="product_descriptions_long.csv",
            mime="text/csv",
            key="download_long"
        )

        with st.expander("Preview"):
            st.dataframe(long_df.head(3), use_container_width=True)

    # Column 3: Bullets only
    with col3:
        st.markdown("#### • Bullet Points Only")
        st.markdown("SKU, product name, and bullet-point descriptions")

        bullets_df = create_bullets_only_df(results)
        bullets_csv = df_to_csv(bullets_df)

        st.download_button(
            label="Download Bullets CSV",
            data=bullets_csv,
            file_name="product_descriptions_bullets.csv",
            mime="text/csv",
            key="download_bullets"
        )

        with st.expander("Preview"):
            st.dataframe(bullets_df.head(3), use_container_width=True)


def render_json_copy():
    """Render the JSON copy helper."""
    results = st.session_state.results

    if not results:
        return

    st.markdown("---")
    st.markdown("### 📋 Copy JSON to Clipboard")

    st.markdown("Full results as JSON (useful for API integrations or backup):")

    json_str = json.dumps(results, indent=2)

    st.code(json_str, language="json")

    st.info("💡 Tip: Click the 'Copy' button in the top-right corner of the code block above")


def main():
    """Main page content."""
    initialize_page_state()

    st.title("📤 Export Results")
    st.markdown("Download your generated product descriptions in various formats")

    # Check if results exist
    if not st.session_state.results:
        st.warning("⚠️ No results available yet. Please generate descriptions first on the **Generate** page.")
        st.info("Navigate to **Generate** in the sidebar to start creating descriptions.")
        return

    # Render summary stats
    render_summary_stats()

    st.markdown("---")

    # Render export options
    render_export_options()

    # Render JSON copy helper
    render_json_copy()


if __name__ == "__main__":
    main()
