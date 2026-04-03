"""DescribeIt AI - Main Streamlit Application."""

import streamlit as st

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
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state with default values."""
    defaults = {
        "catalog_df": None,
        "results": None,
        "brand_voice_guide": None,
        "selected_tone": "Professional",
        "validation_report": None,
        "quality_threshold": 7,
        "consistency_warnings": []
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    """Main application entry point."""
    initialize_session_state()

    # Header
    st.title("✨ DescribeIt AI")
    st.markdown("*GenAI-Powered Product Description Generator for E-Commerce Retailers*")

    st.markdown("---")

    # Introduction
    st.markdown("""
    ### Welcome to DescribeIt AI

    Transform your product catalog into compelling, conversion-optimized descriptions
    using the power of generative AI. Simply upload your product data, choose your tone,
    and let AI craft descriptions that sell.
    """)

    # Feature cards
    st.markdown("### Key Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
        <h4>📦 Batch Processing</h4>
        <p>Generate descriptions for dozens of products at once.
        Upload CSV files, use synthetic data, or enter products manually.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
        <h4>⭐ Quality Scoring</h4>
        <p>AI-powered quality evaluation with automatic retries.
        Each description is scored 1-10 with actionable feedback.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
        <h4>📤 Easy Export</h4>
        <p>Download results in multiple formats.
        Export full data, long descriptions, or bullet points as CSV.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Navigation instructions
    st.markdown("### Getting Started")

    st.markdown("""
    1. **Generate** - Navigate to the "Generate" page using the sidebar to upload your product catalog
    2. **Configure** - Optionally analyze your brand voice and select your preferred tone
    3. **Review** - Review generated descriptions, filter by quality, and regenerate as needed
    4. **Export** - Download your polished descriptions in your preferred format

    Use the sidebar navigation to access each page. Your data persists across pages during this session.
    """)

    # Quick stats if data exists
    if st.session_state.results:
        st.markdown("---")
        st.markdown("### Current Session Stats")

        results = st.session_state.results
        total = len(results)
        avg_quality = sum(r["quality_score"] for r in results) / total if total > 0 else 0
        avg_time = sum(r["generation_time_ms"] for r in results) / total if total > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Products Generated", total)
        col2.metric("Average Quality Score", f"{avg_quality:.1f}/10")
        col3.metric("Avg Generation Time", f"{avg_time:.0f}ms")

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
