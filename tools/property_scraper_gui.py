#!/usr/bin/env python3
from __future__ import annotations

import os
import queue
import re
import shutil
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from urllib import error as urlerror

import property_scraper

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None
    Image = None
    ImageDraw = None


class ScraperApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Bostadsscraper")
        self.root.geometry("560x310")
        self.root.minsize(420, 260)

        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.is_scraping = False
        self.output_dir = Path("scrapes").resolve()
        self.status = tk.StringVar(value="")
        self.tray_icon = None

        self._build_ui()
        self._setup_tray()
        self.root.protocol("WM_DELETE_WINDOW", self._close_or_hide)
        self.root.after(100, self._drain_messages)

    def run(self) -> None:
        self.root.mainloop()
        if self.tray_icon:
            self.tray_icon.stop()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        body = ttk.Frame(self.root, padding=14)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        ttk.Label(body, text="Annonslänkar:").grid(row=0, column=0, sticky="w")

        self.url_text = tk.Text(body, height=8, wrap="word", undo=True)
        self.url_text.grid(row=1, column=0, sticky="nsew", pady=(4, 10))

        actions = ttk.Frame(body)
        actions.grid(row=2, column=0, sticky="ew")

        self.scrape_button = ttk.Button(actions, text="Scrape", command=self._start_scrape)
        self.scrape_button.grid(row=0, column=0, sticky="w")

        ttk.Button(actions, text="Clear", command=self._clear_urls).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )

        ttk.Button(actions, text="Öppna mapp", command=self._open_output_dir).grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )

        log_row = ttk.Frame(body)
        log_row.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        log_row.columnconfigure(1, weight=1)

        ttk.Label(log_row, text="Log:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Label(log_row, textvariable=self.status).grid(row=0, column=1, sticky="w")

    def _setup_tray(self) -> None:
        if pystray is None or Image is None or ImageDraw is None:
            return

        image = Image.new("RGB", (64, 64), "#0f5132")
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 18, 48, 46), fill="#ffffff")
        draw.rectangle((21, 25, 43, 30), fill="#0f5132")
        draw.rectangle((21, 35, 36, 39), fill="#0f5132")

        menu = pystray.Menu(
            pystray.MenuItem("Visa", lambda: self.root.after(0, self._show_window)),
            pystray.MenuItem("Avsluta", lambda: self.root.after(0, self._quit)),
        )
        self.tray_icon = pystray.Icon("property-scraper", image, "Bostadsscraper", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _start_scrape(self) -> None:
        urls = self._extract_urls()
        if not urls:
            self._set_status("Ingen länk.")
            return

        if self.is_scraping:
            return

        self.is_scraping = True
        self.scrape_button.configure(state="disabled")
        self._set_status("Scrapear...")
        threading.Thread(target=self._scrape_worker, args=(urls,), daemon=True).start()

    def _scrape_worker(self, urls: list[str]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        saved = 0
        for url in urls:
            try:
                data = property_scraper.extract_listing(
                    url,
                    timeout=20,
                    user_agent=property_scraper.DEFAULT_USER_AGENT,
                )
                listing_md = property_scraper.save_listing(
                    data,
                    self.output_dir,
                    download=True,
                    max_images=30,
                    timeout=20,
                    user_agent=property_scraper.DEFAULT_USER_AGENT,
                    delay=1.0,
                )
                self._zip_listing(listing_md.parent)
            except (urlerror.URLError, TimeoutError, OSError, PermissionError, ValueError) as exc:
                self.messages.put(("log", f"Fel: {exc}"))
                continue

            saved += 1

        self.messages.put(("done", saved))

    def _zip_listing(self, listing_dir: Path) -> Path:
        zip_base = listing_dir.with_suffix("")
        zip_path = listing_dir.with_suffix(".zip")
        if zip_path.exists():
            zip_path.unlink()
        shutil.make_archive(str(zip_base), "zip", listing_dir)
        return zip_path

    def _drain_messages(self) -> None:
        try:
            while True:
                kind, payload = self.messages.get_nowait()
                if kind == "log":
                    self._set_status(str(payload))
                elif kind == "done":
                    self.is_scraping = False
                    self.scrape_button.configure(state="normal")
                    count = int(payload)
                    suffix = "er" if count != 1 else ""
                    self._set_status(f"Klart. Sparade {count} annons{suffix}.")
        except queue.Empty:
            pass

        self.root.after(100, self._drain_messages)

    def _extract_urls(self) -> list[str]:
        raw = self.url_text.get("1.0", "end")
        urls = re.findall(r"https?://[^\s<>\"]+", raw)
        return [url.rstrip(".,);]") for url in urls]

    def _clear_urls(self) -> None:
        self.url_text.delete("1.0", "end")
        self._set_status("")

    def _open_output_dir(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(self.output_dir)

    def _hide_window(self) -> None:
        if self.tray_icon:
            self.root.withdraw()
        else:
            self.root.iconify()

    def _show_window(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _close_or_hide(self) -> None:
        if self.tray_icon:
            self._hide_window()
        else:
            self.root.destroy()

    def _quit(self) -> None:
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()

    def _set_status(self, message: str) -> None:
        self.status.set(message)


def main() -> None:
    ScraperApp().run()


if __name__ == "__main__":
    main()
