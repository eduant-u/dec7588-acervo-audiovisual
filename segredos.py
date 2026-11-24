"""Leitura local de credenciais; biblioteca padrão, sem conexão com o banco."""
from config import ROOT
import os,re

def local_settings():
 values={}
 for filename in ['.env','.env.txt']:
  path=ROOT/filename
  if not path.is_file():continue
  for line in path.read_text(encoding='utf-8-sig').splitlines():
   line=line.strip()
   if not line or line.startswith('#'):continue
   if line.startswith('export '):line=line[7:].strip()
   if '=' in line:
    name,value=line.split('=',1);values[name.strip()]=value.strip().strip('"').strip("'")
   elif line.startswith('AIza'):values['GEMINI_API_KEY']=line
   elif line.startswith('sk-'):values['OPENAI_API_KEY']=line
   elif re.fullmatch(r'[A-Za-z0-9_.-]{20,}',line):values.setdefault('GEMINI_API_KEY',line)
 for name in ['GEMINI_API_KEY','GOOGLE_API_KEY','OPENAI_API_KEY','GEMINI_MODEL','OPENAI_MODEL']:
  if os.environ.get(name):values[name]=os.environ[name]
 return values

def configured_key(provider):
 values=local_settings()
 if provider=='gemini':return values.get('GEMINI_API_KEY') or values.get('GOOGLE_API_KEY') or ''
 if provider=='openai':return values.get('OPENAI_API_KEY') or ''
 return ''

def public_configuration():
 values=local_settings()
 return {'gemini':{'configured':bool(configured_key('gemini')),'model':values.get('GEMINI_MODEL','gemini-3.5-flash-lite')},'openai':{'configured':bool(configured_key('openai')),'model':values.get('OPENAI_MODEL','')},'ollama':{'configured':False,'model':''}}

