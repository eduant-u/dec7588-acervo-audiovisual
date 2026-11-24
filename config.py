"""Configuração local privada; nenhuma senha entra no pacote de entrega."""
from pathlib import Path
import json,sys

ROOT=Path(__file__).resolve().parent
LOCAL=ROOT/'.local'
for path in [ROOT.parent/'.runtime/deps', LOCAL/'deps']:
 if path.is_dir():sys.path.insert(0,str(path))

def settings():
 path=LOCAL/'config.json'
 if not path.is_file():raise RuntimeError('Execute INICIAR_TRABALHO.cmd para preparar o PostgreSQL local.')
 return json.loads(path.read_text(encoding='utf-8'))

