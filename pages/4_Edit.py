"""Page 4: Edit - Edit product descriptions with LLM validation."""

import json

import streamlit as st

from core.database import get_product, save_product, update_product_fields
from core.prompts import VALIDATOR_PROMPT
from core.llm_client import llm


def initialize_page_state():
    """Ensure required session state exists."""
    if "edit_product_sku" not in st.session_state:
        st.session_state.edit_product_sku = None
    if "validator_ran" not in st.session_state:
        st.session_state.validator_ran = False
    if "last_validation_result" not in st.session_state:
        st.session_state.last_validation_result = None


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


def main():
    """Main page content."""
    initialize_page_state()

    st.title("✏️ Edit Product Description")
    st.markdown("Edit and validate product descriptions before saving")

    # Check if we have a product to edit
    sku_id = st.session_state.edit_product_sku

    if not sku_id:
        st.warning("⚠️ No product selected for editing")
        st.info("Navigate to the Review page and click 'Edit' on a product to edit it.")

        if st.button("← Back to Review"):
            st.switch_page("pages/2_Review.py")
        return

    # Load product from database
    product = get_product(sku_id)

    if not product:
        st.error(f"Product with SKU {sku_id} not found in database")
        if st.button("← Back to Review"):
            st.session_state.edit_product_sku = None
            st.switch_page("pages/2_Review.py")
        return

    # Display product info
    st.markdown(f"### {product['product_name']}")
    st.caption(f"SKU: `{product['sku_id']}` | Category: {product['category']} | Status: {product['status']}")

    st.markdown("---")

    # Editable description
    st.markdown("### Edit Description")

    edited_description = st.text_area(
        "Long Description",
        value=product.get("description_long", ""),
        height=300,
        key="edit_description_long",
        help="Edit the product description. Run the validator to check quality before saving."
    )

    # Edit bullets (optional)
    edited_bullets = st.text_area(
        "Bullet Points (optional)",
        value=product.get("description_bullets", ""),
        height=150,
        key="edit_description_bullets",
        help="Edit bullet points summarizing key features"
    )

    st.markdown("---")

    # Validator section
    st.markdown("### LLM Validator")

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("🔍 Run LLM Validator", use_container_width=True, type="primary"):
            with st.spinner("Validating description..."):
                validation_result = run_validator(
                    description=edited_description,
                    product_name=product["product_name"],
                    category=product["category"]
                )

                st.session_state.last_validation_result = validation_result
                st.session_state.validator_ran = True
                st.rerun()

    # Show validation results if validator has run
    if st.session_state.validator_ran and st.session_state.last_validation_result:
        validation = st.session_state.last_validation_result

        st.markdown("### Validation Results")

        if validation.get("passed"):
            st.success("✅ **PASSED** - Description meets quality standards!")
        else:
            st.error("❌ **FAILED** - Description has issues")

        # Scores
        col_a, col_b = st.columns(2)
        with col_a:
            grammar_score = validation.get("grammar_score", 0)
            if grammar_score >= 7:
                st.metric("Grammar Score", f"{grammar_score}/10", delta="✓ Pass")
            else:
                st.metric("Grammar Score", f"{grammar_score}/10", delta="✗ Below threshold", delta_color="inverse")

        with col_b:
            tone_score = validation.get("tone_score", 0)
            if tone_score >= 7:
                st.metric("Tone Score", f"{tone_score}/10", delta="✓ Pass")
            else:
                st.metric("Tone Score", f"{tone_score}/10", delta="✗ Below threshold", delta_color="inverse")

        if validation.get("issues"):
            st.markdown("#### Issues Found:")
            for issue in validation["issues"]:
                st.write(f"- {issue}")

        if validation.get("suggestion"):
            st.info(f"💡 **Suggestion**: {validation['suggestion']}")

    st.markdown("---")

    # Save buttons
    st.markdown("### Save Changes")

    save_col1, save_col2, back_col = st.columns([1, 1, 1])

    with save_col1:
        # Save to DB button - only enabled after validator runs
        save_disabled = not st.session_state.validator_ran

        if st.button(
            "💾 Save to DB",
            use_container_width=True,
            type="primary",
            disabled=save_disabled,
            help="Save changes to database (validator must be run first)" if save_disabled else "Save validated changes"
        ):
            # Check if validation passed
            validation = st.session_state.last_validation_result

            if validation and validation.get("passed"):
                # Save with approved status
                update_data = {
                    "description_long": edited_description,
                    "description_bullets": edited_bullets,
                    "status": "approved"
                }
                update_product_fields(sku_id, update_data)

                # Also update the full product record
                product["description_long"] = edited_description
                product["description_bullets"] = edited_bullets
                product["status"] = "approved"
                save_product(product)

                st.success("Description saved to database with 'approved' status!")
                st.session_state.validator_ran = False
                st.session_state.last_validation_result = None

                if st.button("Continue Editing"):
                    st.rerun()
                else:
                    st.session_state.edit_product_sku = None
                    st.switch_page("pages/2_Review.py")
            else:
                st.warning("Validation did not pass. Use 'Override & Save' to save anyway, or edit the description and re-run validator.")

    with save_col2:
        # Override & Save button - saves even if validator flagged issues
        if st.button("⚠️ Override & Save", use_container_width=True):
            # Save without checking validation status
            update_data = {
                "description_long": edited_description,
                "description_bullets": edited_bullets,
                "status": "needs_review"  # Mark for review since it didn't pass validation
            }
            update_product_fields(sku_id, update_data)

            # Also update the full product record
            product["description_long"] = edited_description
            product["description_bullets"] = edited_bullets
            product["status"] = "needs_review"
            save_product(product)

            st.warning("Description saved with 'needs_review' status (did not pass validation)")
            st.session_state.validator_ran = False
            st.session_state.last_validation_result = None

            if st.button("Continue", key="override_continue"):
                st.rerun()
            else:
                st.session_state.edit_product_sku = None
                st.switch_page("pages/2_Review.py")

    with back_col:
        if st.button("← Cancel", use_container_width=True):
            st.session_state.edit_product_sku = None
            st.session_state.validator_ran = False
            st.session_state.last_validation_result = None
            st.switch_page("pages/2_Review.py")

    # Footer info
    st.markdown("---")
    st.info("""
    **How to use:**
    1. Edit the description in the text area above
    2. Click "Run LLM Validator" to check grammar, tone, and quality
    3. If it passes (grammar ≥7 AND tone ≥7), click "Save to DB"
    4. If issues are flagged, you can either fix them and re-validate, or use "Override & Save"
    """)


if __name__ == "__main__":
    main()
