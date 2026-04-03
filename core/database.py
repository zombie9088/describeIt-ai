"""SQLite database layer for product storage."""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "products.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database with the products table."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku_id TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT,
            features TEXT,
            description_long TEXT,
            description_bullets TEXT,
            conversion_hook TEXT,
            quality_score INTEGER,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_product(result_dict: Dict[str, Any]) -> None:
    """Insert or update a product by sku_id.

    Args:
        result_dict: Dict with product data including sku_id, product_name, etc.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Extract fields from result_dict
    sku_id = result_dict.get("sku_id")
    product_name = result_dict.get("product_name", "Unknown")
    category = result_dict.get("category", "General")
    features = result_dict.get("features", "")
    description_long = result_dict.get("description_long", "")
    description_bullets = result_dict.get("description_bullets", "")
    conversion_hook = result_dict.get("conversion_hook", "")
    quality_score = result_dict.get("quality_score")
    status = result_dict.get("status", "draft")

    # Convert lists/dicts to JSON strings for storage
    import json
    if isinstance(features, (list, dict)):
        features = json.dumps(features)
    if isinstance(description_bullets, (list, dict)):
        description_bullets = json.dumps(description_bullets)

    cursor.execute("""
        INSERT OR REPLACE INTO products
        (sku_id, product_name, category, features, description_long,
         description_bullets, conversion_hook, quality_score, status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (sku_id, product_name, category, features, description_long,
          description_bullets, conversion_hook, quality_score, status))

    conn.commit()
    conn.close()


def get_all_products() -> pd.DataFrame:
    """Get all products as a DataFrame.

    Returns:
        DataFrame with all products
    """
    conn = get_connection()

    df = pd.read_sql_query("SELECT * FROM products ORDER BY created_at DESC", conn)

    conn.close()
    return df


def search_products(query: str) -> pd.DataFrame:
    """Search products by product_name.

    Args:
        query: Search term to match in product_name

    Returns:
        DataFrame with matching products
    """
    conn = get_connection()

    search_pattern = f"%{query}%"
    df = pd.read_sql_query("""
        SELECT * FROM products
        WHERE product_name LIKE ?
        ORDER BY created_at DESC
    """, conn, params=(search_pattern,))

    conn.close()
    return df


def update_description(sku_id: str, new_description: str, new_status: str) -> None:
    """Update a product's description and status.

    Args:
        sku_id: The SKU ID of the product to update
        new_description: New description_long value
        new_status: New status value
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE products
        SET description_long = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE sku_id = ?
    """, (new_description, new_status, sku_id))

    conn.commit()
    conn.close()


def get_product(sku_id: str) -> Optional[Dict[str, Any]]:
    """Get a single product by SKU ID.

    Args:
        sku_id: The SKU ID to look up

    Returns:
        Dict with product data, or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE sku_id = ?", (sku_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)
    return None


def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """Get a single product by database ID.

    Args:
        product_id: The database ID to look up

    Returns:
        Dict with product data, or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)
    return None


def update_product_status(sku_id: str, new_status: str) -> None:
    """Update only the status of a product.

    Args:
        sku_id: The SKU ID of the product to update
        new_status: New status value
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE products
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE sku_id = ?
    """, (new_status, sku_id))

    conn.commit()
    conn.close()


def update_product_fields(sku_id: str, fields: Dict[str, Any]) -> None:
    """Update specific fields of a product.

    Args:
        sku_id: The SKU ID of the product to update
        fields: Dict of field names to new values
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Build dynamic UPDATE statement
    set_clauses = []
    values = []
    for field, value in fields.items():
        set_clauses.append(f"{field} = ?")
        values.append(value)

    values.append(sku_id)

    query = f"""
        UPDATE products
        SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
        WHERE sku_id = ?
    """

    cursor.execute(query, values)

    conn.commit()
    conn.close()
