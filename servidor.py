"""Aplicação local da disciplina: CRUD completo, consultas e configuração de banco."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs
from datetime import date,datetime
from decimal import Decimal
from pathlib import Path
import argparse,json,logging,secrets,threading,os,hashlib
from config import ROOT,LOCAL
import banco,graficos,importar,ia

TOKEN=secrets.token_urlsafe(32)
MUTATION_LOCK=threading.RLock()

def encode(obj):
 if isinstance(obj,(datetime,date)):return obj.isoformat()
 if isinstance(obj,Decimal):return str(obj)
 raise TypeError(type(obj).__name__)

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def allowed(self):
  host=self.headers.get('Host','');allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
  return host in allowed and self.headers.get('Origin') in (None,*['http://'+h for h in allowed])
 def send(self,status,data,ctype='application/json; charset=utf-8'):
  if isinstance(data,(dict,list)):data=json.dumps(data,default=encode,ensure_ascii=False).encode('utf-8')
  elif isinstance(data,str):data=data.encode('utf-8')
  self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'");self.end_headers()
  try:self.wfile.write(data)
  except (BrokenPipeError,ConnectionResetError):pass
 def do_GET(self):
  if not self.allowed():return self.send(403,{'error':'Origem não permitida.'})
  path=urlsplit(self.path).path;q=parse_qs(urlsplit(self.path).query)
  try:
   if path in ('/','/app.js','/style.css'):
    file='index.html' if path=='/' else path[1:];ctype={'index.html':'text/html; charset=utf-8','app.js':'text/javascript; charset=utf-8','style.css':'text/css; charset=utf-8'}[file]
    return self.send(200,(ROOT/'static'/file).read_bytes(),ctype)
   if path=='/favicon.ico':return self.send(204,b'','image/x-icon')
   if path=='/api/identity':return self.send(200,{'app':'dec7588_audiovisual','instance':hashlib.sha256(str(ROOT).encode()).hexdigest()})
   if path=='/api/meta':return self.send(200,{'tables':banco.metadata(),'csrf':TOKEN,'database':'PostgreSQL · audiovisual_dec7588'})
   if path=='/api/list':return self.send(200,banco.list_rows(q.get('table',['obra'])[0],q.get('search',[''])[0],q.get('page',[1])[0]))
   if path=='/api/choices':return self.send(200,banco.choices(q.get('table',['obra'])[0]))
   if path=='/api/report':
    r=banco.report(q.get('index',[0])[0]);r['svg']=graficos.svg(r['rows'],r['titulo']);return self.send(200,r)
   if path=='/api/manifest':return self.send(200,json.loads((ROOT/'data/manifesto.json').read_text(encoding='utf-8')))
   if path=='/api/ai-record':return self.send(200,ia.payload_record(q.get('id',[''])[0]))
   if path=='/api/ai-config':return self.send(200,ia.public_configuration())
   if path=='/api/export-ddl':return self.send(200,(ROOT/'sql/01_schema.sql').read_bytes(),'text/plain; charset=utf-8')
   if path=='/api/sql-rapido':return self.send(200,{'sql':(ROOT/'CONSULTAS_PGADMIN.sql').read_text(encoding='utf-8')})
   if path=='/api/export-sql-rapido':return self.send(200,(ROOT/'CONSULTAS_PGADMIN.sql').read_bytes(),'text/plain; charset=utf-8')
   return self.send(404,{'error':'Recurso não encontrado.'})
  except Exception as exc:return self.send(400,{'error':banco.public_error(exc)})
 def do_POST(self):
  if not self.allowed() or not secrets.compare_digest(self.headers.get('X-CSRF-Token',''),TOKEN):return self.send(403,{'error':'Reabra a página para renovar a sessão.'})
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<=2_000_000:raise ValueError('Solicitação vazia ou muito extensa.')
   body=json.loads(self.rfile.read(length));path=urlsplit(self.path).path
   with MUTATION_LOCK:
    if path=='/api/save':result=banco.save_row(body['table'],body['values'],body.get('id'))
    elif path=='/api/delete':result=banco.delete_row(body['table'],body['id'])
    elif path=='/api/init':banco.initialize();result={'message':'Tabelas criadas. Você já pode importar os dados.'}
    elif path=='/api/seed':result=importar.seed()
    elif path=='/api/drop':banco.drop_schema(body.get('confirmation'));result={'message':'Tabelas e dados apagados.'}
    elif path=='/api/ai':result=ia.compare(body['a'],body['b'],body['provider'],body['model'],body.get('key',''))
    else:return self.send(404,{'error':'Operação desconhecida.'})
   return self.send(200,result)
  except Exception as exc:
   # Nunca registrar corpo da requisição: pode conter chave de API.
   logging.error('Falha em %s: %s',urlsplit(self.path).path,type(exc).__name__)
   return self.send(400,{'error':banco.public_error(exc)})

def serve(port=8768):
 LOCAL.mkdir(exist_ok=True);logging.basicConfig(filename=LOCAL/'aplicacao.log',level=logging.INFO)
 server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.daemon_threads=True
 (LOCAL/'servidor.pid').write_text(str(os.getpid()),encoding='ascii')
 print(f'Aplicação da disciplina: http://127.0.0.1:{server.server_port}/',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8768);args=p.parse_args();serve(args.port)

