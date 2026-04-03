"""Page 2: Review - Review and edit generated descriptions."""

from typing import Dict, Any, List
import json

import pandas as pd
import streamlit as st

from core.database import save_product, update_product_status, get_product
from core.pipeline import generate_description
from core.prompts import VALIDATOR_PROMPT
from core.llm_client import llm


def initialize_page_state():
    """Ensure required session state exists."""
    if "results" not in st.session_state:
        st.session_state.results = None
    if "catalog_df" not in st.session_state:
        st.session_state.catalog_df = None
    if "consistency_warnings" not in st.session_state:
        st.session_state.consistency_warnings = []


def get_quality_badge_color(score: int) -> str:
    """Return CSS class for quality score badge."""
    if score >= 8:
        return "quality-badge-green"
    elif score >= 5:
        return "quality-badge-amber"
    else:
        return "quality-badge-red"


def render_quality_badge(score: int) -> str:
    """Render HTML for quality score badge."""
    color_class = get_quality_badge_color(score)
    return f'<span class="{color_class}">{score}/10</span>'


def render_metrics():
    """Render the metrics row at the top of the page."""
    results = st.session_state.results

    if not results:
        return

    total = len(results)
    avg_quality = sum(r["quality_score"] for r in results) / total if total > 0 else 0
    avg_time = sum(r["generation_time_ms"] for r in results) / total if total > 0 else 0
    consistency_warnings = len(st.session_state.consistency_warnings)

    # Determine color for quality score
    if avg_quality >= 8:
        quality_delta = f"{avg_quality:.1f} (Excellent)"
        quality_color = "normal"
    elif avg_quality >= 5:
        quality_delta = f"{avg_quality:.1f} (Good)"
        quality_color = "normal"
    else:
        quality_delta = f"{avg_quality:.1f} (Needs Improvement)"
        quality_color = "inverse"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total SKUs", total)
    col2.metric("Avg Quality Score", quality_delta, delta_color=quality_color)
    col3.metric("Avg Generation Time", f"{avg_time:.0f}ms")
    col4.metric("Consistency Warnings", consistency_warnings, delta_color="inverse" if consistency_warnings > 0 else "normal")


def render_filters() -> Dict[str, Any]:
    """Render the filter sidebar and return filter state."""
    st.sidebar.markdown("### Filters")

    # Get unique categories from results
    results = st.session_state.results
    categories = list(set(r["category"] for r in results))

    # Category filter
    selected_categories = st.sidebar.multiselect(
        "Category",
        options=categories,
        default=categories
    )

    # Quality score filter
    min_quality = st.sidebar.slider(
        "Min Quality Score",
        min_value=0,
        max_value=10,
        value=0
    )

    # Show flagged only toggle
    show_flagged_only = st.sidebar.checkbox("Show Low Quality Only (<5)", value=False)

    return {
        "categories": selected_categories,
        "min_quality": min_quality,
        "show_flagged_only": show_flagged_only
    }


def filter_results(results: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
    """Filter results based on filter criteria."""
    filtered = results

    # Category filter
    if filters["categories"]:
        filtered = [r for r in filtered if r["category"] in filters["categories"]]

    # Quality filter
    if filters["min_quality"] > 0:
        filtered = [r for r in filtered if r["quality_score"] >= filters["min_quality"]]

    # Flagged only filter
    if filters["show_flagged_only"]:
        filtered = [r for r in filtered if r["quality_score"] < 5]

    return filtered


def run_validator(description: str, product_name: str, category: str) -> dict:
    """Run the LLM validator on a description.

    Args:
        description: The product description to validate
        product_name: Name of the product
        category: Product category

    Returns:
        Dict with validation results
    """
    prompt = VALIDATOR_PROMPT.format(
        description=description,
        product_name=product_name,
        category=category
    )

    try:
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)

        # Parse JSON response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)
        return result
    except Exception as e:
        return {
            "passed": False,
            "grammar_score": 0,
            "tone_score": 0,
            "issues": [f"Validation error: {str(e)}"],
            "suggestion": "Please retry validation"
        }


def render_result_card(result: Dict[str, Any], index: int):
    """Render a single result card."""
    score = result["quality_score"]
    badge_html = render_quality_badge(score)

    # Card header
    with st.expander(
        f"{result['product_name']} | {result['category']} | Quality: {score}/10 | Time: {result['generation_time_ms']}ms",
        expanded=False
    ):
        # Header row with badges
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            st.markdown(f"### {result['product_name']}")
            st.caption(f"Category: {result['category']}")

        with col2:
            st.markdown(f"<div style='text-align: center'>{badge_html}</div>", unsafe_allow_html=True)

        with col3:
            st.metric("Time", f"{result['generation_time_ms']}ms")

        with col4:
            if result["retry_count"] > 0:
                st.markdown('<span style="background-color: #F39C12; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">Retries: '
                           f'{result["retry_count"]}</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="color: #2ECC71; font-size: 12px;">✓ No retries</span>', unsafe_allow_html=True)

        # Conversion hook
        st.info(f"💡 **Hook**: {result['conversion_hook']}")

        # USPs
        st.markdown("#### Unique Selling Points")
        for i, usp in enumerate(result.get("usps", []), 1):
            st.markdown(f"{i}. {usp}")

        # Description tabs
        st.markdown("#### Description")
        tab_para, tab_bullets = st.tabs(["Paragraph", "Bullets"])

        with tab_para:
            st.markdown(result.get("description_long", "No description generated"))

        with tab_bullets:
            st.markdown(result.get("description_bullets", "No bullets generated"))

        # SEO Keywords
        keywords = result.get("seo_keywords_used", [])
        if keywords:
            st.markdown("#### SEO Keywords")
            keywords_html = " ".join(
                f'<span style="background-color: #3498db; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px;">{k}</span>'
                for k in keywords
            )
            st.markdown(f'<div style="margin: 8px 0">{keywords_html}</div>', unsafe_allow_html=True)

        # Quality feedback
        st.markdown("#### Quality Feedback")
        st.markdown(f"**Score**: {score}/10")
        st.markdown(f"**Reason**: {result.get('quality_reason', 'No feedback available')}")

        # Action buttons: Approve and Edit
        st.markdown("#### Actions")
        action_col1, action_col2, action_col3 = st.columns([1, 1, 3])

        with action_col1:
            if st.button("✅ Approve as is", key=f"approve_{result['sku_id']}"):
                approve_product(result)

        with action_col2:
            if st.button("✏️ Edit", key=f"edit_{result['sku_id']}"):
                st.session_state.edit_product_sku = result["sku_id"]
                st.switch_page("pages/4_Edit.py")

        # Regenerate button
        with action_col3:
            if st.button("🔄 Regenerate", key=f"regenerate_{result['sku_id']}"):
                regenerate_single_product(result)


def approve_product(result: Dict[str, Any]):
    """Run validator and approve product if it passes."""
    with st.spinner("Running LLM validator..."):
        validation_result = run_validator(
            description=result.get("description_long", ""),
            product_name=result.get("product_name", "Unknown"),
            category=result.get("category", "General")
        )

        # Show validation results
        st.markdown("### Validation Results")

        if validation_result.get("passed"):
            st.success("✅ **PASSED** - Description meets quality standards!")
        else:
            st.error("❌ **FAILED** - Description has issues")

        col1, col2 = st.columns(2)
        with col1:
            grammar_score = validation_result.get("grammar_score", 0)
            if grammar_score >= 7:
                st.metric("Grammar Score", f"{grammar_score}/10", delta="✓ Pass")
            else:
                st.metric("Grammar Score", f"{grammar_score}/10", delta="✗ Below threshold", delta_color="inverse")

        with col2:
            tone_score = validation_result.get("tone_score", 0)
            if tone_score >= 7:
                st.metric("Tone Score", f"{tone_score}/10", delta="✓ Pass")
            else:
                st.metric("Tone Score", f"{tone_score}/10", delta="✗ Below threshold", delta_color="inverse")

        if validation_result.get("issues"):
            st.markdown("#### Issues Found:")
            for issue in validation_result["issues"]:
                st.write(f"- {issue}")

        if validation_result.get("suggestion"):
            st.info(f"💡 **Suggestion**: {validation_result['suggestion']}")

        # Confirm approval
        if validation_result.get("passed"):
            # Save to database with approved status
            save_data = {
                "sku_id": result["sku_id"],
                "product_name": result["product_name"],
                "category": result["category"],
                "description_long": result.get("description_long", ""),
                "description_bullets": result.get("description_bullets", ""),
                "conversion_hook": result.get("conversion_hook", ""),
                "quality_score": result.get("quality_score"),
                "features": result.get("usps", []),
                "status": "approved"
            }
            save_product(save_data)
            st.success("Product approved and saved to database!")

            # Update session state results
            for i, r in enumerate(st.session_state.results):
                if r["sku_id"] == result["sku_id"]:
                    st.session_state.results[i]["status"] = "approved"
                    break

            if st.button("Continue"):
                st.rerun()
        else:
            st.warning("Description did not pass validation. Please edit and improve it before approving.")


def regenerate_single_product(original_result: Dict[str, Any]):
    """Regenerate a single product description."""
    # Find the original row in catalog
    catalog_df = st.session_state.catalog_df
    if catalog_df is None:
        st.error("No catalog data available")
        return

    sku_id = original_result["sku_id"]
    row = catalog_df[catalog_df["sku_id"] == sku_id]

    if row.empty:
        st.error(f"Product with SKU {sku_id} not found in catalog")
        return

    with st.spinner(f"Regenerating description for {original_result['product_name']}..."):
        try:
            new_result = generate_description(
                product_row=row.iloc[0],
                tone=st.session_state.selected_tone,
                brand_voice_guide=st.session_state.brand_voice_guide,
                max_retries=2
            )

            # Update results
            results = st.session_state.results
            for i, r in enumerate(results):
                if r["sku_id"] == sku_id:
                    results[i] = new_result
                    break

            st.session_state.results = results
            st.success("Regenerated successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Error regenerating: {e}")


def render_consistency_warnings():
    """Render the consistency warnings section at the bottom."""
    warnings = st.session_state.consistency_warnings

    if not warnings:
        return

    st.markdown("---")
    st.markdown("### ⚠️ Consistency Warnings")
    st.markdown("The following descriptions deviate from the expected tone or style:")

    for warning in warnings:
        sku_id = warning.get("sku_id", "Unknown")
        reason = warning.get("reason", "No reason provided")

        # Find the product name
        results = st.session_state.results
        product_name = next(
            (r["product_name"] for r in results if r["sku_id"] == sku_id),
            "Unknown Product"
        )

        st.warning(f"**{product_name}** ({sku_id}): {reason}")


def main():
    """Main page content."""
    initialize_page_state()

    st.title("🔍 Review Descriptions")
    st.markdown("Review, filter, and regenerate your AI-generated product descriptions")

    # Check if results exist
    if not st.session_state.results:
        st.warning("⚠️ No results available yet. Please generate descriptions first on the **Generate** page.")
        st.info("Navigate to **Generate** in the sidebar to start creating descriptions.")
        return

    # Render metrics
    render_metrics()

    st.markdown("---")

    # Render filters and get filtered results
    filters = render_filters()
    filtered_results = filter_results(st.session_state.results, filters)

    # Results count
    st.markdown(f"### Results ({len(filtered_results)} of {len(st.session_state.results)} shown)")

    if not filtered_results:
        st.info("No results match your filters. Try adjusting the filter criteria.")
        return

    # Render result cards
    for idx, result in enumerate(filtered_results):
        render_result_card(result, idx)

    # Consistency warnings at bottom
    render_consistency_warnings()


if __name__ == "__main__":
    main()
