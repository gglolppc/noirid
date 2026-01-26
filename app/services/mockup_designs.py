from __future__ import annotations
from app.services.mockup_engine import DesignTemplate, TextSlot

DESIGNS: dict[str, DesignTemplate] = {
    # 1) 2_letters.jpg (две буквы в столбик)
    "black-on-black-initials": DesignTemplate(
        name="black-on-black-initials",
        style="deboss",
        ink_alpha=0.70,
        slots=[
            TextSlot(
                key="line1",
                anchor="center",
                dy=-0.02,
                font="IBM.TTF",
                font_px=350,
                tracking=0,
                align="center",
                stroke_width=6,
            ),
            TextSlot(
                key="line2",
                anchor="center",
                dy=+0.20,
                font="IBM.TTF",
                font_px=350,
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
        ink_alpha=0.65,
        slots=[
            TextSlot(
                key="initials",             # ожидаем "A · K" или "A.K"
                anchor="bottom_text",
                dy=-0.10,
                font="IBM.TTF",
                font_px=160,
                tracking=8,
                align="center",
                max_width=0.70,
                stroke_width=6,
            )
        ],
    ),

    # 3) coord.jpg (координаты вверху слева/центре — у тебя ближе к верху)
    "coords_top": DesignTemplate(
        name="coords_top",
        style="deboss",
        ink_alpha=0.60,
        slots=[
            TextSlot(
                key="coord_line1",
                anchor="top_text",
                dy=0.06,
                font="IBM.TTF",
                font_px=130,
                tracking=2,
                align="center",
                max_width=0.72,
                stroke_width=1,
            ),
            TextSlot(
                key="coord_line2",
                anchor="top_text",
                dy=0.13,
                font="IBM.TTF",
                font_px=130,
                tracking=2,
                align="center",
                max_width=0.72,
                stroke_width=1,
            ),
        ],
    ),

    # 4) date.jpg (дата в ряд вверху)
    "date_top": DesignTemplate(
        name="date_top",
        style="deboss",
        ink_alpha=0.65,
        slots=[
            TextSlot(
                key="date",
                anchor="top_text",
                dy=0.08,
                font="IBM.TTF",
                font_px=150,
                tracking=14,       # точки/разделители красиво выглядят с трекингом
                align="center",
                max_width=0.72,
                stroke_width=1,
            )
        ],
    ),

    # 5) number.jpg (номер снизу)
    "number_bottom": DesignTemplate(
        name="number_bottom",
        style="deboss",
        ink_alpha=0.70,
        slots=[
            TextSlot(
                key="number",
                anchor="bottom_text",
                dy=0.00,
                font="IBM.TTF",
                font_px=170,
                tracking=8,
                align="center",
                max_width=0.78,
                stroke_width=1,
            )
        ],
    ),

    # 6) oneword.jpg (одно слово сверху)
    "one_word_top": DesignTemplate(
        name="one_word_top",
        style="deboss",
        ink_alpha=0.70,
        slots=[
            TextSlot(
                key="word",
                anchor="top_text",
                dy=0.10,
                font="IBM.TTF",
                font_px=150,
                tracking=6,
                align="center",
                max_width=0.70,
                stroke_width=1,
            )
        ],
    ),
}
