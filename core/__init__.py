# DescribeIt AI Core Module

from .database import init_db, save_product, get_all_products, search_products, update_description, get_product
from .prompts import VALIDATOR_PROMPT

__all__ = [
    "init_db",
    "save_product",
    "get_all_products",
    "search_products",
    "update_description",
    "get_product",
    "VALIDATOR_PROMPT"
]
