"""Motor de narración multivoz. Requiere OPENAI_API_KEY y ffmpeg."""
from __future__ import annotations
import hashlib, json, os, re, time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable
from pydub import AudioSegment
from openai import OpenAI

VOICES = {"JASON":"onyx", "SKARD":"echo", "BLAKE":"ash", "RYAN":"fable", "SARAH":"nova", "LLAMADA":"alloy", "JASON EN CINTA":"onyx"}
VOICE_RE = re.compile(r'^\[VOZ:\s*([^|\]]+?)(?:\s*\|\s*ACTUACI[ÓO]N:\s*([^\]]+))?\]$', re.I)
PAUSE_RE = re.compile(r'^\[PAUSA:\s*([\d.]+)\s*s\]$', re.I)
FX_RE = re.compile(r'^\[(SFX|MÚSICA|MUSICA):\s*(.*?)\]$', re.I)
CHAPTER_RE = re.compile(r'^#\s+(CAP[ÍI]TULO\s+\d+.*|EP[ÍI]LOGO.*)$', re.I)

@dataclass
class Part:
    kind: str
    text: str = ""
    voice: str = "JASON"
    acting: str = ""
    seconds: float = 0
    chapter: str = ""

def parse_script(raw: str) -> list[Part]:
    """Analiza guiones con [VOZ], [PAUSA], [SFX], [MÚSICA] y capítulos.
    No convierte automáticamente citas dentro de párrafos a otras voces.
    """
    result=[]; voice="JASON"; acting="narración de terror"; chapter=""; buffer=[]; started=False
    def flush():
        if buffer:
            t=" ".join(buffer).strip()
            if t: result.append(Part("speech",t,voice,acting,chapter=chapter))
            buffer.clear()
    for line in raw.splitlines():
        line=line.strip()
        if not line:
            flush(); continue
        ch=CHAPTER_RE.match(line)
        if ch:
            flush(); chapter=ch.group(1); started=True
            if "EPÍLOGO" in chapter.upper() or "EPILOGO" in chapter.upper(): voice="BLAKE"
            continue
        if not started: continue  # omitir cabeceras y convenciones
        vm=VOICE_RE.match(line)
        if vm:
            flush(); voice=vm.group(1).strip().upper(); acting=(vm.group(2) or "narración de terror").strip(); continue
        pm=PAUSE_RE.match(line)
        if pm:
            flush(); result.append(Part("pause",seconds=min(30,max(0,float(pm.group(1)))),chapter=chapter)); continue
        fx=FX_RE.match(line)
        if fx:
            flush(); result.append(Part("effect",text=fx.group(2),voice=fx.group(1).upper(),chapter=chapter)); continue
        if line.startswith("#") or line=="---":
            flush(); continue
        if line.startswith("[") and line.endswith("]"):
            flush(); continue
        buffer.append(re.sub(r'\*([^*]+)\*',r'\1',line))
    flush()
    return result

def split_text(text: str, max_chars: int=1900) -> list[str]:
    if len(text)<=max_chars: return [text]
    sentences=re.split(r'(?<=[.!?…])\s+',text)
    out=[]; current=""
    for sentence in sentences:
        while len(sentence)>max_chars:
            if current: out.append(current); current=""
            cut=sentence.rfind(" ",0,max_chars)
            if cut<max_chars//3: cut=max_chars
            out.append(sentence[:cut].strip()); sentence=sentence[cut:].strip()
        if not sentence: continue
        if len(current)+len(sentence)+1>max_chars:
            if current: out.append(current)
            current=sentence
        else: current=(current+" "+sentence).strip()
    if current: out.append(current)
    return out

def generate(script: str, output_dir: str, config: dict, *, dry_run=False, limit: int|None=None, progress: Callable|None=None):
    parts=parse_script(script)
    if limit is not None: parts=parts[:limit]
    dest=Path(output_dir); dest.mkdir(parents=True,exist_ok=True)
    cache=dest/"cache"; cache.mkdir(exist_ok=True)
    (dest/"plan.json").write_text(json.dumps([asdict(p) for p in parts],ensure_ascii=False,indent=2),encoding="utf-8")
    if dry_run: return {"segments":len(parts),"spoken":sum(p.kind=="speech" for p in parts),"plan":str(dest/"plan.json")}
    if not os.getenv("OPENAI_API_KEY"): raise RuntimeError("Falta OPENAI_API_KEY. Configúrala en .env o como variable de entorno.")
    client=OpenAI()
    model=config.get("model","gpt-4o-mini-tts")
    voices={**VOICES,**config.get("voices",{})}
    speed=float(config.get("speed",1.0))
    gap=int(config.get("gap_ms",450))
    audio=AudioSegment.silent(duration=300)
    log=[]; spoken=0
    for i,part in enumerate(parts,1):
        if progress: progress(i,len(parts),part)
        if part.kind=="pause":
            audio+=AudioSegment.silent(duration=round(part.seconds*1000)); continue
        if part.kind=="effect":
            # Opcional: archivo assets/efecto_N.mp3 o assets/efecto_N.wav, indexado por posición
            effects=config.get("effects",{})
            asset=effects.get(str(i))
            if asset and Path(asset).is_file():
                audio+=AudioSegment.from_file(asset)
            log.append({"index":i,"effect_instruction":part.text,"file":asset or None})
            continue
        for j,chunk in enumerate(split_text(part.text),1):
            selected=voices.get(part.voice,voices["JASON"])
            instructions=f"Habla en español latinoamericano, como narración de terror realista. Personaje: {part.voice}. Interpretación: {part.acting}. No leas instrucciones ni agregues palabras."
            signature=json.dumps([model,selected,speed,instructions,chunk],ensure_ascii=False)
            name=hashlib.sha256(signature.encode()).hexdigest()[:24]
            file=cache/f"{name}.mp3"
            if not file.exists():
                for attempt in range(3):
                    try:
                        with client.audio.speech.with_streaming_response.create(model=model,voice=selected,input=chunk,instructions=instructions,speed=speed,response_format="mp3") as response:
                            response.stream_to_file(file)
                        break
                    except Exception:
                        file.unlink(missing_ok=True)
                        if attempt==2: raise
                        time.sleep(2**attempt)
            segment=AudioSegment.from_file(file)
            if part.voice=="JASON EN CINTA":
                segment=segment.high_pass_filter(280).low_pass_filter(3200)-3
            audio+=segment+AudioSegment.silent(duration=gap)
            spoken+=1
            log.append({"index":i,"chunk":j,"voice":part.voice,"tts_voice":selected,"file":str(file),"text":chunk})
    target=dest/"historia_completa.mp3"
    audio.export(target,format="mp3",bitrate=config.get("bitrate","192k"),tags={"title":"Las 7 reglas del turno nocturno","artist":"Producción de voz sintética"})
    (dest/"manifest.json").write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding="utf-8")
    return {"mp3":str(target),"duration_seconds":round(len(audio)/1000,1),"chunks":spoken,"segments":len(parts)}
