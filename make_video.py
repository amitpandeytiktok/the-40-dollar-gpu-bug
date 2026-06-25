#!/usr/bin/env python3
"""Render 'The $40 GPU Bug' explainer video: PIL slides + `say` TTS + ffmpeg.
Outputs: build/the-40-dollar-gpu-bug.mp4 (1080p 16:9) and thumbnail.png (1280x720)."""
import os, subprocess, shutil, json
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FFMPEG = "/opt/homebrew/Cellar/ffmpeg-full/8.1.1/bin/ffmpeg"
FFPROBE = "/opt/homebrew/Cellar/ffmpeg-full/8.1.1/bin/ffprobe"
HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
os.makedirs(BUILD, exist_ok=True)

# theme
BG="#0d1117"; PANEL="#161b22"; PANEL2="#0a0d12"; BORDER="#30363d"
TXT="#e6edf3"; DIM="#8b949e"; ACCENT="#58a6ff"; GREEN="#3fb950"
YELLOW="#e3b341"; RED="#f85149"; ORANGE="#db6d28"

HEL="/System/Library/Fonts/Helvetica.ttc"
MENLO="/System/Library/Fonts/Menlo.ttc"
def f_bold(s):  return ImageFont.truetype(HEL, s, index=1)
def f_reg(s):   return ImageFont.truetype(HEL, s, index=0)
def f_light(s): return ImageFont.truetype(HEL, s, index=4)
def f_mono(s):  return ImageFont.truetype(MENLO, s, index=0)

def measure(draw, text, font):
    b = draw.textbbox((0,0), text, font=font); return b[2]-b[0], b[3]-b[1]

def wrap(draw, text, font, max_w):
    words = text.split(); lines=[]; cur=""
    for w in words:
        t = (cur+" "+w).strip()
        if measure(draw,t,font)[0] <= max_w: cur=t
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines

def base():
    img = Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    # header chip
    d.ellipse((80,72,98,90), fill=RED)
    d.text((112,68), "THE $40 GPU BUG  ·  build-in-public post-mortem",
           font=f_reg(26), fill=DIM)
    # thin rule under header
    d.line((80,118,W-80,118), fill=BORDER, width=2)
    return img,d

def footer(d, idx, total):
    d.text((80,H-46), "amitpandeytiktok.github.io/the-40-dollar-gpu-bug",
           font=f_mono(22), fill=DIM)
    d.text((W-150,H-46), f"{idx:02d} / {total:02d}", font=f_mono(22), fill=DIM)

def caption(d, text):
    """burned caption bar at bottom; auto-shrink to fit."""
    pad=44; x0=80; x1=W-80; y1=H-70; max_w=x1-x0-2*pad
    for size in (36,34,32,30,28,26):
        font=f_reg(size); lines=wrap(d,text,font,max_w)
        lh=size+10; box_h=len(lines)*lh+2*pad
        if len(lines)<=4 and box_h<=300: break
    y0=y1-box_h
    d.rounded_rectangle((x0,y0,x1,y1), radius=18, fill=PANEL, outline=BORDER, width=2)
    d.rectangle((x0,y0,x0+6,y1), fill=ACCENT)  # accent edge
    ty=y0+pad
    for ln in lines:
        d.text((x0+pad,ty), ln, font=font, fill=TXT); ty+=lh
    return y0

def hcenter(d, text, font, y, fill):
    w,_=measure(d,text,font); d.text(((W-w)//2,y), text, font=font, fill=fill); return w

# ---- vector glyphs (avoid font tofu for arrows/checks) ----
def d_arrow_r(d,x,cy,s,c):
    lw=max(5,s//9); d.line((x,cy,x+s,cy),fill=c,width=lw); hl=s*0.42
    d.line((x+s-hl,cy-hl*0.75,x+s,cy),fill=c,width=lw)
    d.line((x+s-hl,cy+hl*0.75,x+s,cy),fill=c,width=lw)
def d_arrow_d(d,x,cy,s,c):
    cx=x+s/2; lw=max(5,s//9); top=cy-s/2; bot=cy+s/2
    d.line((cx,top,cx,bot),fill=c,width=lw); hl=s*0.42
    d.line((cx-hl*0.75,bot-hl,cx,bot),fill=c,width=lw)
    d.line((cx+hl*0.75,bot-hl,cx,bot),fill=c,width=lw)
def d_check(d,x,cy,s,c):
    lw=max(5,s//7); t=cy-s/2
    d.line((x+0.12*s,t+0.55*s,x+0.40*s,t+0.82*s),fill=c,width=lw)
    d.line((x+0.40*s,t+0.82*s,x+0.90*s,t+0.16*s),fill=c,width=lw)
def d_cross(d,x,cy,s,c):
    lw=max(5,s//7); t=cy-s/2
    d.line((x+0.18*s,t+0.18*s,x+0.82*s,t+0.82*s),fill=c,width=lw)
    d.line((x+0.82*s,t+0.18*s,x+0.18*s,t+0.82*s),fill=c,width=lw)

# inline row of mixed text + vector-glyph tokens, horizontally centered.
# token: ("t",text,font,color) | ("ar"|"ad"|"ck"|"cx", size, color)
def _tw(d,t): return measure(d,t[1],t[2])[0] if t[0]=="t" else t[1]
def row_width(d,tokens,gap): return sum(_tw(d,t) for t in tokens)+gap*(len(tokens)-1)
def draw_row(d,y,tokens,ref_size,gap=24,x_start=None):
    total=row_width(d,tokens,gap)
    x=x_start if x_start is not None else (W-total)//2
    cy=int(y+ref_size*0.36)
    for t in tokens:
        w=_tw(d,t); k=t[0]
        if k=="t": d.text((x,y),t[1],font=t[2],fill=t[3])
        elif k=="ar": d_arrow_r(d,x,cy,w,t[2])
        elif k=="ad": d_arrow_d(d,x,cy,w,t[2])
        elif k=="ck": d_check(d,x,cy,w,t[2])
        elif k=="cx": d_cross(d,x,cy,w,t[2])
        x+=w+gap
    return total

def panel_row(d,y,tokens,ref_size,gap=24,pad=40,h=None):
    w=row_width(d,tokens,gap); bw=w+2*pad; bx=(W-bw)//2
    bh=h or (ref_size+2*pad)
    d.rounded_rectangle((bx,y,bx+bw,y+bh),radius=16,fill=PANEL,outline=BORDER,width=2)
    draw_row(d, y+(bh-ref_size)//2-4, tokens, ref_size, gap, x_start=bx+pad)

# ---------- per-scene stage painters ----------
def stage_cold(d, top, bot):
    f=f_bold(150)
    parts=[("$40",YELLOW),("  ·  ",DIM),("85 MIN",TXT),("  ·  ",DIM),("0 CLIPS",RED)]
    tot=sum(measure(d,t,f)[0] for t,_ in parts); x=(W-tot)//2; y=top+60
    for t,c in parts:
        d.text((x,y),t,font=f,fill=c); x+=measure(d,t,f)[0]
    hcenter(d,"twelve GPUs · one bug · nothing saved", f_light(40), y+200, DIM)

def stage_setup(d, top, bot):
    hcenter(d,"The job", f_bold(64), top+30, TXT)
    panel_row(d, top+150, [("t","12 images",f_bold(76),ACCENT),("ar",70,ACCENT),
                           ("t","12 clips",f_bold(76),ACCENT)], 76)
    panel_line(d, top+350, "12x A100-80GB   ·   $2.50 / GPU-hr   ·   in parallel", TXT, 48, mono=True)
    hcenter(d,"parallel = fast.  also = you can waste money 12 ways at once.",
            f_light(36), bot-70, DIM)

def panel_line(d, y, text, color, size, mono=False, h=None):
    font = f_mono(size) if mono else f_bold(size)
    w,_=measure(d,text,font); pad=40; bw=w+2*pad; bx=(W-bw)//2
    bh = h or (size+2*pad); 
    d.rounded_rectangle((bx,y,bx+bw,y+bh), radius=16, fill=PANEL, outline=BORDER, width=2)
    d.text((bx+pad, y+(bh-size)//2-4), text, font=font, fill=color)

def stage_cliff(d, top, bot):
    hcenter(d,"40 / 40 steps", f_bold(96), top+20, GREEN)
    draw_row(d, top+150, [("ck",44,GREEN),("t","the expensive part finished",f_light(40),DIM)], 44)
    d_arrow_d(d, W//2-26, top+250, 52, DIM)
    hcenter(d,"CUDA out of memory", f_bold(96), top+300, RED)
    msg="Tried to allocate 1.32 GiB · 79.25 GiB total · only 1.06 GiB free"
    f=f_mono(30); w,_=measure(d,msg,f); pad=30; bx=(W-(w+2*pad))//2; y=top+440
    d.rounded_rectangle((bx,y,bx+w+2*pad,y+74), radius=12, fill=PANEL2, outline=BORDER, width=2)
    d.text((bx+pad,y+20),msg,font=f,fill=YELLOW)

def stage_cascade(d, top, bot):
    draw_row(d, top+20, [("t","1 OOM",f_bold(78),RED),("ar",70,RED),
                         ("t","cancel × 11",f_bold(78),RED),("ar",70,RED),
                         ("t","0 saved",f_bold(78),RED)], 78, gap=28)
    n=12; sq=88; gap=22; tot=n*sq+(n-1)*gap; x0=(W-tot)//2; y=top+200
    for i in range(n):
        x=x0+i*(sq+gap)
        col=RED if i==6 else PANEL; oc=RED if i==6 else GREEN
        d.rounded_rectangle((x,y,x+sq,y+sq), radius=14, fill=col, outline=oc, width=4)
        if i==6: d_cross(d, x+sq*0.28, y+sq*0.5, sq*0.44, "#ffffff")
        else:    d_check(d, x+sq*0.28, y+sq*0.5, sq*0.44, GREEN)
    hcenter(d,"one clip's failure killed eleven that were seconds from done",
            f_light(38), y+150, DIM)

def stage_foolish(d, top, bot):
    hcenter(d,"This wasn't bad luck.", f_light(56), top+40, DIM)
    hcenter(d,"I scaled before I validated.", f_bold(92), top+140, TXT)
    hcenter(d,"I sent 12 jobs to find a bug that 1 job would have caught.",
            f_reg(44), top+300, YELLOW)

def stage_fix(d, top, bot):
    hcenter(d,"The fix: 4 lines", f_bold(64), top+10, TXT)
    code=[("  pipe.to(\"cuda\")", DIM),
          ("+ pipe.vae.enable_tiling()", GREEN),
          ("+ pipe.vae.enable_slicing()", GREEN),
          ("",DIM),
          ("- starmap(args)", RED),
          ("+ starmap(args, return_exceptions=True)", GREEN)]
    f=f_mono(40); lh=58
    bw=W-520; bx=260; by=top+130; bh=len(code)*lh+60
    d.rounded_rectangle((bx,by,bx+bw,by+bh), radius=16, fill=PANEL2, outline=BORDER, width=2)
    y=by+30
    for t,c in code:
        d.text((bx+40,y),t,font=f,fill=c); y+=lh
    draw_row(d, by+bh+24, [("t","same bug",f_reg(40),GREEN),("ar",46,GREEN),
                           ("t","$3 of damage instead of $40",f_reg(40),GREEN)], 40)

def stage_guards(d, top, bot):
    hcenter(d,"6 guardrails", f_bold(70), top, TXT)
    items=[("1","Canary before you fan out — test one unit end-to-end first"),
           ("2","Find the peak-memory moment — for video it's the decode, at the end"),
           ("3","Isolate failures — one death must never cancel the swarm"),
           ("4","Save incrementally — make re-runs resumable"),
           ("5","Do the cost math out loud — before you hit enter"),
           ("6","Pay the cold-start tax once — cache big models in a Volume")]
    y=top+130; x=200; lh=92
    for num,txt in items:
        d.ellipse((x,y,x+56,y+56), fill=ACCENT)
        nw,_=measure(d,num,f_bold(34)); d.text((x+(56-nw)//2,y+8),num,font=f_bold(34),fill="#06101f")
        d.text((x+86,y+4), txt, font=f_reg(40), fill=TXT)
        y+=lh

def stage_outro(d, top, bot):
    hcenter(d,"Remember one thing:", f_light(48), top+30, DIM)
    lines=["The cheapest place to find a bug","is a $2 canary, not a $40 swarm."]
    y=top+120
    for ln in lines:
        hcenter(d, ln, f_bold(78), y, TXT); y+=100
    hcenter(d,"Test the last mile first.", f_reg(48), y+20, ACCENT)
    draw_row(d, y+120, [("t","full write-up",f_mono(34),GREEN),("ar",40,GREEN),
                        ("t","amitpandeytiktok.github.io/the-40-dollar-gpu-bug",f_mono(34),GREEN)], 34, gap=18)

SCENES=[
 ("cold", stage_cold,
  "I just set forty dollars on fire. In eighty-five minutes. On one bug. Twelve GPUs, a fourteen-billion-parameter video model, and at the end of it, zero clips. Let me show you exactly how, so it never happens to you."),
 ("setup", stage_setup,
  "Here's the job. I'm rendering an AI music video: twelve still images turned into twelve animated clips. To make it fast, I fanned the work across twelve A100 GPUs in parallel, one clip each. Parallel means fast. It also means you can waste money twelve ways at once."),
 ("cliff", stage_cliff,
  "Every clip ran its full forty steps. The expensive part, done. And then on the very last operation, turning the finished math into pixels, every GPU ran out of memory. Not during the hard part. At the finish line. Because a video decoder unpacks all eighty-one frames at once."),
 ("cascade", stage_cascade,
  "And here's what turned annoying into expensive. My batch was set to fail-fast. So the instant one clip crashed, the system cancelled the other eleven, clips that were seconds from finishing. Eighty-five minutes of compute, nothing saved. The bill? About forty dollars, for nothing."),
 ("foolish", stage_foolish,
  "I want to be honest. This wasn't bad luck. Bad luck is a GPU dying. This was me scaling up before testing a single unit. I sent twelve jobs to find a bug that one job would have caught. And I skipped the test because the code looked done."),
 ("fix", stage_fix,
  "The fix is almost insultingly small. Two lines so the decoder works in tiles and never spikes the memory. And one keyword, return exceptions, so a single failure saves the survivors instead of nuking the whole batch. Same bug, now three dollars of damage instead of forty."),
 ("guards", stage_guards,
  "So here are six rules I'm burning into my brain. One, canary before you fan out. Two, find the peak-memory moment; for video models it's the decode, at the end. Three, isolate failures. Four, save results as they land. Five, do the cost math out loud. Six, cache your big models once."),
 ("outro", stage_outro,
  "If you remember one thing, make it this. The cheapest place to find a bug is a two-dollar canary, not a forty-dollar swarm. Test the last mile first. I wrote the whole thing up, link in the description. Mistakes are a lot cheaper when you publish them."),
]

def render_slides():
    total=len(SCENES); paths=[]
    for i,(name,painter,vo) in enumerate(SCENES, start=1):
        img,d=base()
        cap_top=caption(d, vo)
        painter(d, 150, cap_top)             # stage between header and caption
        footer(d,i,total)
        p=os.path.join(BUILD,f"slide_{i:02d}_{name}.png"); img.save(p); paths.append((p,vo,name))
    return paths

def tts(text, out_aiff):
    subprocess.run(["say","-v","Daniel","-o",out_aiff,"--file-format=AIFF",text], check=True)

def dur(path):
    r=subprocess.run([FFPROBE,"-v","quiet","-show_entries","format=duration",
                      "-of","csv=p=0",path],capture_output=True,text=True)
    return float(r.stdout.strip())

def make_segment(png, aiff, out_mp4, tail=0.6):
    t=dur(aiff)+tail
    subprocess.run([FFMPEG,"-y","-loop","1","-framerate","30","-i",png,"-i",aiff,
        "-af",f"apad=pad_dur={tail}","-t",f"{t:.3f}",
        "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-r","30",
        "-c:a","aac","-b:a","192k","-ar","48000",out_mp4],
        check=True, capture_output=True)
    return t

def thumbnail():
    img=Image.new("RGB",(1280,720),BG); d=ImageDraw.Draw(img)
    d.rectangle((0,0,1280,12),fill=ORANGE)
    d.text((70,80),"GPU RENDER",font=f_reg(48),fill=DIM)
    d.text((70,140),"POST-MORTEM",font=f_bold(64),fill=TXT)
    big=ImageFont.truetype(HEL,300,index=1)
    d.text((60,250),"$40",font=big,fill=YELLOW)
    d.text((70,580),"85 MINUTES · 0 CLIPS SAVED",font=f_bold(50),fill=RED)
    # right side: 12 squares one red
    x0=860;y0=250;sq=64;gap=16
    for r in range(3):
        for c in range(4):
            i=r*4+c; x=x0+c*(sq+gap); y=y0+r*(sq+gap)
            col=RED if i==6 else PANEL; oc=RED if i==6 else GREEN
            d.rounded_rectangle((x,y,x+sq,y+sq),radius=10,fill=col,outline=oc,width=4)
    p=os.path.join(HERE,"thumbnail.png"); img.save(p); return p

def main():
    print("rendering slides…"); slides=render_slides()
    segs=[]; total=0.0
    for i,(png,vo,name) in enumerate(slides, start=1):
        aiff=os.path.join(BUILD,f"vo_{i:02d}.aiff"); tts(vo,aiff)
        seg=os.path.join(BUILD,f"seg_{i:02d}.mp4"); t=make_segment(png,aiff,seg)
        total+=t; segs.append(seg); print(f"  scene {i} {name}: {t:.1f}s")
    listf=os.path.join(BUILD,"concat.txt")
    with open(listf,"w") as fh:
        for s in segs: fh.write(f"file '{s}'\n")
    out=os.path.join(HERE,"the-40-dollar-gpu-bug.mp4")
    subprocess.run([FFMPEG,"-y","-f","concat","-safe","0","-i",listf,"-c","copy",out],
                   check=True, capture_output=True)
    thumb=thumbnail()
    m,s=divmod(round(total),60)
    print(f"\nDONE  {out}\n  runtime ~{m}:{s:02d}  ({total:.1f}s)\n  thumbnail {thumb}")

if __name__=="__main__":
    main()
