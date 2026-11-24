"""Instância PostgreSQL exclusiva em loopback, autenticada por SCRAM; não altera o serviço existente."""
from pathlib import Path
import json,os,secrets,socket,subprocess,sys,shutil
from config import ROOT,LOCAL

def binaries():
 explicit=os.environ.get('PG_BIN')
 choices=[Path(explicit)] if explicit else []
 base=Path(os.environ.get('ProgramFiles',r'C:\Program Files'))/'PostgreSQL'
 if base.is_dir():choices+=sorted(base.glob('*/bin'),key=lambda p:int(p.parent.name.split('.')[0]),reverse=True)
 for p in choices:
  if (p/'initdb.exe').is_file():return p
 raise RuntimeError('PostgreSQL não localizado. Informe PG_BIN com a pasta bin de sua instalação.')

def run(args,logname,env=None):
 with (LOCAL/logname).open('w',encoding='utf-8') as log:
  r=subprocess.run([str(x) for x in args],stdout=log,stderr=subprocess.STDOUT,env=env,timeout=60)
 if r.returncode:raise RuntimeError('Falha na preparação; consulte .local/'+logname)

def prepare():
 LOCAL.mkdir(exist_ok=True)
 try:import psycopg
 except ImportError:
  subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check','--target',str(LOCAL/'deps'),'-r',str(ROOT/'requirements.txt')],check=True)
  sys.path.insert(0,str(LOCAL/'deps'));import psycopg
 from psycopg import sql
 binpath=binaries();cfgpath=LOCAL/'config.json';data=LOCAL/'pgdata'
 if cfgpath.is_file():cfg=json.loads(cfgpath.read_text(encoding='utf-8'))
 else:
  port=None
  for candidate in range(55432,55460):
   with socket.socket() as s:
    try:s.bind(('127.0.0.1',candidate));port=candidate;break
    except OSError:continue
  if port is None:raise RuntimeError('Nenhuma porta local disponível para o banco do trabalho.')
  cfg={'host':'127.0.0.1','port':port,'user':'audiovisual_local','password':secrets.token_urlsafe(32),'dbname':'audiovisual_dec7588','schema':'audiovisual'}
  cfgpath.write_text(json.dumps(cfg,indent=2),encoding='utf-8')
 if cfg['dbname']!='audiovisual_dec7588' or cfg['schema']!='audiovisual':raise RuntimeError('Configuração não pertence ao banco exclusivo da disciplina.')
 if not (data/'PG_VERSION').exists():
  pw=LOCAL/'init-password.tmp'
  try:
   pw.write_text(cfg['password']+'\n',encoding='utf-8')
   run([binpath/'initdb.exe','-D',data,'-U',cfg['user'],'--pwfile',pw,'--auth-host=scram-sha-256','--auth-local=scram-sha-256','--encoding=UTF8','--locale=C'],'initdb.log')
  finally:pw.unlink(missing_ok=True)
 status=subprocess.run([str(binpath/'pg_ctl.exe'),'-D',str(data),'status'],capture_output=True)
 if status.returncode:
  run([binpath/'pg_ctl.exe','-D',data,'-l',LOCAL/'postgresql.log','-o',f'-h 127.0.0.1 -p {cfg["port"]}','-w','-t','30','start'],'pg-start.log')
 admin={k:v for k,v in cfg.items() if k!='schema'};admin['dbname']='postgres';admin['connect_timeout']=5
 with psycopg.connect(**admin,autocommit=True) as c:
  if not c.execute('SELECT 1 FROM pg_database WHERE datname=%s',(cfg['dbname'],)).fetchone():
   c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(cfg['dbname'])))
 print(f'PostgreSQL exclusivo disponível em 127.0.0.1:{cfg["port"]}; banco {cfg["dbname"]}.')
 return cfg

if __name__=='__main__':prepare()

