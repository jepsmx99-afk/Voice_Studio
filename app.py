from pathlib import Path
import json, os
import streamlit as st
from dotenv import load_dotenv
from engine import generate,parse_script,VOICES
load_dotenv()
st.set_page_config(page_title="Terror Voice Studio",page_icon="🎙️",layout="wide")
st.title("🎙️ Terror Voice Studio")
st.caption("Guiones de terror → voces por personaje → MP3. El audio es generado por IA.")
root=Path(__file__).parent
uploaded=st.file_uploader("Sube un guion .md o .txt",type=["md","txt"])
default=root/"guion_ejemplo.md"
script=uploaded.getvalue().decode("utf-8-sig") if uploaded else (default.read_text(encoding="utf-8") if default.exists() else "")
with st.expander("Editar guion",expanded=False): script=st.text_area("Guion",value=script,height=300)
parts=parse_script(script)
st.write(f"**{len(parts)} segmentos** · **{sum(p.kind=='speech' for p in parts)} segmentos de voz**")
with st.expander("Vista previa del análisis"):
    st.dataframe([{"tipo":p.kind,"voz":p.voice,"capítulo":p.chapter,"contenido":p.text[:130],"pausa_s":p.seconds} for p in parts[:100]],use_container_width=True)
with st.sidebar:
    st.header("Configuración")
    st.info("La API se factura por separado. Configura OPENAI_API_KEY en el archivo .env; no incluyas la clave en el guion.")
    model=st.selectbox("Modelo",["gpt-4o-mini-tts","tts-1","tts-1-hd"])
    speed=st.slider("Velocidad",0.75,1.25,1.0,0.05)
    gap=st.slider("Pausa entre segmentos (ms)",0,1500,450,50)
    choices=["alloy","ash","ballad","coral","echo","fable","nova","onyx","sage","shimmer","verse"]
    voices={name:st.selectbox(name,choices,index=choices.index(v) if v in choices else 0) for name,v in VOICES.items()}
    limit=st.number_input("Limitar segmentos (0 = todos)",0,10000,0)
    dry=st.checkbox("Solo validar (sin consumir API)",value=True)
    output=st.text_input("Carpeta de salida",value=str(root/"salida"))
if model!="gpt-4o-mini-tts": st.warning("Los modelos tts-1 y tts-1-hd pueden no admitir instrucciones expresivas. Usa gpt-4o-mini-tts para interpretar emociones.")
if st.button("Generar audio",type="primary",disabled=not bool(parts)):
    bar=st.progress(0,text="Preparando")
    def update(i,total,part): bar.progress(i/total,text=f"Procesando {i}/{total}: {part.voice}")
    try:
        result=generate(script,output,{"model":model,"voices":voices,"speed":speed,"gap_ms":gap},dry_run=dry,limit=limit or None,progress=update)
        st.success("Validación completada" if dry else "Audio generado")
        st.json(result)
        if not dry:
            path=Path(result["mp3"])
            st.audio(path.read_bytes(),format="audio/mp3")
            st.download_button("Descargar MP3",path.read_bytes(),file_name=path.name,mime="audio/mpeg")
    except Exception as e: st.error(f"No se pudo completar: {e}")
