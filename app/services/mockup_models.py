from __future__ import annotations
from app.services.mockup_engine import ModelLayout, Anchor

COMMON_LAYOUT = ModelLayout(
    anchors={
        "center": Anchor(x=0.50, y=0.55),
        "top_text": Anchor(x=0.50, y=0.24),
        "bottom_text": Anchor(x=0.50, y=0.86),
    }
)

MODEL_LAYOUTS: dict[str, ModelLayout] = {

    # iPhone 17
    "apple/iphone_17_air": COMMON_LAYOUT,
    "apple/iphone_17_pro_max": COMMON_LAYOUT,
    "apple/iphone_17_pro": COMMON_LAYOUT,
    "apple/iphone_17": COMMON_LAYOUT,

    # iPhone 16
    "apple/iphone_16_pro_max": COMMON_LAYOUT,
    "apple/iphone_16_pro": COMMON_LAYOUT,
    "apple/iphone_16": COMMON_LAYOUT,
    "apple/iphone_16_plus": COMMON_LAYOUT,

    # iPhone 15
    "apple/iphone_15_pro_max": COMMON_LAYOUT,
    "apple/iphone_15_pro": COMMON_LAYOUT,
    "apple/iphone_15": COMMON_LAYOUT,

    # iPhone 14
    "apple/iphone_14_pro_max": COMMON_LAYOUT,
    "apple/iphone_14_pro": COMMON_LAYOUT,
    "apple/iphone_14": COMMON_LAYOUT,

    # iPhone 13
    "apple/iphone_13_pro_max": COMMON_LAYOUT,
    "apple/iphone_13_pro": COMMON_LAYOUT,
    "apple/iphone_13": COMMON_LAYOUT,

    # Samsung S26
    "samsung/s26": COMMON_LAYOUT,
    "samsung/s26_plus": COMMON_LAYOUT,
    "samsung/s26_edge": COMMON_LAYOUT,
    "samsung/s26_ultra": COMMON_LAYOUT,

    # Samsung S25
    "samsung/s25": COMMON_LAYOUT,
    "samsung/s25_plus": COMMON_LAYOUT,
    "samsung/s25_ultra": COMMON_LAYOUT,

    # Samsung S24
    "samsung/s24": COMMON_LAYOUT,
    "samsung/s24_plus": COMMON_LAYOUT,
    "samsung/s24_ultra": COMMON_LAYOUT,

    # Samsung S23
    "samsung/s23": COMMON_LAYOUT,
    "samsung/s23_plus": COMMON_LAYOUT,
    "samsung/s23_ultra": COMMON_LAYOUT,

    # Samsung S22
    "samsung/s22": COMMON_LAYOUT,
    "samsung/s22_plus": COMMON_LAYOUT,
    "samsung/s22_ultra": COMMON_LAYOUT,
}
