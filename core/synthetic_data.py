"""Synthetic product catalog generator for testing and demonstration."""

import json
import random
from typing import Dict, List, Any

import pandas as pd


# Category-specific data pools
CATEGORIES = ["Electronics", "Apparel", "Home & Kitchen", "Sports & Fitness"]

BRANDS_BY_CATEGORY = {
    "Electronics": ["TechVibe", "CircuitPro", "DigitalEdge", "NanoWave", "PixelCore", "QuantumSound", "SmartFlow"],
    "Apparel": ["UrbanThread", "StyleCraft", "FashionForward", "PrimeWear", "EliteFit", "ComfortZone", "TrendSetters"],
    "Home & Kitchen": ["HomeEssence", "KitchenCraft", "CozyLiving", "ModernHome", "ArtisanWare", "PureLiving", "ChefMaster"],
    "Sports & Fitness": ["ProAthlete", "FitGear", "ActiveEdge", "PowerPlay", "EndurancePro", "FlexMotion", "PeakPerformance"]
}

PRODUCT_NAMES_BY_CATEGORY = {
    "Electronics": [
        "Wireless Noise-Cancelling Headphones", "4K Smart Display Monitor", "Portable Bluetooth Speaker",
        "Smart Home Hub Controller", "USB-C Fast Charging Power Bank", "Mechanical Gaming Keyboard",
        "Ergonomic Wireless Mouse", "HD Webcam with Microphone", "Smart LED Light Strips",
        "Portable SSD External Drive", "Wireless Charging Pad", "Smart Doorbell Camera",
        "Fitness Tracking Smartwatch", "True Wireless Earbuds", "Mini Projector"
    ],
    "Apparel": [
        "Premium Cotton T-Shirt", "Slim Fit Chino Pants", "Waterproof Running Jacket",
        "Merino Wool Sweater", "Athletic Performance Shorts", "Classic Denim Jeans",
        "Breathable Sports Bra", "Leather Casual Sneakers", "Insulated Winter Coat",
        "Moisture-Wicking Polo Shirt", "Yoga Leggings", "Canvas Backpack",
        "Silk Blend Scarf", "Compression Socks Set", "Sun Protection Hat"
    ],
    "Home & Kitchen": [
        "Stainless Steel Cookware Set", "Programmable Coffee Maker", "Non-Stick Frying Pan",
        "Digital Air Fryer", "Bamboo Cutting Board Set", "Ceramic Knife Set",
        "Glass Food Storage Containers", "Electric Kettle", "Stand Mixer",
        "Vacuum Sealer System", "Herb Garden Kit", "Cast Iron Dutch Oven",
        "Silicone Baking Mat Set", "Wine Aerator Pourer", "Spice Rack Organizer"
    ],
    "Sports & Fitness": [
        "Adjustable Dumbbell Set", "Yoga Mat with Alignment Lines", "Resistance Bands Kit",
        "Foam Roller for Recovery", "Jump Rope with Counter", "Kettlebell Set",
        "Pull-Up Bar Doorway", "Exercise Ball with Pump", "Ankle Weights Pair",
        "Ab Roller Wheel", "Boxing Speed Bag", "Climbing Rope",
        "Battle Rope", "Agility Ladder", "Heart Rate Monitor Chest Strap"
    ]
}

FEATURES_BY_CATEGORY = {
    "Electronics": [
        "Bluetooth 5.0 connectivity", "40-hour battery life", "IPX4 water resistance",
        "Active noise cancellation", "Touch control interface", "Voice assistant compatible",
        "Fast charging support", "Multi-device pairing", "Premium sound drivers",
        "Compact foldable design", "LED indicator lights", "USB-C charging port",
        "Built-in microphone", "Low latency mode", "Auto sleep/wake function"
    ],
    "Apparel": [
        "100% organic cotton", "Moisture-wicking fabric", "UV protection UPF 50+",
        "Four-way stretch material", "Reinforced stitching", "Antimicrobial treatment",
        "Ergonomic seam placement", "Quick-dry technology", "Temperature regulating",
        "Eco-friendly dyes", "Wrinkle-resistant finish", "Breathable mesh panels",
        "Reflective details", "Adjustable fit system", "Machine washable"
    ],
    "Home & Kitchen": [
        "Dishwasher safe", "BPA-free materials", "Heat-resistant up to 450°F",
        "Non-toxic ceramic coating", "Ergonomic soft-grip handles", "Space-saving stackable design",
        "Precision temperature control", "Energy efficient operation", "Scratch-resistant surface",
        "Rust-proof construction", "Easy-clean design", "Professional grade quality",
        "Modular components", "Quiet operation", "Auto shut-off feature"
    ],
    "Sports & Fitness": [
        "High-density foam construction", "Non-slip textured surface", "Weight capacity 500lbs",
        "Eco-friendly TPE material", "Reinforced core design", "Portable carrying strap included",
        "Anti-tear technology", "Sweat-resistant coating", "Ergonomic grip design",
        "Quick-release mechanism", "Progressive resistance levels", "Joint-friendly design",
        "Durable steel construction", "Easy assembly", "Compact storage"
    ]
}

SPECS_TEMPLATES = {
    "Electronics": ["battery_life", "connectivity", "weight", "dimensions", "warranty", "color_options"],
    "Apparel": ["material", "care_instructions", "fit", "sizes_available", "country_of_origin", "season"],
    "Home & Kitchen": ["capacity", "power", "material", "dimensions", "warranty", "certifications"],
    "Sports & Fitness": ["weight", "material", "dimensions", "resistance_levels", "warranty", "skill_level"]
}

TARGET_AUDIENCES = [
    "Young professionals", "Tech enthusiasts", "Fitness enthusiasts", "Home cooks",
    "Outdoor adventurers", "Students", "Parents", "Athletes", "Remote workers",
    "Minimalists", "Luxury seekers", "Budget-conscious shoppers", "Eco-conscious consumers",
    "Gamers", "Content creators"
]

KEYWORDS_BY_CATEGORY = {
    "Electronics": ["wireless", "bluetooth", "portable", "smart home", "tech gadget", "USB-C", "noise cancelling", "fast charging", "4K", "HD"],
    "Apparel": ["sustainable fashion", "comfortable", "stylish", "versatile", "premium quality", "breathable", "trendy", "classic", "athletic", "casual wear"],
    "Home & Kitchen": ["modern kitchen", "space saving", "durable", "easy clean", "energy efficient", "chef quality", "home essential", "organization", "non-toxic", "elegant"],
    "Sports & Fitness": ["workout gear", "home gym", "fitness equipment", "muscle building", "cardio", "recovery", "strength training", "flexibility", "endurance", "athletic performance"]
}


def _generate_specs_for_category(category: str) -> Dict[str, Any]:
    """Generate realistic specs for a given category."""
    specs_template = SPECS_TEMPLATES[category]
    specs = {}

    if category == "Electronics":
        specs["battery_life"] = f"{random.choice([20, 24, 30, 40, 48, 60])} hours"
        specs["connectivity"] = random.choice(["Bluetooth 5.0", "Bluetooth 5.2", "WiFi + Bluetooth", "USB-C"])
        specs["weight"] = f"{random.choice([150, 200, 250, 300, 350, 400])}g"
        specs["dimensions"] = f"{random.randint(5, 15)} x {random.randint(3, 10)} x {random.randint(2, 5)} cm"
        specs["warranty"] = f"{random.choice([1, 2])} year{'s' if random.choice([1, 2]) == 2 else ''}"
        specs["color_options"] = random.randint(2, 5)

    elif category == "Apparel":
        specs["material"] = random.choice(["100% Cotton", "Cotton Blend", "Polyester", "Merino Wool", "Nylon"])
        specs["care_instructions"] = random.choice(["Machine wash cold", "Hand wash only", "Dry clean only"])
        specs["fit"] = random.choice(["Regular", "Slim", "Relaxed", "Athletic"])
        specs["sizes_available"] = random.choice(["XS-XL", "S-XXL", "One Size", "XS-3XL"])
        specs["country_of_origin"] = random.choice(["Vietnam", "Bangladesh", "China", "India", "USA"])
        specs["season"] = random.choice(["All Season", "Spring/Summer", "Fall/Winter"])

    elif category == "Home & Kitchen":
        specs["capacity"] = random.choice(["2L", "3L", "4L", "5L", "6-quart", "8-quart"])
        specs["power"] = f"{random.choice([800, 1000, 1200, 1500])}W"
        specs["material"] = random.choice(["Stainless Steel", "Ceramic", "Cast Iron", "Bamboo", "Glass"])
        specs["dimensions"] = f"{random.randint(20, 40)} x {random.randint(15, 30)} x {random.randint(10, 25)} cm"
        specs["warranty"] = f"{random.choice([1, 2, 3])} year{'s' if random.choice([1, 2, 3]) > 1 else ''}"
        specs["certifications"] = random.choice(["FDA Approved", "BPA-Free", "Energy Star", "ETL Listed"])

    elif category == "Sports & Fitness":
        specs["weight"] = f"{random.choice([1, 2, 5, 10, 15, 20, 25])} lbs"
        specs["material"] = random.choice(["Steel", "TPE", "Neoprene", "Cast Iron", "High-density foam"])
        specs["dimensions"] = f"{random.randint(30, 120)} x {random.randint(10, 60)} x {random.randint(5, 30)} cm"
        specs["resistance_levels"] = random.choice(["5 levels", "10 levels", "Adjustable", "Fixed"])
        specs["warranty"] = f"{random.choice([1, 2, 5])} year{'s' if random.choice([1, 2, 5]) > 1 else ''}"
        specs["skill_level"] = random.choice(["Beginner", "Intermediate", "Advanced", "All Levels"])

    return specs


def generate_synthetic_catalog(n: int = 50) -> pd.DataFrame:
    """Generate a synthetic product catalog.

    Args:
        n: Number of products to generate (default 50)

    Returns:
        pandas DataFrame with columns: sku_id, product_name, category, brand,
        price, features, specs, target_audience, keywords
    """
    # Distribute products across categories (roughly equal)
    products_per_category = n // len(CATEGORIES)
    remainder = n % len(CATEGORIES)

    data = []
    sku_counter = 1

    for idx, category in enumerate(CATEGORIES):
        # Add one extra to first 'remainder' categories
        category_count = products_per_category + (1 if idx < remainder else 0)

        available_names = PRODUCT_NAMES_BY_CATEGORY[category].copy()
        available_brands = BRANDS_BY_CATEGORY[category]
        available_features = FEATURES_BY_CATEGORY[category]
        available_keywords = KEYWORDS_BY_CATEGORY[category]

        random.shuffle(available_names)

        for i in range(category_count):
            # Get product name (cycle if we need more than available)
            product_name = available_names[i % len(available_names)]
            if i >= len(available_names):
                product_name += f" v{i // len(available_names) + 1}"

            # Select 4-6 random features
            num_features = random.randint(4, 6)
            features = random.sample(available_features, min(num_features, len(available_features)))

            # Generate specs
            specs = _generate_specs_for_category(category)

            # Generate price based on category
            if category == "Electronics":
                price = round(random.uniform(29.99, 299.99), 2)
            elif category == "Apparel":
                price = round(random.uniform(19.99, 149.99), 2)
            elif category == "Home & Kitchen":
                price = round(random.uniform(24.99, 199.99), 2)
            else:  # Sports & Fitness
                price = round(random.uniform(14.99, 249.99), 2)

            # Select target audience and keywords
            target_audience = random.choice(TARGET_AUDIENCES)
            num_keywords = random.randint(3, 5)
            keywords = random.sample(available_keywords, num_keywords)

            data.append({
                "sku_id": f"SKU-{sku_counter:03d}",
                "product_name": product_name,
                "category": category,
                "brand": random.choice(available_brands),
                "price": price,
                "features": json.dumps(features),
                "specs": json.dumps(specs),
                "target_audience": target_audience,
                "keywords": json.dumps(keywords)
            })
            sku_counter += 1

    df = pd.DataFrame(data)

    # Save to CSV in project root
    df.to_csv("products.csv", index=False)

    return df


def load_catalog(filepath: str) -> pd.DataFrame:
    """Load a product catalog from CSV and parse JSON fields.

    Args:
        filepath: Path to the CSV file

    Returns:
        pandas DataFrame with features, specs, and keywords parsed as Python objects
    """
    df = pd.read_csv(filepath)

    # Parse JSON string fields
    for col in ["features", "specs", "keywords"]:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x else x
            )

    return df


if __name__ == "__main__":
    print("Generating synthetic product catalog with 50 products...")
    df = generate_synthetic_catalog(50)
    print(f"Generated {len(df)} products across {df['category'].nunique()} categories")
    print(f"Saved to products.csv")
    print("\nCategory distribution:")
    print(df["category"].value_counts())
