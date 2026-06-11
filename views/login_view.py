"""Login / Register view — animated medical center design."""

import math
import random
import tkinter as tk
import customtkinter as ctk

from views.components.theme import Theme


class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_login, on_register=None, **kwargs):
        super().__init__(master, fg_color="#0A1628", **kwargs)
        self.on_login = on_login
        self.on_register = on_register
        self._mode = "login"
        self._pw_visible = False
        self._cpw_visible = False

        # Animation state
        self._particles: list[dict] = []
        self._anim_id = None
        self._slide_y = 0.65          # card starts lower, slides to 0.5
        self._slide_done = False
        self._pulse_sizes: list[float] = [0.0, 0.5, 1.0]

        self._build_ui()
        self.after(100, self._start_animations)

    # ──────────────────────────────────────────────── build

    def _build_ui(self) -> None:
        # ── Animated canvas background
        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#0A1628")
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.bind("<Configure>", lambda e: self._draw_background())

        self._init_particles()

        # ── Card (placed over canvas)
        self.card = ctk.CTkFrame(
            self,
            fg_color="white",
            corner_radius=20,
            border_width=0,
            width=920,
            height=590,
        )
        self.card.place(relx=0.5, rely=self._slide_y, anchor="center")
        self.card.pack_propagate(False)

        self._build_brand_panel()
        self._build_form_panel()

    # ──────────────────────────────────────────────── background canvas

    def _init_particles(self) -> None:
        self._particles = [
            {
                "x": random.uniform(0, 1),
                "y": random.uniform(0, 1),
                "r": random.uniform(2, 10),
                "vx": random.uniform(-0.0002, 0.0002),
                "vy": random.uniform(-0.0004, -0.0001),
                "phase": random.uniform(0, math.tau),
            }
            for _ in range(35)
        ]

    def _draw_background(self) -> None:
        w = self.winfo_width() or 1280
        h = self.winfo_height() or 800
        c = self.canvas
        c.delete("all")

        # ── Gradient bands (dark navy → deep blue)
        steps = 40
        for i in range(steps):
            t = i / steps
            r = int(10 + t * 18)
            g = int(22 + t * 38)
            b = int(40 + t * 88)
            c.create_rectangle(
                0, int(h * i / steps), w, int(h * (i + 1) / steps) + 1,
                fill=f"#{r:02x}{g:02x}{b:02x}", outline="",
            )

        # ── Subtle grid
        for xi in range(0, w, 72):
            c.create_line(xi, 0, xi, h, fill="#132040", width=1)
        for yi in range(0, h, 72):
            c.create_line(0, yi, w, yi, fill="#132040", width=1)

        # ── Static decorative medical crosses
        for rx, ry, sz in [
            (0.06, 0.12, 24), (0.93, 0.20, 18), (0.12, 0.82, 20),
            (0.88, 0.78, 22), (0.50, 0.04, 16), (0.72, 0.55, 14),
            (0.25, 0.48, 12),
        ]:
            self._draw_cross(c, int(rx * w), int(ry * h), sz, "#1E3A6E")

        # ── Pulsing rings (centre-left area)
        for i, size_frac in enumerate(self._pulse_sizes):
            ring_r = int(60 + size_frac * 180)
            alpha = max(0, int(120 * (1 - size_frac)))
            col = f"#{alpha // 3:02x}{alpha // 3:02x}{min(255, alpha + 60):02x}"
            c.create_oval(
                int(0.18 * w) - ring_r, int(0.5 * h) - ring_r,
                int(0.18 * w) + ring_r, int(0.5 * h) + ring_r,
                outline=col, width=2,
            )

        # ── Floating particles
        for p in self._particles:
            px = int(p["x"] * w)
            py = int(p["y"] * h)
            pulse = 0.5 + 0.5 * math.sin(p["phase"])
            rv = max(1, int(p["r"] * (0.75 + 0.25 * pulse)))
            brightness = int(80 + pulse * 100)
            col = f"#{brightness // 4:02x}{brightness // 4:02x}{min(255, brightness + 40):02x}"
            c.create_oval(px - rv, py - rv, px + rv, py + rv, fill=col, outline="")

        # ── Decorative large glowing orbs
        for rx, ry, radius, col in [
            (0.0, 0.0, 220, "#0D2147"),
            (1.0, 1.0, 260, "#0D2147"),
            (0.5, 1.05, 180, "#091B3A"),
        ]:
            ox, oy = int(rx * w), int(ry * h)
            c.create_oval(ox - radius, oy - radius, ox + radius, oy + radius,
                          fill=col, outline="")

    def _draw_cross(self, c: tk.Canvas, cx: int, cy: int, s: int, color: str) -> None:
        t = max(2, s // 3)
        c.create_rectangle(cx - t, cy - s, cx + t, cy + s, fill=color, outline="")
        c.create_rectangle(cx - s, cy - t, cx + s, cy + t, fill=color, outline="")

    # ──────────────────────────────────────────────── animation loop

    def _start_animations(self) -> None:
        self._animate()

    def _animate(self) -> None:
        if not self.winfo_exists():
            return

        # Update particles
        for p in self._particles:
            p["x"] = (p["x"] + p["vx"]) % 1.0
            p["y"] = (p["y"] + p["vy"]) % 1.0
            p["phase"] += 0.045

        # Advance pulsing rings
        for i in range(len(self._pulse_sizes)):
            self._pulse_sizes[i] = (self._pulse_sizes[i] + 0.007) % 1.0

        self._draw_background()

        # Slide-in card animation
        if not self._slide_done:
            target = 0.5
            self._slide_y += (target - self._slide_y) * 0.12
            if abs(self._slide_y - target) < 0.002:
                self._slide_y = target
                self._slide_done = True
            self.card.place(relx=0.5, rely=self._slide_y, anchor="center")

        self._anim_id = self.after(40, self._animate)

    def destroy(self) -> None:
        if self._anim_id:
            self.after_cancel(self._anim_id)
        super().destroy()

    # ──────────────────────────────────────────────── brand panel

    def _build_brand_panel(self) -> None:
        self.brand = ctk.CTkFrame(
            self.card, fg_color="#0F2D6B", corner_radius=0, width=370
        )
        self.brand.pack(side="left", fill="y")
        self.brand.pack_propagate(False)

        # ── Background decorative blobs ──────────────────────────────────────
        ctk.CTkFrame(
            self.brand, fg_color="#1a3f8f", corner_radius=120,
            width=240, height=240,
        ).place(relx=-0.30, rely=-0.08)
        ctk.CTkFrame(
            self.brand, fg_color="#163580", corner_radius=100,
            width=180, height=180,
        ).place(relx=0.70, rely=0.78)
        ctk.CTkFrame(
            self.brand, fg_color="#122d72", corner_radius=60,
            width=100, height=100,
        ).place(relx=0.55, rely=-0.04)

        # ── Content container (left-aligned, padded) ─────────────────────────
        inner = ctk.CTkFrame(self.brand, fg_color="transparent")
        inner.place(relx=0, rely=0, relwidth=1, relheight=1)

        # top spacer
        ctk.CTkFrame(inner, fg_color="transparent", height=56).pack()

        # ── Logo badge ───────────────────────────────────────────────────────
        logo_frame = ctk.CTkFrame(
            inner, fg_color="#1E4DB7", corner_radius=18,
            width=68, height=68,
            border_width=2, border_color="#3B6FD4",
        )
        logo_frame.pack(padx=36, anchor="w")
        logo_frame.pack_propagate(False)

        # Medical cross inside the badge
        cross_v = ctk.CTkFrame(logo_frame, fg_color="white", width=10, height=34, corner_radius=3)
        cross_v.place(relx=0.5, rely=0.5, anchor="center")
        cross_h = ctk.CTkFrame(logo_frame, fg_color="white", width=34, height=10, corner_radius=3)
        cross_h.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkFrame(inner, fg_color="transparent", height=20).pack()

        # ── Clinic name ──────────────────────────────────────────────────────
        ctk.CTkLabel(
            inner,
            text="MEDICAL CENTER",
            font=("Segoe UI", 28, "bold"),
            text_color="white",
            anchor="w",
        ).pack(fill="x", padx=36)

        # ── Subtitle ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            inner,
            text="Clinic Management System",
            font=("Segoe UI", 11),
            text_color="#7EB3FF",
            anchor="w",
        ).pack(fill="x", padx=38, pady=(4, 0))

        # ── Gradient separator ────────────────────────────────────────────────
        ctk.CTkFrame(
            inner, fg_color="#3B6FD4", height=2, corner_radius=1
        ).pack(fill="x", padx=36, pady=(16, 20))

        # ── Tagline ───────────────────────────────────────────────────────────
        ctk.CTkLabel(
            inner,
            text="Professional healthcare\nmanagement system for\nmodern medical practices.",
            font=("Segoe UI", 13),
            text_color="#A8CAFF",
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=36)

        ctk.CTkFrame(inner, fg_color="transparent", height=28).pack()

        # ── Feature list ──────────────────────────────────────────────────────
        features = [
            ("#22C55E", "◆", "Secure & Encrypted"),
            ("#3B82F6", "◆", "Fast & Reliable"),
            ("#A78BFA", "◆", "PhilHealth Integrated"),
        ]
        for dot_color, dot, label in features:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", padx=36, pady=4)
            ctk.CTkLabel(
                row, text=dot, font=("Segoe UI", 9),
                text_color=dot_color, width=16,
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=label, font=("Segoe UI", 12),
                text_color="#C8DEFF", anchor="w",
            ).pack(side="left", padx=(6, 0))

        ctk.CTkFrame(inner, fg_color="transparent", height=24).pack()

        # ── Version pill ──────────────────────────────────────────────────────
        pill = ctk.CTkFrame(
            inner, fg_color="#193F8A", corner_radius=20,
            border_width=1, border_color="#2A55B0",
        )
        pill.pack(padx=36, anchor="w")
        ctk.CTkLabel(
            pill, text="Medical Center  ·  v2.0",
            font=("Segoe UI", 9, "bold"),
            text_color="#7EB3FF",
        ).pack(padx=12, pady=5)

        # ── Copyright ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            inner,
            text="© 2026 Medical Center",
            font=("Segoe UI", 9),
            text_color="#3B6FD4",
        ).pack(side="bottom", pady=20, anchor="w", padx=36)

    # ──────────────────────────────────────────────── form panel

    def _build_form_panel(self) -> None:
        self.form_panel = ctk.CTkFrame(
            self.card, fg_color="white", corner_radius=0
        )
        self.form_panel.pack(side="left", fill="both", expand=True)
        self._render_mode()

    # ──────────────────────────────────────────────── mode switching

    def _render_mode(self) -> None:
        for w in self.form_panel.winfo_children():
            w.destroy()
        if self._mode == "login":
            self._build_login_form()
        else:
            self._build_register_form()

    def _switch_mode(self, mode: str) -> None:
        self._mode = mode
        self._pw_visible = False
        self._cpw_visible = False
        self.card.configure(height=620 if mode == "register" else 580)
        self._render_mode()

    # ──────────────────────────────────────────────── login form

    def _build_login_form(self) -> None:
        panel = self.form_panel

        # Header section
        header = ctk.CTkFrame(panel, fg_color="#F4F8FF", corner_radius=0)
        header.pack(fill="x")

        # small clinic label above title
        ctk.CTkLabel(
            header,
            text="MEDICAL CENTER  ·  Clinic Management System",
            font=("Segoe UI", 9, "bold"),
            text_color="#7EB3FF",
        ).pack(pady=(36, 0))

        ctk.CTkLabel(
            header,
            text="Welcome Back",
            font=("Segoe UI", 30, "bold"),
            text_color="#0F2D6B",
        ).pack(pady=(4, 2))
        ctk.CTkLabel(
            header,
            text="Sign in to your account to continue",
            font=("Segoe UI", 12),
            text_color="#64748B",
        ).pack(pady=(0, 0))

        # Accent bar
        ctk.CTkFrame(header, fg_color="#1E4DB7", height=3, corner_radius=0).pack(
            fill="x", pady=(16, 0)
        )

        form = ctk.CTkFrame(panel, fg_color="white")
        form.pack(fill="x", padx=44, pady=(28, 0))

        # Username
        ctk.CTkLabel(
            form, text="Username", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(fill="x", pady=(0, 4))
        self.username_entry = ctk.CTkEntry(
            form, height=46, corner_radius=10,
            font=Theme.FONT_BODY, border_color="#CBD5E1",
            border_width=2, placeholder_text="Enter your username",
        )
        self.username_entry.pack(fill="x", pady=(0, 18))
        self.username_entry.bind("<FocusIn>",
            lambda e: self.username_entry.configure(border_color=Theme.ACCENT))
        self.username_entry.bind("<FocusOut>",
            lambda e: self.username_entry.configure(border_color="#CBD5E1"))

        # Password
        ctk.CTkLabel(
            form, text="Password", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(fill="x", pady=(0, 4))
        pw_row = ctk.CTkFrame(form, fg_color="transparent")
        pw_row.pack(fill="x", pady=(0, 28))
        pw_row.grid_columnconfigure(0, weight=1)

        self.password_entry = ctk.CTkEntry(
            pw_row, height=46, corner_radius=10,
            font=Theme.FONT_BODY, border_color="#CBD5E1",
            border_width=2, placeholder_text="Enter your password", show="•",
        )
        self.password_entry.grid(row=0, column=0, sticky="ew")
        self.password_entry.bind("<Return>", lambda e: self._login())
        self.password_entry.bind("<FocusIn>",
            lambda e: self.password_entry.configure(border_color=Theme.ACCENT))
        self.password_entry.bind("<FocusOut>",
            lambda e: self.password_entry.configure(border_color="#CBD5E1"))

        self._eye_btn = ctk.CTkButton(
            pw_row, text="👁", width=46, height=46, corner_radius=10,
            fg_color="#F1F5F9", hover_color="#E2E8F0",
            text_color=Theme.TEXT_SECONDARY, font=("Segoe UI Emoji", 14),
            command=self._toggle_pw_visibility,
        )
        self._eye_btn.grid(row=0, column=1, padx=(8, 0))

        # Sign In button
        self.login_btn = ctk.CTkButton(
            form, text="  Sign In  →", height=50, corner_radius=12,
            font=("Segoe UI", 14, "bold"),
            fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER,
            command=self._login,
        )
        self.login_btn.pack(fill="x")

        # Divider + register link
        div_frame = ctk.CTkFrame(form, fg_color="transparent")
        div_frame.pack(fill="x", pady=(22, 0))
        ctk.CTkFrame(div_frame, fg_color="#E2E8F0", height=1).pack(
            fill="x", side="left", expand=True, pady=8)
        ctk.CTkLabel(
            div_frame, text="  or  ", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(side="left")
        ctk.CTkFrame(div_frame, fg_color="#E2E8F0", height=1).pack(
            fill="x", side="left", expand=True, pady=8)

        reg_frame = ctk.CTkFrame(form, fg_color="transparent")
        reg_frame.pack(pady=(10, 0))
        ctk.CTkLabel(
            reg_frame, text="Don't have an account?",
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
        ).pack(side="left")
        ctk.CTkButton(
            reg_frame, text="Create one",
            font=("Segoe UI", 11, "bold"),
            fg_color="transparent", hover_color="#EFF6FF",
            text_color=Theme.ACCENT, height=28, width=80,
            command=lambda: self._switch_mode("register"),
        ).pack(side="left", padx=(4, 0))

    def _toggle_pw_visibility(self) -> None:
        self._pw_visible = not self._pw_visible
        self.password_entry.configure(show="" if self._pw_visible else "•")

    # ──────────────────────────────────────────────── register form

    def _build_register_form(self) -> None:
        panel = self.form_panel

        scroll = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", scrollbar_button_color="#E2E8F0",
        )
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll, text="Create Account",
            font=("Segoe UI", 24, "bold"), text_color=Theme.TEXT_PRIMARY,
        ).pack(pady=(40, 4))
        ctk.CTkLabel(
            scroll, text="Fill in the details below to register",
            font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY,
        ).pack(pady=(0, 24))

        form = ctk.CTkFrame(scroll, fg_color="transparent")
        form.pack(fill="x", padx=44)

        def field(label, placeholder, show=""):
            ctk.CTkLabel(
                form, text=label, font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_SECONDARY, anchor="w",
            ).pack(fill="x", pady=(0, 4))
            e = ctk.CTkEntry(
                form, height=42, corner_radius=10,
                font=Theme.FONT_BODY, border_color="#CBD5E1",
                border_width=2, placeholder_text=placeholder, show=show,
            )
            e.pack(fill="x", pady=(0, 14))
            e.bind("<FocusIn>", lambda ev, ew=e: ew.configure(border_color=Theme.ACCENT))
            e.bind("<FocusOut>", lambda ev, ew=e: ew.configure(border_color="#CBD5E1"))
            return e

        self.reg_fullname = field("Full Name", "e.g. Dr. Juan dela Cruz")
        self.reg_username = field("Username", "Choose a username (min 3 chars)")
        self.reg_email = field("Email Address", "your@email.com")

        # Password with toggle
        ctk.CTkLabel(
            form, text="Password", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(fill="x", pady=(0, 4))
        pw_row = ctk.CTkFrame(form, fg_color="transparent")
        pw_row.pack(fill="x", pady=(0, 14))
        pw_row.grid_columnconfigure(0, weight=1)
        self.reg_password = ctk.CTkEntry(
            pw_row, height=42, corner_radius=10,
            font=Theme.FONT_BODY, border_color="#CBD5E1",
            border_width=2, placeholder_text="At least 6 characters", show="•",
        )
        self.reg_password.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            pw_row, text="👁", width=42, height=42, corner_radius=10,
            fg_color="#F1F5F9", hover_color="#E2E8F0",
            text_color=Theme.TEXT_SECONDARY, font=("Segoe UI Emoji", 13),
            command=self._toggle_reg_pw,
        ).grid(row=0, column=1, padx=(8, 0))

        # Confirm password
        ctk.CTkLabel(
            form, text="Confirm Password", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(fill="x", pady=(0, 4))
        cpw_row = ctk.CTkFrame(form, fg_color="transparent")
        cpw_row.pack(fill="x", pady=(0, 20))
        cpw_row.grid_columnconfigure(0, weight=1)
        self.reg_confirm = ctk.CTkEntry(
            cpw_row, height=42, corner_radius=10,
            font=Theme.FONT_BODY, border_color="#CBD5E1",
            border_width=2, placeholder_text="Re-enter password", show="•",
        )
        self.reg_confirm.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            cpw_row, text="👁", width=42, height=42, corner_radius=10,
            fg_color="#F1F5F9", hover_color="#E2E8F0",
            text_color=Theme.TEXT_SECONDARY, font=("Segoe UI Emoji", 13),
            command=self._toggle_cpw,
        ).grid(row=0, column=1, padx=(8, 0))

        self.register_btn = ctk.CTkButton(
            form, text="Create Account", height=48, corner_radius=12,
            font=("Segoe UI", 14, "bold"),
            fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER,
            command=self._submit_register,
        )
        self.register_btn.pack(fill="x")

        back_frame = ctk.CTkFrame(form, fg_color="transparent")
        back_frame.pack(pady=(16, 28))
        ctk.CTkLabel(
            back_frame, text="Already have an account?",
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
        ).pack(side="left")
        ctk.CTkButton(
            back_frame, text="Sign in",
            font=("Segoe UI", 11, "bold"),
            fg_color="transparent", hover_color="#EFF6FF",
            text_color=Theme.ACCENT, height=28, width=60,
            command=lambda: self._switch_mode("login"),
        ).pack(side="left", padx=(4, 0))

    def _toggle_reg_pw(self) -> None:
        self._pw_visible = not self._pw_visible
        self.reg_password.configure(show="" if self._pw_visible else "•")

    def _toggle_cpw(self) -> None:
        self._cpw_visible = not self._cpw_visible
        self.reg_confirm.configure(show="" if self._cpw_visible else "•")

    # ──────────────────────────────────────────────── actions

    def _login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self._flash_error("Please enter your username and password.")
            return
        self.login_btn.configure(state="disabled", text="Signing in…")
        self.update_idletasks()
        if not self.on_login(username, password):
            self.login_btn.configure(state="normal", text="  Sign In  →")

    def _submit_register(self) -> None:
        full_name = self.reg_fullname.get().strip()
        username = self.reg_username.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()

        if not all([full_name, username, email, password, confirm]):
            self._flash_error("All fields are required.")
            return
        if len(username) < 3:
            self._flash_error("Username must be at least 3 characters.")
            return
        if len(password) < 6:
            self._flash_error("Password must be at least 6 characters.")
            return
        if password != confirm:
            self._flash_error("Passwords do not match.")
            return
        if self.on_register is None:
            self._flash_error("Registration is not available right now.")
            return

        self.register_btn.configure(state="disabled", text="Creating account…")
        self.update_idletasks()
        success, message = self.on_register({
            "full_name": full_name,
            "username": username,
            "email": email,
            "password": password,
        })
        if success:
            self._switch_mode("login")
            self._flash_success(f"Account created! You can now sign in, {full_name}.")
        else:
            self.register_btn.configure(state="normal", text="Create Account")
            self._flash_error(message)

    # ──────────────────────────────────────────────── banners

    def _flash_error(self, msg: str) -> None:
        self._show_banner(msg, "#FEF2F2", "#EF4444")

    def _flash_success(self, msg: str) -> None:
        self._show_banner(msg, "#ECFDF5", "#10B981")

    def _show_banner(self, msg: str, bg: str, fg: str) -> None:
        for w in self.form_panel.winfo_children():
            if getattr(w, "_is_banner", False):
                w.destroy()
        banner = ctk.CTkFrame(
            self.form_panel, fg_color=bg, corner_radius=8,
            border_width=1, border_color=fg,
        )
        banner._is_banner = True
        banner.place(relx=0.5, rely=0.94, anchor="center", relwidth=0.88)
        ctk.CTkLabel(
            banner, text=msg, font=Theme.FONT_SMALL,
            text_color=fg, wraplength=320,
        ).pack(pady=8, padx=12)
        self.after(4000, lambda: banner.destroy() if banner.winfo_exists() else None)
