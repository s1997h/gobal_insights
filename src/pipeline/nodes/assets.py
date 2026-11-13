"""Scene art: one generated still per `still` scene, in the aspect ratio of the format that uses it."""

from __future__ import annotations

from typing import Any

from ..context import RunContext
from ..schemas import ScriptDoc
from ..state import RunState
from ..util import read_json, write_json


def assets_node(ctx: RunContext, state: RunState) -> dict[str, Any]:
    p = ctx.paths
    cache_dir = ctx.cfg.root / "cache" / "images"
    price = ctx.cfg.prices.image.get(ctx.image.name, {}).get("usd_per_image", 0.0)
    for fmt in ctx.channel.formats:
        doc = ScriptDoc.model_validate(read_json(p.script(fmt)))
        aspect = "16:9" if fmt == "long" else "9:16"
        image_map: dict[str, str] = {}
        generated = 0
        for scene in doc.scenes:
            if scene.visual.type == "template":
                continue
            if scene.visual.type == "hero_clip":
                ctx.log(
                    f"assets: scene {scene.id} asked for a hero clip; using a still instead (no video provider is plugged in)"
                )
            if ctx.no_stills:
                raise RuntimeError(f"scene {scene.id} needs a still but stills are off")
            out = p.images_dir(fmt) / f"{scene.id}.png"
            prompt = f"{scene.visual.prompt}. {ctx.style.image_suffix}".strip()
            if price > 0:
                ctx.ledger.check_cap(price)
            hit = ctx.image.generate(prompt, aspect, out, cache_dir)  # type: ignore[arg-type]
            if not hit:
                ctx.ledger.record("image", f"image:{ctx.image.name}", 1.0, price)
                generated += 1
            image_map[scene.id] = f"assets/{fmt}/{scene.id}.png"
        write_json(p.image_map(fmt), image_map)
        ctx.log(f"assets[{fmt}]: {len(image_map)} still(s), {generated} newly generated")
    return {}
