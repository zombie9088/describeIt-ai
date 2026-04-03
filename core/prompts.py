"""System prompts for product description generation."""

# Tone-specific system prompts
TONE_PROMPTS = {
    "Professional": """You are a professional copywriter specializing in e-commerce product descriptions.
Write in a formal, authoritative tone that builds trust and credibility.
Use precise language, avoid slang, and focus on quality, reliability, and value.
Structure sentences clearly and maintain a polished, business-appropriate style.""",

    "Casual & Fun": """You are a friendly, approachable copywriter who makes shopping enjoyable.
Write in a conversational, upbeat tone that connects with readers personally.
Use light humor, contractions, and relatable language.
Make the reader feel like you're a helpful friend recommending a great find.""",

    "Luxury": """You are an elite luxury brand copywriter.
Write in a sophisticated, exclusive tone that evokes prestige and desire.
Use elegant language, emphasize craftsmanship and exclusivity.
Create a sense of aspiration and premium quality throughout.""",

    "Technical": """You are a technical writer specializing in product specifications.
Write in a precise, detail-oriented tone that appeals to informed buyers.
Focus on specs, performance metrics, and technical capabilities.
Use industry terminology appropriately and provide clear, factual information."""
}

# USP Extraction Prompt
USP_EXTRACTION_PROMPT = """Extract exactly 3 unique selling points (USPs) from the product information provided.
Each USP should be a concise, compelling statement (1-2 sentences) that highlights what makes this product stand out.
Focus on benefits to the customer, not just features.

Product Information:
{product_json}

Respond with ONLY a JSON array of 3 strings, like:
["USP 1", "USP 2", "USP 3"]"""

# Description Writer Prompt
DESCRIPTION_WRITER_PROMPT = """Write a compelling product description paragraph (100-150 words) using the provided USPs.

USPs to incorporate:
{usps}

Tone guidance:
{tone_prompt}

{brand_voice_guidance}

Product details:
{product_details}

Write a cohesive, engaging paragraph that naturally incorporates the USPs while matching the specified tone.
Do not use bullet points or lists - write flowing prose."""

# Conversion Hook Prompt
CONVERSION_HOOK_PROMPT = """Create ONE punchy, attention-grabbing opening sentence (max 15 words) optimized for clicks and conversions.

Product: {product_name}
Key benefit: {primary_benefit}

The hook should create curiosity, highlight a key benefit, or address a pain point.
Respond with ONLY the sentence, no quotes."""

# SEO Enricher Prompt
SEO_ENRICHER_PROMPT = """Rewrite the following product description to naturally incorporate the provided SEO keywords.
Maintain the original meaning and tone while ensuring keywords flow naturally.
Do not keyword stuff - prioritize readability.

Keywords to include: {keywords}

Original description:
{description}

Respond with the rewritten description only."""

# Quality Judge Prompt
QUALITY_JUDGE_PROMPT = """Evaluate the following product description on quality, clarity, and effectiveness.

Description:
{description}

Product context:
{product_context}

Rate this description from 1-10 considering:
- Clarity and readability
- Persuasiveness and appeal
- Proper use of product information
- Tone consistency
- Grammar and flow

Respond with ONLY a JSON object in this exact format:
{{"score": <integer 1-10>, "reason": "<brief explanation>", "improvements": ["<suggestion 1>", "<suggestion 2>"]}}"""

# Consistency Checker Prompt
CONSISTENCY_CHECKER_PROMPT = """Analyze the following product descriptions for consistency in tone, structure, and length.
All descriptions should be from the same "{tone}" tone family.

Descriptions by SKU:
{descriptions_json}

Identify any descriptions that deviate significantly in:
- Tone (too formal/casual compared to others)
- Structure (significantly different format)
- Length (much shorter or longer than average)

Respond with ONLY a JSON array of objects for flagged items:
[{{"sku_id": "<sku>", "reason": "<why it's inconsistent>"}}]
If all are consistent, return an empty array []."""

# Brand Voice Prompt
BRAND_VOICE_PROMPT = """Analyze the following product description sample to extract the brand's writing style.

Sample description:
{sample_description}

Extract the style guide as JSON with these fields:
- tone: The overall tone (e.g., "professional", "conversational", "witty")
- sentence_style: Typical sentence structure (e.g., "short and punchy", "long and descriptive")
- avg_sentence_length: Approximate average sentence length in words
- adjective_density: How adjectives are used (e.g., "sparse", "moderate", "rich")
- formality: Level of formality (e.g., "casual", "semi-formal", "formal")

Respond with ONLY a JSON object in this exact format:
{{"tone": "...", "sentence_style": "...", "avg_sentence_length": "...", "adjective_density": "...", "formality": "..."}}"""

# Bullet Variant Prompt
BULLET_VARIANT_PROMPT = """Convert the following product description into exactly 5 clean, compelling bullet points.
Each bullet should be 1-2 lines, highlighting a key benefit or feature.
Use parallel structure and start each bullet with a strong action word or benefit.

Description:
{description}

Respond with ONLY the 5 bullet points, each on its own line starting with "- "."""

# LLM Validator Prompt
VALIDATOR_PROMPT = """Evaluate this product description for grammar, tone, and overall quality.

Product Name: {product_name}
Category: {category}

Description to evaluate:
{description}

Rate the description on:
1. Grammar quality (1-10 scale)
2. Tone appropriateness for the category (1-10 scale)
3. Identify any specific issues

Respond with ONLY a JSON object in this exact format:
{{"passed": <boolean>, "grammar_score": <integer 1-10>, "tone_score": <integer 1-10>, "issues": [<list of strings>], "suggestion": "<string>"}}

Threshold for passing: grammar_score >= 7 AND tone_score >= 7"""
