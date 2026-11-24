"""Prepara banco exclusivo e abre a aplicação; não depende do Drive após a extração."""
import argparse,threading,webbrowser,urllib.request,urllib.error,json,hashlib
from preparar_banco import prepare
from config import ROOT

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-browser',action='store_true');p.add_argument('--port',type=int,default=8768);args=p.parse_args()
 prepare()
 url=f'http://127.0.0.1:{args.port}/'
 try:
  with urllib.request.urlopen(url+'api/identity',timeout=2) as response:identity=json.load(response)
 except (urllib.error.URLError,TimeoutError,ValueError):identity=None
 if identity:
  if identity.get('app')!='dec7588_audiovisual' or identity.get('instance')!=hashlib.sha256(str(ROOT).encode()).hexdigest():raise RuntimeError('A porta já pertence a outra aplicação. Use --port 8770.')
  print('Aplicação já está disponível: '+url)
  if not args.no_browser:webbrowser.open(url)
  return
 import banco
 banco.initialize()
 with banco.connect() as c:empty=c.execute('SELECT COUNT(*) AS n FROM obra').fetchone()['n']==0
 if empty:
  from importar import seed
  result=seed();print('Amostra carregada:',result['tabelas']['registro_fonte'],'registros.')
 if not args.no_browser:threading.Timer(1.0,lambda:webbrowser.open(url)).start()
 from servidor import serve
 serve(args.port)

if __name__=='__main__':main()

