from __future__ import annotations
from app.services.mockup_engine import DesignTemplate, TextSlot

DESIGNS: dict[str, DesignTemplate] = {
    # 1) 2_letters.jpg (две буквы в столбик)
    "black-on-black-initials": DesignTemplate(
        name="black-on-black-initials",
        style="deboss",
        ink_alpha=0.60,
        slots=[
            TextSlot(
                key="line1",
                anchor="center",
                dy=+0.02,
                font="IBM.ttf",
                font_px=280,
                tracking=0,
                align="center",
                stroke_width=6,
            ),
            TextSlot(
                key="line2",
                anchor="center",
                dy=+0.20,
                font="IBM.ttf",
                font_px=280,
                tracking=0,
                align="center",
                stroke_width=6,
            ),
        ],
    ),

    # 2) AK.jpg (A·K по центру снизу)
    "black-on-black-initials-dot": DesignTemplate(
        name="black-on-black-initials-dot",
        style="deboss",
        ink_alpha=0.60,
        slots=[
            TextSlot(
                key="initials",             # ожидаем "A · K" или "A.K"
                anchor="bottom_text",
                dy=-0.08,
                font="IBM.ttf",
                font_px=195,
                tracking=25,
                align="center",
                max_width=0.70,
                stroke_width=6,
            )
        ],
    ),

    # 3) coord.jpg (координаты вверху слева/центре — у тебя ближе к верху)
    "coords": DesignTemplate(
        name="coords",
        style="deboss",
        ink_alpha=0.70,
        slots=[
            TextSlot(
                key="coord_line1",
                anchor="bottom_text",
                dy=-0.06,
                dx=-0.17,
                font="IBM.ttf",
                font_px=50,
                tracking=8,
                align="left",
                max_width=0.3,
                stroke_width=2,
            ),
            TextSlot(
                key="coord_line2",
                anchor="bottom_text",
                dy=0.0,
                dx=-0.17,
                font="IBM.ttf",
                font_px=50,
                tracking=8,
                align="left",
                max_width=0.3,
                stroke_width=2,
            ),
        ],
    ),

    # 4) date.jpg (дата в ряд вверху)
    "date": DesignTemplate(
        name="date",
        style="deboss",
        ink_alpha=0.65,
        slots=[
            TextSlot(
                key="date",
                anchor="bottom_text",
                dy=0.01,
                font="IBM.ttf",
                font_px=150,
                tracking=10,       # точки/разделители красиво выглядят с трекингом
                align="center",
                max_width=0.36,
                stroke_width=2,
            )
        ],
    ),

    # 5) number.jpg (номер снизу)
    "car-plate": DesignTemplate(
        name="car-plate",
        style="deboss",
        ink_alpha=0.63,
        slots=[
            TextSlot(
                key="number",
                anchor="bottom_text",
                dy=-0.02,
                font="IBM.ttf",
                font_px=90,
                tracking=12,
                align="center",
                max_width=0.35,
                stroke_width=3,
            )
        ],
    ),

    # 6) oneword.jpg (одно слово сверху)
    "one-word": DesignTemplate(
        name="one-word",
        style="deboss",
        ink_alpha=0.50,
        slots=[
            TextSlot(
                key="word",
                anchor="bottom_text",
                dy=-0.02,
                font="IBM.ttf",
                font_px=60,
                tracking=13,
                align="center",
                max_width=0.35,
                stroke_width=3,
            )
        ],
    ),
    "letter": DesignTemplate(
        name="letter",
        style="deboss",
        ink_alpha=0.59,
        slots=[
            TextSlot(
                key="word",
                anchor="bottom_text",
                dy=-0.14,
                font="IBM.ttf",
                font_px=360,
                tracking=13,
                align="center",
                max_width=0.35,
                stroke_width=8,
            )
        ],
    ),
}
