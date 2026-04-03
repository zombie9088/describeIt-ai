"""Full generation pipeline for product descriptions."""

import json
import time
from typing import Dict, List, Any, Optional, Callable

import pandas as pd

from .llm_client import llm
from .prompts import (
    TONE_PROMPTS,
    USP_EXTRACTION_PROMPT,
    DESCRIPTION_WRITER_PROMPT,
    CONVERSION_HOOK_PROMPT,
    SEO_ENRICHER_PROMPT,
    QUALITY_JUDGE_PROMPT,
    CONSISTENCY_CHECKER_PROMPT,
    BRAND_VOICE_PROMPT,
    BULLET_VARIANT_PROMPT
)


def _call_llm(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Call the LLM with a prompt and optional system prompt.

    Args:
        prompt: The user prompt
        system_prompt: Optional system prompt to prepend

    Returns:
        LLM response text
    """
    try:
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt

        response = llm.invoke(full_prompt)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        raise LLMCallError(f"LLM call failed: {e}")


def _parse_json_response(response: str, fallback: Any) -> Any:
    """Parse JSON from LLM response with fallback on failure."""
    try:
        # Try to extract JSON from the response
        # Handle cases where LLM wraps JSON in markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        return json.loads(response)
    except (json.JSONDecodeError, IndexError):
        return fallback


class LLMCallError(Exception):
    """Exception raised when LLM call fails."""
    pass


def generate_description(
    product_row: pd.Series,
    tone: str,
    brand_voice_guide: Optional[Dict[str, Any]] = None,
    max_retries: int = 2
) -> Dict[str, Any]:
    """Generate a complete product description for a single product.

    Args:
        product_row: pandas Series with product data
        tone: Tone to use (Professional, Casual & Fun, Luxury, Technical)
        brand_voice_guide: Optional brand voice guide dict
        max_retries: Maximum retry attempts for low quality scores

    Returns:
        Dict with generated description and metadata
    """
    start_time = time.time()
    retry_count = 0
    current_description = ""
    usps = []
    conversion_hook = ""
    seo_keywords = product_row.get("keywords", [])
    if isinstance(seo_keywords, str):
        try:
            seo_keywords = json.loads(seo_keywords)
        except json.JSONDecodeError:
            seo_keywords = []

    # Prepare product info as JSON
    product_info = {
        "product_name": product_row.get("product_name", "Unknown Product"),
        "category": product_row.get("category", "General"),
        "brand": product_row.get("brand", "Unknown Brand"),
        "price": product_row.get("price", 0),
        "features": product_row.get("features", []),
        "specs": product_row.get("specs", {}),
        "target_audience": product_row.get("target_audience", "General audience")
    }

    # Ensure features and specs are lists/dicts
    if isinstance(product_info["features"], str):
        try:
            product_info["features"] = json.loads(product_info["features"])
        except json.JSONDecodeError:
            product_info["features"] = []

    if isinstance(product_info["specs"], str):
        try:
            product_info["specs"] = json.loads(product_info["specs"])
        except json.JSONDecodeError:
            product_info["specs"] = {}

    tone_prompt = TONE_PROMPTS.get(tone, TONE_PROMPTS["Professional"])

    try:
        # Step 1: USP Extraction
        usps_prompt = USP_EXTRACTION_PROMPT.format(
            product_json=json.dumps(product_info, indent=2)
        )
        usps_response = _call_llm(usps_prompt)
        usps = _parse_json_response(usps_response, [
            f"High-quality {product_info['product_name']}",
            f"From trusted brand {product_info['brand']}",
            f"Great value at ${product_info['price']}"
        ])
        if not isinstance(usps, list):
            usps = [str(usps)]

        # Step 2-5: Description writing with quality loop
        quality_score = 0
        improvements_context = ""

        while retry_count <= max_retries:
            # Build brand voice guidance
            brand_voice_guidance = ""
            if brand_voice_guide:
                brand_voice_guidance = f"""Brand voice guidance:
- Tone: {brand_voice_guide.get('tone', 'professional')}
- Sentence style: {brand_voice_guide.get('sentence_style', 'varied')}
- Formality: {brand_voice_guide.get('formality', 'semi-formal')}
- Adjective density: {brand_voice_guide.get('adjective_density', 'moderate')}"""

            # Step 2: Description Writing
            product_details = f"""Name: {product_info['product_name']}
Category: {product_info['category']}
Brand: {product_info['brand']}
Price: ${product_info['price']}
Features: {', '.join(product_info['features'][:5]) if product_info['features'] else 'N/A'}
Target Audience: {product_info['target_audience']}"""

            desc_prompt = DESCRIPTION_WRITER_PROMPT.format(
                usps="\n".join(f"- {usp}" for usp in usps),
                tone_prompt=tone_prompt,
                brand_voice_guidance=brand_voice_guidance,
                product_details=product_details
            )

            if improvements_context:
                desc_prompt += f"\n\nPrevious feedback for improvement: {improvements_context}"

            current_description = _call_llm(desc_prompt)

            # Step 3: Conversion Hook
            primary_benefit = usps[0] if usps else f"Great {product_info['category']} product"
            hook_prompt = CONVERSION_HOOK_PROMPT.format(
                product_name=product_info["product_name"],
                primary_benefit=primary_benefit[:100]
            )
            conversion_hook = _call_llm(hook_prompt).strip().strip('"')

            # Step 4: SEO Enrichment
            if seo_keywords:
                seo_prompt = SEO_ENRICHER_PROMPT.format(
                    keywords=", ".join(seo_keywords),
                    description=current_description
                )
                current_description = _call_llm(seo_prompt)

            # Step 5: Quality Judge
            judge_prompt = QUALITY_JUDGE_PROMPT.format(
                description=current_description,
                product_context=json.dumps(product_info, indent=2)
            )
            judge_response = _call_llm(judge_prompt)
            judge_result = _parse_json_response(judge_response, {
                "score": 5,
                "reason": "Unable to evaluate",
                "improvements": []
            })

            quality_score = judge_result.get("score", 5)
            quality_reason = judge_result.get("reason", "No reason provided")
            improvements = judge_result.get("improvements", [])

            if quality_score >= 7 or retry_count >= max_retries:
                break

            # Prepare for retry
            retry_count += 1
            improvements_context = f"Previous score: {quality_score}/10. Suggestions: {'; '.join(improvements)}"

        # Step 6: Bullet Variant
        bullet_prompt = BULLET_VARIANT_PROMPT.format(description=current_description)
        bullets_response = _call_llm(bullet_prompt)
        description_bullets = bullets_response.strip()

    except LLMCallError as e:
        # Graceful fallback
        current_description = "Generation failed — please retry"
        description_bullets = "- Generation failed\n- Please retry\n- Check API connection"
        conversion_hook = "Retry generating this description"
        quality_score = 0
        quality_reason = str(e)

    end_time = time.time()
    generation_time_ms = int((end_time - start_time) * 1000)

    return {
        "sku_id": str(product_row.get("sku_id", "UNKNOWN")),
        "product_name": str(product_row.get("product_name", "Unknown")),
        "category": str(product_row.get("category", "General")),
        "usps": usps,
        "conversion_hook": conversion_hook,
        "description_long": current_description,
        "description_bullets": description_bullets,
        "quality_score": quality_score,
        "quality_reason": quality_reason,
        "generation_time_ms": generation_time_ms,
        "retry_count": retry_count,
        "seo_keywords_used": seo_keywords if isinstance(seo_keywords, list) else []
    }


def run_batch(
    df: pd.DataFrame,
    tone: str,
    brand_voice_guide: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[Dict[str, Any]]:
    """Run description generation for all products in a DataFrame.

    Args:
        df: DataFrame with product data
        tone: Tone to use for all generations
        brand_voice_guide: Optional brand voice guide
        progress_callback: Optional callback(i, total, current_product_name)

    Returns:
        List of result dicts for each product
    """
    results = []
    total = len(df)

    for idx, row in df.iterrows():
        product_name = row.get("product_name", f"Product {idx}")

        if progress_callback:
            progress_callback(idx, total, product_name)

        result = generate_description(
            product_row=row,
            tone=tone,
            brand_voice_guide=brand_voice_guide,
            max_retries=2
        )
        results.append(result)

    return results


def check_batch_consistency(
    results: List[Dict[str, Any]],
    tone: str
) -> List[Dict[str, str]]:
    """Check generated descriptions for consistency.

    Args:
        results: List of result dicts from run_batch
        tone: The tone that was used for generation

    Returns:
        List of flagged items with sku_id and reason
    """
    if not results:
        return []

    # Build descriptions JSON for the prompt
    descriptions_data = {}
    for result in results:
        descriptions_data[result["sku_id"]] = result["description_long"][:500]  # Truncate for context

    descriptions_json = json.dumps(descriptions_data, indent=2)

    consistency_prompt = CONSISTENCY_CHECKER_PROMPT.format(
        tone=tone,
        descriptions_json=descriptions_json
    )

    try:
        response = _call_llm(consistency_prompt)
        flagged = _parse_json_response(response, [])

        if not isinstance(flagged, list):
            return []

        return flagged
    except Exception:
        return []


def analyze_brand_voice(sample_description: str) -> Dict[str, str]:
    """Analyze a sample description to extract brand voice.

    Args:
        sample_description: Sample product description text

    Returns:
        Dict with brand voice attributes
    """
    brand_prompt = BRAND_VOICE_PROMPT.format(sample_description=sample_description)

    try:
        response = _call_llm(brand_prompt)
        result = _parse_json_response(response, {
            "tone": "professional",
            "sentence_style": "varied",
            "avg_sentence_length": "medium",
            "adjective_density": "moderate",
            "formality": "semi-formal"
        })
        return result
    except Exception:
        return {
            "tone": "professional",
            "sentence_style": "varied",
            "avg_sentence_length": "medium",
            "adjective_density": "moderate",
            "formality": "semi-formal"
        }
