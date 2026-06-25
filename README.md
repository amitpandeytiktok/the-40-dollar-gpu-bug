# I Set ~$40 on Fire in 85 Minutes — on One GPU Bug

> **Live article:** https://amitpandeytiktok.github.io/the-40-dollar-gpu-bug/

Twelve A100s. Eighty-five minutes. A 14-billion-parameter video model. **Zero clips saved.**
This is the honest autopsy of a spectacularly dumb render failure — and the six-line checklist
that makes sure it never happens again.

## The receipt for nothing

| Line item | |
|---|---|
| 12 × A100-80GB · ~1.4 h each | $2.50 / GPU-hr |
| 40/40 diffusion steps completed | ✅ paid in full |
| VAE decode (the **last** step) | ❌ OOM |
| Clips delivered | **0 / 12** |
| **Net result** | **~$40 → /dev/null** |

The job was **SWAAHA**, an image-to-video pass: 12 keyframes → 12 animated clips via
**Wan2.2 I2V-A14B** on [Modal](https://modal.com), fanned out across 12 A100-80GB GPUs.

## Two bugs, stacked

### Bug #1 — the memory cliff is at the *end*, not the middle
Sampling fit in VRAM for all 40 steps. But a **video** VAE decodes all 81 frames *at once*, and
that decode — the most memory-hungry moment in the pipeline — only runs **after** you've already
paid for sampling. The model sailed through the costly 99% and OOM'd on the final 1%:

```
# diffusers/.../autoencoder_kl_wan.py
OutOfMemoryError: CUDA out of memory. Tried to allocate 1.32 GiB.
GPU 0 has a total capacity of 79.25 GiB of which 1.06 GiB is free.
```

**Fix — tile + slice the decode so peak memory stays bounded:**
```python
pipe.to("cuda")
+ pipe.vae.enable_tiling()
+ pipe.vae.enable_slicing()
```
Plus a fragmentation guard: `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.

### Bug #2 — one death sentenced eleven innocents
The batch was a plain fan-out, and `starmap` **fails fast** — the instant one input raises, the
whole map is cancelled:

```python
for out_p, data in zip(todo, render.starmap(args)):   # fail-fast
    out_p.write_bytes(data)
```

So clip #7's OOM sent `Successfully canceled input` to the eleven clips that were *seconds from
done*. **Fix — isolate failures and save the survivors:**
```python
for out_p, data in zip(todo, render.starmap(args, return_exceptions=True)):
    if isinstance(data, Exception):
        print(f"FAILED {out_p.name}: {data}"); continue
    out_p.write_bytes(data)        # save the ones that worked
```

With one keyword, the same OOM costs **1** clip (~$3), not 12 (~$40).

## The 6 guardrails (steal these)

1. **Canary before you fan out.** Run ONE unit end-to-end — including the last step — before
   launching N. A `--limit 1` flag is the highest-ROI line in any batch job.
2. **Find the peak-memory moment, not the average.** For diffusion it's the VAE decode, at the end.
   `enable_tiling()` + `enable_slicing()` by default; test at real resolution/frame-count.
3. **Isolate failures in any fan-out.** `return_exceptions=True` / `--keep-going`. One death must
   never cancel the swarm.
4. **Save incrementally & make it resumable.** Write each result as it lands; re-runs skip finished
   work, so a crash costs minutes, not the batch.
5. **Do the cost math out loud — first.** `$/GPU-hr × parallelism × wall-time`. Say the number
   before you hit enter; set a spend cap + alert.
6. **Pay the cold-start tax once.** Don't let N cold workers each re-download a 60–80 GB model.
   Cache weights in a shared Volume (and bake into the image), then scale out warm.

> **The cheapest place to find a bug is a $2 canary, not a $40 swarm. Test the last mile first.**

## Pre-flight checklist

- [ ] Smoke-tested ONE unit end-to-end (incl. the final step)
- [ ] Verified peak memory at real resolution / length
- [ ] Fan-out isolates failures (`return_exceptions` / keep-going)
- [ ] Results saved incrementally; re-run skips finished work
- [ ] Said the cost number out loud; spend cap + alert set
- [ ] Heavy assets cached/warmed once, not per-worker

---

The bug is fixed in four lines. The redone render costs ~$25 for all twelve clips, or ~$2–4 to
prove it on one first. The $40 was just tuition — the lesson is the asset.

*Written in public, the afternoon it happened.*
