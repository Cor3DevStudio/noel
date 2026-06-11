"""Reusable UI theme and styling constants."""

import customtkinter as ctk

from config.settings import THEME

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class Theme:
    PRIMARY = THEME["primary"]
    SECONDARY = THEME["secondary"]
    ACCENT = THEME["accent"]
    ACCENT_HOVER = THEME["accent_hover"]
    ACCENT_LIGHT = "#EFF6FF"
    TEXT_PRIMARY = THEME["text_primary"]
    TEXT_SECONDARY = THEME["text_secondary"]
    TEXT_MUTED = THEME["text_muted"]
    BORDER = THEME["border"]
    SUCCESS = THEME["success"]
    SUCCESS_LIGHT = "#ECFDF5"
    WARNING = THEME["warning"]
    WARNING_LIGHT = "#FFFBEB"
    DANGER = THEME["danger"]
    DANGER_LIGHT = "#FEF2F2"
    PURPLE = "#8B5CF6"
    PURPLE_LIGHT = "#F5F3FF"
    SIDEBAR_BG = THEME["sidebar_bg"]
    SIDEBAR_TEXT = THEME["sidebar_text"]
    SIDEBAR_HOVER = THEME["sidebar_hover"]
    SIDEBAR_ACTIVE = "#2563EB"
    CARD_BG = THEME["card_bg"]
    PAGE_BG = "#F1F5F9"

    FONT_DISPLAY = ("Segoe UI", 28, "bold")
    FONT_TITLE = ("Segoe UI", 22, "bold")
    FONT_HEADING = ("Segoe UI", 17, "bold")
    FONT_SUBHEADING = ("Segoe UI", 14, "bold")
    FONT_BODY = ("Segoe UI", 13)
    FONT_SMALL = ("Segoe UI", 11)
    FONT_TINY = ("Segoe UI", 10)
    FONT_BUTTON = ("Segoe UI", 13, "bold")
    FONT_STAT = ("Segoe UI", 32, "bold")

    CORNER_RADIUS = 14
    BUTTON_RADIUS = 10
    PADDING = 24
    CARD_PADDING = 20
    SIDEBAR_WIDTH = 260
