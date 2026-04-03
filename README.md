# DescribeIt AI

A GenAI-powered product description generator for e-commerce retailers.

## Features

- **Batch Processing**: Generate descriptions for multiple products at once
- **Quality Scoring**: AI-powered quality evaluation with retry mechanism
- **Multiple Tones**: Professional, Casual & Fun, Luxury, Technical
- **Brand Voice**: Analyze and replicate your brand's writing style
- **Export Options**: CSV export with full results, long descriptions, or bullet points

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your API credentials:
   ```bash
   cp .env.example .env
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage

1. **Home Page**: Overview of features and navigation
2. **Generate (Page 1)**: Upload product data or use synthetic data, configure brand voice, generate descriptions
3. **Review (Page 2)**: Review generated descriptions, filter by quality, regenerate individual products
4. **Export (Page 3)**: Download results in various CSV formats

## Project Structure

```
describeIt-ai/
├── app.py                  # Main Streamlit app
├── pages/
│   ├── 1_Generate.py       # Batch generation page
│   ├── 2_Review.py         # Review & edit results
│   └── 3_Export.py         # Export page
├── core/
│   ├── __init__.py
│   ├── llm_client.py       # LLM setup
│   ├── preprocessor.py     # Data validation
│   ├── pipeline.py         # Generation pipeline
│   ├── prompts.py          # System prompts
│   └── synthetic_data.py   # Synthetic data generator
├── .env                    # API credentials (not committed)
├── .env.example            # Example env file
├── requirements.txt
└── README.md
```

## API Configuration

The application uses OpenAI-compatible APIs. Configure in `.env`:

```
api_endpoint=https://your-endpoint-here
api_key=your-api-key-here
```

## License

MIT
