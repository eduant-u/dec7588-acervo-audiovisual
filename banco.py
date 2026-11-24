"""Acesso PostgreSQL, CRUD parametrizado e consultas analíticas."""
from config import ROOT,settings
import json,re
from decimal import Decimal
import psycopg
from psycopg import sql
from psycopg.rows import dict_row

TABLES={
 'fonte_dados':'Fontes de dados','lote_importacao':'Lotes de importação',
 'tipo_obra':'Tipos de obra','obra':'Obras audiovisuais','registro_fonte':'Registros das fontes',
 'titulo':'Títulos','certificado':'Certificados','pessoa':'Pessoas','empresa':'Empresas',
 'funcao_credito':'Funções de crédito','credito_pessoa':'Créditos de pessoas',
 'participacao_empresa':'Participações de empresas','pais':'Países','obra_pais':'Países de produção',
 'genero':'Gêneros','obra_genero':'Gêneros por registro',
 'caracteristica_tecnica':'Características técnicas','relacao_obra':'Relações entre obras',
 'decisao_integracao':'Decisões de integração'
}
LABELS={'obra':'titulo_referencia','registro_fonte':'chave_origem','lote_importacao':'nome','titulo':'valor','certificado':'numero','caracteristica_tecnica':'nome','relacao_obra':'tipo','decisao_integracao':'parecer'}
ENUMS={'obra.nivel':['obra','serie','episodio','temporada','nao_especificado'],
 'titulo.tipo':['declarado','alternativo','chave_normalizada'],
 'decisao_integracao.parecer':['mesma_obra','obras_distintas','incerto','episodio_da_serie']}
QUERY_TEXT=(ROOT/'sql/02_consultas.sql').read_text(encoding='utf-8')
QUERIES=[s.strip() for s in QUERY_TEXT.split(';') if s.strip()]
# SQL contém comentários com ponto e vírgula? Use sentinelas de SELECT, mantendo só uma instrução por consulta.
QUERIES=re.findall(r'(SELECT\s+.*?;)',QUERY_TEXT,re.S|re.I)
REPORTS=[
 {'titulo':'Obras por década e fonte','objetivo':'Contar as obras descritas por cada fonte em cada década. Uma obra nas duas fontes participa de ambas as séries.','unidade':'obras distintas por fonte e década','nota':'Os números se referem apenas aos registros deste acervo.'},
 {'titulo':'Empresas e papéis declarados','objetivo':'Identificar as empresas com mais obras na amostra, separando o papel de requerente do de produtora.','unidade':'obras distintas por empresa e papel','nota':'Empresas com o mesmo nome podem ser diferentes; os nomes são mantidos por fonte.'},
 {'titulo':'Obras com CPB por fonte e papel','objetivo':'Contar obras com CPB, preservando a distinção entre certificado próprio, da série e do episódio.','unidade':'obras distintas por fonte e papel do CPB','nota':'Uma obra pode participar de mais de uma categoria. As contagens não devem ser somadas como total único.'}
]

def connect():
 cfg=settings();params={k:v for k,v in cfg.items() if k!='schema'}
 c=psycopg.connect(**params,row_factory=dict_row,connect_timeout=5)
 c.execute('SET search_path TO audiovisual, public')
 c.execute("SET statement_timeout TO '15s'")
 return c

def table_name(name):
 if name not in TABLES:raise ValueError('Tabela desconhecida.')
 return sql.Identifier('audiovisual',name)

def initialize():
 with connect() as c:c.execute((ROOT/'sql/01_schema.sql').read_text(encoding='utf-8'))

def drop_schema(confirmation):
 if confirmation!='ELIMINAR TABELAS':raise ValueError('Digite ELIMINAR TABELAS para confirmar.')
 with connect() as c:
  if c.execute('SELECT current_database() AS db').fetchone()['db']!='audiovisual_dec7588':raise ValueError('Operação restrita ao banco da disciplina.')
  c.execute('DROP SCHEMA IF EXISTS audiovisual CASCADE')

def metadata():
 with connect() as c:
  cols=c.execute("""SELECT table_name,column_name,data_type,is_nullable,column_default,is_identity,
   character_maximum_length FROM information_schema.columns
   WHERE table_schema='audiovisual' ORDER BY ordinal_position""").fetchall()
  fks=c.execute("""SELECT tc.table_name,kcu.column_name,ccu.table_name AS target
   FROM information_schema.table_constraints tc
   JOIN information_schema.key_column_usage kcu ON kcu.constraint_name=tc.constraint_name AND kcu.constraint_schema=tc.constraint_schema
   JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name=tc.constraint_name AND ccu.constraint_schema=tc.constraint_schema
   WHERE tc.constraint_schema='audiovisual' AND tc.constraint_type='FOREIGN KEY'""").fetchall()
  targets={(r['table_name'],r['column_name']):r['target'] for r in fks}
  out=[]
  for name,label in TABLES.items():
   fields=[]
   for col in cols:
    if col['table_name']!=name:continue
    field={'name':col['column_name'],'type':col['data_type'],'required':col['is_nullable']=='NO' and col['column_default'] is None and col['is_identity']=='NO','default':col['column_default'],'max_length':col['character_maximum_length']}
    field['target']=targets.get((name,field['name']));field['options']=ENUMS.get(name+'.'+field['name'])
    fields.append(field)
   count=c.execute(sql.SQL('SELECT COUNT(*) AS n FROM {}').format(table_name(name))).fetchone()['n'] if fields else 0
   out.append({'name':name,'label':label,'fields':fields,'count':count})
  return out

def list_rows(name,search='',page=1,limit=25):
 table_name(name);page=max(1,int(page));limit=max(1,min(100,int(limit)))
 fields=next(t['fields'] for t in metadata() if t['name']==name)
 if not fields:raise ValueError('Crie as tabelas na área Banco de dados.')
 searchable=[f['name'] for f in fields if f['type'] not in ('jsonb','timestamp with time zone')]
 where=sql.SQL('');args=[]
 if search:
  where=sql.SQL(' WHERE ')+sql.SQL(' OR ').join(sql.SQL('{}::text ILIKE %s').format(sql.Identifier(k)) for k in searchable)
  args=['%'+str(search).strip()[:240]+'%']*len(searchable)
 with connect() as c:
  total=c.execute(sql.SQL('SELECT COUNT(*) AS n FROM {}').format(table_name(name))+where,args).fetchone()['n']
  rows=c.execute(sql.SQL('SELECT * FROM {}').format(table_name(name))+where+sql.SQL(' ORDER BY id LIMIT %s OFFSET %s'),args+[limit,(page-1)*limit]).fetchall()
 return {'rows':rows,'total':total,'page':page,'limit':limit}

def choices(name):
 label=LABELS.get(name,'nome')
 with connect() as c:
  if name=='registro_fonte':
   return c.execute("SELECT id,id::text||' · '||chave_origem||' · '||left(COALESCE(perfil_json->>'titulo_exibicao','Sem título'),90) AS label FROM registro_fonte ORDER BY id LIMIT 4000").fetchall()
  return c.execute(sql.SQL("SELECT id, id::text||' · '||left({},110) AS label FROM {} ORDER BY id LIMIT 4000").format(sql.Identifier(label),table_name(name))).fetchall()

def clean_values(name,values):
 info=next(t for t in metadata() if t['name']==name)
 fields={f['name']:f for f in info['fields'] if f['name']!='id'}
 if not fields:raise ValueError('Tabela ainda não foi criada.')
 if not isinstance(values,dict) or set(values)-set(fields):raise ValueError('Campos inválidos.')
 result={}
 for key,value in values.items():
  f=fields[key]
  if isinstance(value,str):value=value.strip()
  if value=='':
   if f['default'] is not None:continue
   value=None
  if value is not None:
   if f['type']=='jsonb':
    if isinstance(value,str):value=json.loads(value)
    if not isinstance(value,(dict,list)):raise ValueError('JSON precisa ser objeto ou lista.')
    value=psycopg.types.json.Jsonb(value)
   elif f['type'] in ('bigint','integer'):value=int(value)
   elif f['type']=='numeric':value=Decimal(str(value).replace(',','.'))
  result[key]=value
 return result

def save_row(name,values,row_id=None):
 values=clean_values(name,values)
 if not values:raise ValueError('Preencha ao menos um campo.')
 with connect() as c:
  if row_id is None:
   query=sql.SQL('INSERT INTO {} ({}) VALUES ({}) RETURNING *').format(table_name(name),sql.SQL(',').join(map(sql.Identifier,values)),sql.SQL(',').join(sql.Placeholder() for _ in values))
   row=c.execute(query,list(values.values())).fetchone()
  else:
   query=sql.SQL('UPDATE {} SET {} WHERE id=%s RETURNING *').format(table_name(name),sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in values))
   row=c.execute(query,[*values.values(),int(row_id)]).fetchone()
  if not row:raise ValueError('Registro não encontrado.')
  return row

def delete_row(name,row_id):
 with connect() as c:
  row=c.execute(sql.SQL('DELETE FROM {} WHERE id=%s RETURNING id').format(table_name(name)),(int(row_id),)).fetchone()
  if not row:raise ValueError('Registro não encontrado.')
 return row

def report(index):
 index=int(index)
 if not 0<=index<len(REPORTS):raise ValueError('Consulta desconhecida.')
 with connect() as c:
  rows=c.execute(QUERIES[index]).fetchall()
 return {**REPORTS[index],'sql':QUERIES[index],'rows':rows,'index':index}

def public_error(exc):
 if isinstance(exc,(psycopg.errors.ForeignKeyViolation,psycopg.errors.RestrictViolation)):return 'Há uma referência inválida ou registros dependentes. Cadastre o registro referenciado ou remova primeiro as dependências.'
 if isinstance(exc,psycopg.errors.UniqueViolation):return 'Já existe um registro com essa combinação de valores.'
 if isinstance(exc,psycopg.errors.CheckViolation):return 'O valor não atende às regras do campo. Confira nível da obra, ano, duração, decisão ou autorreferência.'
 if isinstance(exc,psycopg.errors.NotNullViolation):return 'Preencha todos os campos obrigatórios.'
 if isinstance(exc,(psycopg.errors.InvalidTextRepresentation,psycopg.errors.InvalidDatetimeFormat,psycopg.errors.DatetimeFieldOverflow)):return 'Formato inválido. Confira números, datas (AAAA-MM-DD) e JSON.'
 if isinstance(exc,psycopg.errors.StringDataRightTruncation):return 'Um campo ultrapassa o tamanho permitido.'
 if isinstance(exc,psycopg.OperationalError):return 'Não foi possível conectar ao PostgreSQL. Execute INICIAR_TRABALHO.cmd.'
 if isinstance(exc,(ValueError,TypeError,json.JSONDecodeError)):return str(exc)[:300]
 return 'Não foi possível concluir a operação. Confira o log local do servidor.'

