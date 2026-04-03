"""Data validation and normalization for product catalogs."""

import json
from typing import Dict, List, Any, Tuple

import pandas as pd


REQUIRED_COLUMNS = [
    "sku_id",
    "product_name",
    "category",
    "brand",
    "price",
    "features",
    "specs",
    "target_audience",
    "keywords"
]


def _safe_json_parse(value: Any) -> Any:
    """Safely parse a JSON string, returning the original value if parsing fails."""
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def preprocess(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Preprocess and validate a product catalog DataFrame.

    Args:
        df: Raw product catalog DataFrame

    Returns:
        Tuple of (cleaned_df, validation_report) where:
        - cleaned_df: DataFrame with normalized values
        - validation_report: Dict with keys 'total', 'valid', 'flagged'
    """
    validation_report = {
        "total": len(df),
        "valid": 0,
        "flagged": []
    }

    # Check for required columns
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        validation_report["flagged"].append({
            "type": "missing_columns",
            "columns": missing_columns,
            "message": f"Missing required columns: {', '.join(missing_columns)}"
        })
        # Add missing columns with None values
        for col in missing_columns:
            df[col] = None

    # Create a copy to avoid modifying the original
    cleaned_df = df.copy()

    # Normalize product_name (strip whitespace, title case)
    if "product_name" in cleaned_df.columns:
        cleaned_df["product_name"] = cleaned_df["product_name"].apply(
            lambda x: x.strip().title() if isinstance(x, str) else x
        )

    # Parse JSON fields
    for col in ["features", "specs", "keywords"]:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].apply(_safe_json_parse)

    # Validate each row
    flagged_indices = []
    for idx, row in cleaned_df.iterrows():
        issues = []

        # Check for null product_name
        if pd.isna(row.get("product_name")) or row.get("product_name") == "":
            issues.append("product_name is null or empty")

        # Check for empty features
        features = row.get("features")
        if features is None or (isinstance(features, list) and len(features) == 0):
            issues.append("features is empty")

        if issues:
            flagged_indices.append(idx)
            validation_report["flagged"].append({
                "sku_id": row.get("sku_id", f"Row {idx}"),
                "issues": issues
            })

    # Calculate valid count
    validation_report["valid"] = len(df) - len(flagged_indices)

    # Add a 'flagged' column to the dataframe
    cleaned_df["_flagged"] = cleaned_df.index.isin(flagged_indices)

    return cleaned_df, validation_report


def validate_row(row: pd.Series) -> List[str]:
    """Validate a single product row and return list of issues.

    Args:
        row: pandas Series representing a product row

    Returns:
        List of validation issue strings
    """
    issues = []

    if pd.isna(row.get("product_name")) or row.get("product_name") == "":
        issues.append("product_name is null or empty")

    features = row.get("features")
    if features is None or (isinstance(features, list) and len(features) == 0):
        issues.append("features is empty")

    if pd.isna(row.get("category")):
        issues.append("category is null")

    if pd.isna(row.get("brand")):
        issues.append("brand is null")

    price = row.get("price")
    if pd.isna(price) or (isinstance(price, (int, float)) and price <= 0):
        issues.append("price is invalid")

    return issues
