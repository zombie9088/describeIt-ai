"""Full generation pipeline for product descriptions with async support and caching."""

import json
import time
import asyncio
import hashlib
from typing import Dict, List, Any, Optional, Callable
import pandas as pd

from .llm_client import get_ollama_client, LLMCallError
from .prompts import (
    TONE_PROMPTS,
    USP_EXTRACTION_PROMPT,
    DESCRIPTION_WRITER_PROMPT,
    CONVERSION_HOOK_PROMPT,
    SEO_ENRICHER_PROMPT,
    QUALITY_JUDGE_PROMPT,
    CONSISTENCY_CHECKER_PROMPT,
    BRAND_VOICE_PROMPT,
    BULLET_VARIANT_PROMPT,
)

# Get Ollama client instance
ollama = get_ollama_client()

# In-memory cache for LLM responses (prompt_hash -> response)
_llm_cache: Dict[str, str] = {}
_cache_enabled = True


def _compute_prompt_hash(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Compute a hash of the prompt for caching."""
    combined = f"{prompt}|||{system_prompt or ''}"
    return hashlib.md5(combined.encode()).hexdigest()


def _call_llm_cached(prompt: str, system_prompt: Optional[str] = None, use_cache: bool = True) -> str:
    """Call LLM with caching support."""
    if use_cache and _cache_enabled:
        prompt_hash = _compute_prompt_hash(prompt, system_prompt)
        if prompt_hash in _llm_cache:
            return _llm_cache[prompt_hash]

    result = ollama.generate(prompt, system_prompt)

    if use_cache and _cache_enabled:
        prompt_hash = _compute_prompt_hash(prompt, system_prompt)
        _llm_cache[prompt_hash] = result

    return result


def _parse_json_response(response: str, fallback: Any) -> Any:
    """Parse JSON from LLM response with fallback on failure."""
    try:
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


async def _call_llm_async(prompt: str, system_prompt: Optional[str] = None, use_cache: bool = True) -> str:
    """Async LLM call with caching."""
    if use_cache and _cache_enabled:
        prompt_hash = _compute_prompt_hash(prompt, system_prompt)
        if prompt_hash in _llm_cache:
            return _llm_cache[prompt_hash]

    result = await ollama.generate_async(prompt, system_prompt)

    if use_cache and _cache_enabled:
        prompt_hash = _compute_prompt_hash(prompt, system_prompt)
        _llm_cache[prompt_hash] = result

    return result


async def generate_description_async(
    product_row: pd.Series,
    tone: str,
    brand_voice_guide: Optional[Dict[str, Any]] = None,
    max_retries: int = 1,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Generate a complete product description asynchronously.

    Args:
        product_row: pandas Series with product data
        tone: Tone to use (Professional, Casual & Fun, Luxury, Technical)
        brand_voice_guide: Optional brand voice guide dict
        max_retries: Maximum retry attempts for low quality scores (reduced to 1)
        use_cache: Whether to use response caching

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

    product_info = {
        "product_name": product_row.get("product_name", "Unknown Product"),
        "category": product_row.get("category", "General"),
        "brand": product_row.get("brand", "Unknown Brand"),
        "price": product_row.get("price", 0),
        "features": product_row.get("features", []),
        "specs": product_row.get("specs", {}),
        "target_audience": product_row.get("target_audience", "General audience"),
    }

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
        usps_response = await _call_llm_async(usps_prompt, use_cache=use_cache)
        usps = _parse_json_response(usps_response, [
            f"High-quality {product_info['product_name']}",
            f"From trusted brand {product_info['brand']}",
            f"Great value at ${product_info['price']}"
        ])
        if not isinstance(usps, list):
            usps = [str(usps)]

        # Optimized: Combined Steps 2-5 into single quality loop with max 1 retry
        quality_score = 0
        improvements_context = ""

        while retry_count <= max_retries:
            brand_voice_guidance = ""
            if brand_voice_guide:
                brand_voice_guidance = f"""Brand voice guidance:
- Tone: {brand_voice_guide.get('tone', 'professional')}
- Sentence style: {brand_voice_guide.get('sentence_style', 'varied')}
- Formality: {brand_voice_guide.get('formality', 'semi-formal')}
- Adjective density: {brand_voice_guide.get('adjective_density', 'moderate')}"""

            product_details = f"""Name: {product_info['product_name']}
Category: {product_info['category']}
Brand: {product_info['brand']}
Price: ${product_info['price']}
Features: {', '.join(product_info['features'][:5]) if product_info['features'] else 'N/A'}
Target Audience: {product_info['target_audience']}"""

            # Combined prompt: Description + Hook + SEO in one call
            desc_prompt = DESCRIPTION_WRITER_PROMPT.format(
                usps="\n".join(f"- {usp}" for usp in usps),
                tone_prompt=tone_prompt,
                brand_voice_guidance=brand_voice_guidance,
                product_details=product_details
            )

            if improvements_context:
                desc_prompt += f"\n\nPrevious feedback for improvement: {improvements_context}"

            # Run description, hook, and judge in parallel
            desc_task = _call_llm_async(desc_prompt, use_cache=use_cache)

            primary_benefit = usps[0] if usps else f"Great {product_info['category']} product"
            hook_prompt = CONVERSION_HOOK_PROMPT.format(
                product_name=product_info["product_name"],
                primary_benefit=primary_benefit[:100]
            )
            hook_task = _call_llm_async(hook_prompt, use_cache=use_cache)

            current_description, conversion_hook = await asyncio.gather(desc_task, hook_task)

            # SEO enrichment (only if keywords provided)
            if seo_keywords:
                seo_prompt = SEO_ENRICHER_PROMPT.format(
                    keywords=", ".join(seo_keywords),
                    description=current_description
                )
                current_description = await _call_llm_async(seo_prompt, use_cache=use_cache)

            # Quality judge
            judge_prompt = QUALITY_JUDGE_PROMPT.format(
                description=current_description,
                product_context=json.dumps(product_info, indent=2)
            )
            judge_response = await _call_llm_async(judge_prompt, use_cache=use_cache)
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

            retry_count += 1
            improvements_context = f"Previous score: {quality_score}/10. Suggestions: {'; '.join(improvements)}"

        # Step 6: Bullet Variant
        bullet_prompt = BULLET_VARIANT_PROMPT.format(description=current_description)
        description_bullets = await _call_llm_async(bullet_prompt, use_cache=use_cache)

    except LLMCallError as e:
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


def generate_description(
    product_row: pd.Series,
    tone: str,
    brand_voice_guide: Optional[Dict[str, Any]] = None,
    max_retries: int = 1,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Generate a complete product description (sync wrapper).

    Uses asyncio to run internal calls concurrently for better performance.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            generate_description_async(
                product_row=product_row,
                tone=tone,
                brand_voice_guide=brand_voice_guide,
                max_retries=max_retries,
                use_cache=use_cache,
            )
        )
    finally:
        loop.close()


async def run_batch_async(
    df: pd.DataFrame,
    tone: str,
    brand_voice_guide: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    concurrency: int = 5,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Run description generation for all products asynchronously with concurrency.

    Args:
        df: DataFrame with product data
        tone: Tone to use for all generations
        brand_voice_guide: Optional brand voice guide
        progress_callback: Optional callback(i, total, current_product_name)
        concurrency: Number of products to process in parallel
        use_cache: Whether to use response caching

    Returns:
        List of result dicts for each product
    """
    results = []
    total = len(df)
    semaphore = asyncio.Semaphore(concurrency)

    async def process_with_semaphore(idx, row):
        async with semaphore:
            product_name = row.get("product_name", f"Product {idx}")
            if progress_callback:
                progress_callback(idx, total, product_name)

            result = await generate_description_async(
                product_row=row,
                tone=tone,
                brand_voice_guide=brand_voice_guide,
                max_retries=1,
                use_cache=use_cache,
            )
            return result

    tasks = [process_with_semaphore(idx, row) for idx, row in df.iterrows()]
    results = await asyncio.gather(*tasks)

    # Cleanup async client
    await ollama.close_async()

    return list(results)


def run_batch(
    df: pd.DataFrame,
    tone: str,
    brand_voice_guide: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    concurrency: int = 5,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Run description generation for all products with concurrency.

    Args:
        df: DataFrame with product data
        tone: Tone to use for all generations
        brand_voice_guide: Optional brand voice guide
        progress_callback: Optional callback(i, total, current_product_name)
        concurrency: Number of products to process in parallel (default: 5)
        use_cache: Whether to use response caching

    Returns:
        List of result dicts for each product
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            run_batch_async(
                df=df,
                tone=tone,
                brand_voice_guide=brand_voice_guide,
                progress_callback=progress_callback,
                concurrency=concurrency,
                use_cache=use_cache,
            )
        )
    finally:
        loop.close()


def check_batch_consistency(
    results: List[Dict[str, Any]],
    tone: str
) -> List[Dict[str, str]]:
    """Check generated descriptions for consistency."""
    if not results:
        return []

    descriptions_data = {}
    for result in results:
        descriptions_data[result["sku_id"]] = result["description_long"][:500]

    descriptions_json = json.dumps(descriptions_data, indent=2)

    consistency_prompt = CONSISTENCY_CHECKER_PROMPT.format(
        tone=tone,
        descriptions_json=descriptions_json
    )

    try:
        response = _call_llm_cached(consistency_prompt)
        flagged = _parse_json_response(response, [])
        if not isinstance(flagged, list):
            return []
        return flagged
    except Exception:
        return []


def analyze_brand_voice(sample_description: str) -> Dict[str, str]:
    """Analyze a sample description to extract brand voice."""
    brand_prompt = BRAND_VOICE_PROMPT.format(sample_description=sample_description)

    try:
        response = _call_llm_cached(brand_prompt)
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


def clear_cache():
    """Clear the LLM response cache."""
    global _llm_cache
    _llm_cache = {}


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return {
        "enabled": _cache_enabled,
        "size": len(_llm_cache),
    }


def set_cache_enabled(enabled: bool):
    """Enable or disable caching."""
    global _cache_enabled
    _cache_enabled = enabled
