"""Scene-art adapter: one image per call, cached by a hash of provider, model, aspect and prompt."""

from __future__ import annotations

import base64
import os
import random
import shutil
from pathlib import Path
from typing import Literal, Protocol

import httpx
from PIL import Image, ImageDraw

from ..config import ImageModels
from ..util import sha

Aspect = Literal["16:9", "9:16"]


class ImageGen(Protocol):
    name: str

    def generate(self, prompt: str, aspect: Aspect, out_path: Path, cache_dir: Path) -> bool:
        """Write the image to out_path. Returns True if it came from the cache (so no cost)."""
        ...


class _CachedImage:
    name = "base"
    model = ""

    def _render(self, prompt: str, aspect: Aspect, out: Path) -> None:
        raise NotImplementedError

    def generate(self, prompt: str, aspect: Aspect, out_path: Path, cache_dir: Path) -> bool:
        cache_dir.mkdir(parents=True, exist_ok=True)
        key = sha(self.name, self.model, aspect, prompt)
        cached = cache_dir / f"{key}.png"
        hit = cached.exists()
        if not hit:
            tmp = cached.with_suffix(".tmp.png")
            self._render(prompt, aspect, tmp)
            os.replace(tmp, cached)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cached, out_path)
        return hit


class OpenAIImage(_CachedImage):
    """OpenAI Images API. Not exercised against the live API in the offline build; check model name and prices."""

    name = "openai"

    def __init__(self, cfg: ImageModels, key: str | None = None):
        self.model = cfg.model
        self.quality = cfg.quality
        self.key = key or os.environ.get("OPENAI_API_KEY")
        if not self.key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set (put it in .env), or run with --no-stills / --offline. "
                "Stills are optional: templates alone cost nothing."
            )

    def _render(self, prompt: str, aspect: Aspect, out: Path) -> None:
        size = "1536x1024" if aspect == "16:9" else "1024x1536"
        r = httpx.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {self.key}"},
            json={"model": self.model, "prompt": prompt, "size": size, "quality": self.quality, "n": 1},
            timeout=300,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"image API error {r.status_code}: {r.text[:300]}")
        item = r.json()["data"][0]
        if item.get("b64_json"):
            out.write_bytes(base64.b64decode(item["b64_json"]))
        else:
            out.write_bytes(httpx.get(item["url"], timeout=120).content)


class FakeImage(_CachedImage):
    """Offline stand-in: a flat geometric picture seeded by the prompt, clearly marked as fake."""

    name = "fake"
    model = "pillow"

    def _render(self, prompt: str, aspect: Aspect, out: Path) -> None:
        w, h = (1280, 720) if aspect == "16:9" else (720, 1280)
        rng = random.Random(prompt)
        img = Image.new("RGB", (w, h), (11, 27, 51))
        d = ImageDraw.Draw(img)
        for y in range(h):  # vertical gradient
            k = y / h
            d.line([(0, y), (w, y)], fill=(int(11 + 20 * k), int(27 + 40 * k), int(51 + 60 * k)))
        for _ in range(9):
            x, y = rng.randint(0, w), rng.randint(0, h)
            r = rng.randint(min(w, h) // 12, min(w, h) // 4)
            col = rng.choice([(242, 184, 75), (46, 196, 182), (244, 246, 250)])
            if rng.random() < 0.5:
                d.ellipse([x - r, y - r, x + r, y + r], fill=col)
            else:
                d.rounded_rectangle([x - r, y - r // 2, x + r, y + r // 2], radius=r // 4, fill=col)
        d.rectangle([0, h - 36, w, h], fill=(11, 27, 51))
        d.text((12, h - 28), "FAKE STILL (offline)", fill=(244, 246, 250))
        img.save(out)


def build_image(cfg: ImageModels, offline: bool, needed: bool) -> ImageGen:
    if offline or cfg.provider == "fake":
        return FakeImage()
    if cfg.provider == "openai":
        if not needed:  # stills are off for this run: don't demand a key
            return FakeImage()
        return OpenAIImage(cfg)
    raise ValueError(f"unknown image provider {cfg.provider!r}")
