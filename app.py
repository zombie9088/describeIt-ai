"""DescribeIt AI - Main Streamlit Application."""

import streamlit as st
import pandas as pd
from datetime import datetime

from core.database import init_db, get_all_products, search_products, save_product, update_product_status
from core.pipeline import generate_description
from core.prompts import VALIDATOR_PROMPT
from core.llm_client import get_ollama_client

ollama = get_ollama_client()

# Initialize database on startup
init_db()

# Set page config
st.set_page_config(
    page_title="DescribeIt AI",
    page_icon="✨",
    layout="wide"
)

# Custom CSS for badge styling
st.markdown("""
<style>
    .quality-badge-green {
        background-color: #2ECC71;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .quality-badge-amber {
        background-color: #F39C12;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .quality-badge-red {
        background-color: #E74C3C;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .feature-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #3498db;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        text-align: center;
    }
    .status-badge-draft {
        background-color: #95a5a6;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85em;
    }
    .status-badge-approved {
        background-color: #2ECC71;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85em;
    }
    .status-badge-manual_draft {
        background-color: #3498db;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85em;
    }
    .status-badge-needs_review {
        background-color: #F39C12;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85em;
    }
    .status-badge-rejected {
        background-color: #E74C3C;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)


def get_status_badge_class(status: str) -> str:
    """Get the CSS class for a status badge."""
    status_classes = {
        "draft": "status-badge-draft",
        "approved": "status-badge-approved",
        "manual_draft": "status-badge-manual_draft",
        "needs_review": "status-badge-needs_review",
        "rejected": "status-badge-rejected"
    }
    return status_classes.get(status, "status-badge-draft")


def render_status_badge(status: str) -> str:
    """Render a status badge HTML."""
    badge_class = get_status_badge_class(status)
    return f'<span class="{badge_class}">{status.replace("_", " ").title()}</span>'


def initialize_session_state():
    """Initialize session state with default values."""
    defaults = {
        "catalog_df": None,
        "results": None,
        "brand_voice_guide": None,
        "selected_tone": "Professional",
        "validation_report": None,
        "quality_threshold": 7,
        "consistency_warnings": [],
        "show_manual_entry": False
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
        import json
        response_text = ollama.generate(prompt)

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


def main():
    """Main application entry point."""
    initialize_session_state()

    # Header
    st.title("✨ DescribeIt AI")
    st.markdown("*GenAI-Powered Product Description Generator for E-Commerce Retailers*")

    st.markdown("---")

    # Entry point buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 AI Agent (batch)", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Generate.py")
    with col2:
        if st.button("✍️ Manual Entry", use_container_width=True):
            st.session_state.show_manual_entry = not st.session_state.get("show_manual_entry", False)
            st.rerun()

    st.markdown("---")

    # Manual entry form (conditionally shown)
    if st.session_state.get("show_manual_entry", False):
        st.markdown("### Manual Product Entry")

        with st.form("manual_entry_form"):
            col_a, col_b = st.columns(2)

            with col_a:
                product_name = st.text_input("Product Name *", key="manual_product_name")
                category = st.text_input("Category", key="manual_category")
                brand = st.text_input("Brand", key="manual_brand")
                price = st.number_input("Price ($)", min_value=0.0, step=0.01, key="manual_price")

            with col_b:
                features = st.text_area("Features (comma-separated)", key="manual_features",
                                        help="Enter features separated by commas")
                specs = st.text_area("Specifications (key:value per line)", key="manual_specs",
                                     help="Enter specs like 'Weight: 500g' on separate lines")
                target_audience = st.text_input("Target Audience", key="manual_target",
                                                value="General audience")
                keywords = st.text_area("SEO Keywords (comma-separated)", key="manual_keywords")

            submit_btn = st.form_submit_button("Save to Database", type="primary")

            if submit_btn:
                if not product_name:
                    st.error("Product name is required!")
                else:
                    # Generate SKU from product name
                    import hashlib
                    sku_id = hashlib.md5(f"{product_name}{datetime.now().isoformat()}".encode()).hexdigest()[:12]

                    # Parse features
                    features_list = [f.strip() for f in features.split(",") if f.strip()] if features else []

                    # Parse specs
                    specs_dict = {}
                    if specs:
                        for line in specs.split("\n"):
                            if ":" in line:
                                key, value = line.split(":", 1)
                                specs_dict[key.strip()] = value.strip()

                    # Parse keywords
                    keywords_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []

                    # Create product record
                    product_data = {
                        "sku_id": sku_id,
                        "product_name": product_name,
                        "category": category or "General",
                        "brand": brand or "Unknown",
                        "price": price or 0,
                        "features": features_list,
                        "specs": specs_dict,
                        "target_audience": target_audience,
                        "keywords": keywords_list,
                        "status": "manual_draft",
                        "description_long": "",
                        "description_bullets": "",
                        "conversion_hook": "",
                        "quality_score": None
                    }

                    save_product(product_data)
                    st.success(f"Product '{product_name}' saved to database!")
                    st.session_state.show_manual_entry = False
                    st.rerun()

        # Generate description button for manual entry
        if st.button("📝 Generate Description for Manual Entry Product"):
            st.info("Navigate to the Generate page to batch-generate descriptions for manual draft products.")

        st.markdown("---")

    # Search bar
    st.markdown("### Product Database")
    search_query = st.text_input("🔍 Search Products", placeholder="Search by product name...",
                                 key="product_search", label_visibility="collapsed")

    # Get products from database
    if search_query:
        products_df = search_products(search_query)
    else:
        products_df = get_all_products()

    # Display products table
    if not products_df.empty:
        st.markdown(f"Found {len(products_df)} product(s)")

        # Create display dataframe with formatted columns
        display_df = products_df.copy()

        # Add status badge column
        display_df["status_badge"] = display_df["status"].apply(render_status_badge)

        # Select and rename columns for display
        display_columns = ["sku_id", "product_name", "category", "description_long",
                          "quality_score", "status_badge", "created_at"]

        # Build the table with custom rendering
        for idx, row in products_df.iterrows():
            cols = st.columns([1, 2, 1, 3, 1, 1, 1])

            cols[0].write(f"`{row['sku_id']}`")
            cols[1].write(row["product_name"])
            cols[2].write(row["category"])

            # Truncate description for display
            desc = row.get("description_long", "")
            if desc and len(desc) > 100:
                desc = desc[:100] + "..."
            cols[3].write(desc if desc else "*No description*")

            # Quality score
            qs = row.get("quality_score")
            if qs:
                if qs >= 7:
                    cols[4].markdown(f'<span class="quality-badge-green">{qs}/10</span>',
                                     unsafe_allow_html=True)
                elif qs >= 4:
                    cols[4].markdown(f'<span class="quality-badge-amber">{qs}/10</span>',
                                     unsafe_allow_html=True)
                else:
                    cols[4].markdown(f'<span class="quality-badge-red">{qs}/10</span>',
                                     unsafe_allow_html=True)
            else:
                cols[4].write("-")

            # Status badge
            cols[5].markdown(render_status_badge(row["status"]), unsafe_allow_html=True)

            # Created date
            cols[6].write(str(row.get("created_at", ""))[:10])

        st.markdown("---")

        # Quick actions for products
        st.markdown("### Quick Actions")
        action_col1, action_col2 = st.columns(2)

        with action_col1:
            if st.button("📤 Export All Products", use_container_width=True):
                st.switch_page("pages/3_Export.py")

        with action_col2:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
    else:
        st.info("No products found in database. Use 'AI Agent (batch)' or 'Manual Entry' to add products.")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Built with Streamlit and GenAI | Ready to describe your products?"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
