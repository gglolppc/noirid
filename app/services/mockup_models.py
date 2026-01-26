from __future__ import annotations
from app.services.mockup_engine import ModelLayout, Anchor

MODEL_LAYOUTS: dict[str, ModelLayout] = {
    # ключ как тебе удобно: "apple/iphone_14_pro"
    "apple/iphone_14_pro": ModelLayout(
        anchors={
            "center": Anchor(x=0.50, y=0.55),
            "top_text": Anchor(x=0.50, y=0.24),
            "bottom_text": Anchor(x=0.50, y=0.86),
        }
    ),
    "samsung/s23_ultra": ModelLayout(
        anchors={
            "center": Anchor(x=0.50, y=0.55),
            "top_text": Anchor(x=0.50, y=0.24),
            "bottom_text": Anchor(x=0.50, y=0.86),
        }
    ),
}
