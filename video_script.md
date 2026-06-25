# SWAAHA / "The $40 GPU Bug" — YouTube video script

**Runtime target:** ~3:15 · **Format:** 1080p 16:9 explainer · **VO voice:** Daniel (en_GB)
**Tone:** self-deprecating but useful — *dire foolishness + how to prevent it*

---

### 1 · COLD OPEN  (~12s)
**On screen:** `$40.  85 minutes.  0 clips.`
**VO:** I just set forty dollars on fire. In eighty-five minutes. On one bug. Twelve GPUs, a
fourteen-billion-parameter video model — and at the end of it, zero clips. Let me show you exactly
how, so it never happens to you.

### 2 · THE SETUP  (~25s)
**On screen:** `12 images → 12 clips · 12× A100-80GB · $2.50/GPU-hr`
**VO:** Here's the job. I'm rendering an AI music video — twelve still images turned into twelve
animated clips. To make it fast, I fanned the work out across twelve A100 GPUs in parallel, one clip
each. Parallel means fast. It also means you can waste money twelve ways at once. Remember that line.

### 3 · THE CLIFF  (~30s)
**On screen:** `40/40 steps ✓  →  CUDA out of memory`
**VO:** Every clip ran its full forty steps. The expensive part — done. I was already planning the
edit. And then, on the very last operation — turning the finished math into actual pixels — every
GPU ran out of memory. Not during the hard part. At the finish line. Because a video decoder unpacks
all eighty-one frames at once, and that's the most memory-hungry moment in the entire pipeline. It
only happens after you've already paid for everything else.

### 4 · THE CASCADE  (~28s)
**On screen:** `1 OOM → cancel × 11 → 0 saved`
**VO:** And here's what turned annoying into expensive. My batch was set to fail-fast. So the instant
one clip crashed, the system cancelled the other eleven — clips that were seconds from finishing. One
death, eleven innocents. Eighty-five minutes of compute, nothing written to disk. The bill? About
forty dollars. For nothing.

### 5 · FOOLISH, NOT UNLUCKY  (~22s)
**On screen:** `I scaled before I validated.`
**VO:** And I want to be honest — this wasn't bad luck. Bad luck is a GPU dying. This was me scaling
up before testing a single unit. I sent twelve jobs to find a bug that one job would have caught. The
failure lived in the cheapest thing to test and the last thing to run — the perfect smoke test — and
I skipped it, because the code looked done.

### 6 · THE FIX  (~25s)
**On screen:** `enable_tiling() · enable_slicing() · return_exceptions=True`
**VO:** The fix is almost insultingly small. Two lines so the decoder works in tiles and never spikes
the memory. And one keyword — return exceptions — so a single failure saves the survivors instead of
nuking the whole batch. Same bug, now: three dollars of damage instead of forty.

### 7 · THE 6 GUARDRAILS  (~38s)
**On screen:** the six numbered rules
**VO:** So here are the six rules I'm burning into my brain. One — canary before you fan out: run one
unit end to end before you launch a hundred. Two — find the peak-memory moment; for video models it's
the decode, at the end. Three — isolate failures, so one death never cancels the swarm. Four — save
results as they land, and make re-runs resumable. Five — do the cost math out loud, before you hit
enter. Six — cache your big models once; don't re-download them on every worker.

### 8 · THE PRINCIPLE / OUTRO  (~18s)
**On screen:** `The cheapest place to find a bug is a $2 canary, not a $40 swarm.`
**VO:** If you remember one thing, make it this: the cheapest place to find a bug is a two-dollar
canary, not a forty-dollar swarm. Test the last mile first. I wrote the whole thing up — link in the
description. Mistakes are a lot cheaper when you publish them. See you in the next one.

---

**Title ideas:** "I Wasted $40 on ONE GPU Bug (don't do this)" · "How to Burn $40 in 85 Minutes"
**Description CTA:** Full write-up → https://amitpandeytiktok.github.io/the-40-dollar-gpu-bug/
