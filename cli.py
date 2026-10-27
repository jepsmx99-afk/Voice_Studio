import argparse,json
from pathlib import Path
from dotenv import load_dotenv
from engine import generate
load_dotenv()
p=argparse.ArgumentParser(description="Genera narración MP3 multivoz")
p.add_argument("script",type=Path)
p.add_argument("--output",default="salida")
p.add_argument("--dry-run",action="store_true")
p.add_argument("--limit",type=int)
p.add_argument("--config",type=Path,default=Path(__file__).parent/"config.json")
a=p.parse_args()
config=json.loads(a.config.read_text(encoding="utf-8"))
result=generate(a.script.read_text(encoding="utf-8-sig"),a.output,config,dry_run=a.dry_run,limit=a.limit,progress=lambda i,n,p:print(f"{i}/{n} {p.kind} {p.voice}",flush=True))
print(json.dumps(result,ensure_ascii=False,indent=2))
