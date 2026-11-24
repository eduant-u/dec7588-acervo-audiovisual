"""Carga transacional da amostra real, disponível no pacote e independente do Drive."""
from config import ROOT
from banco import connect,initialize,TABLES
import json,re,hashlib
from psycopg.types.json import Jsonb

def seed():
 initialize();data=json.loads((ROOT/'data/amostra.json').read_text(encoding='utf-8'))
 with connect() as c:
  # Todos os dados são inseridos em uma transação. Não duplicar nem sobrescrever cadastros.
  c.execute('LOCK TABLE obra IN EXCLUSIVE MODE')
  if c.execute('SELECT COUNT(*) AS n FROM obra').fetchone()['n']:raise ValueError('O banco já contém obras. A carga inicial exige tabelas sem obras; não sobrescreve registros existentes.')
  cache={}
  def add(table,**kw):
   from psycopg import sql
   row=c.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({}) RETURNING id').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,kw)),sql.SQL(',').join(sql.Placeholder() for _ in kw)),list(kw.values())).fetchone()
   return row['id']
  def named(table,name,**kw):
   name=str(name).strip()
   if not name:return None
   key=(table,name,*kw.values())
   if key not in cache:
    from psycopg import sql
    where=sql.SQL('nome=%s')
    args=[name]
    if 'fonte_id' in kw:where+=sql.SQL(' AND fonte_id=%s');args.append(kw['fonte_id'])
    found=c.execute(sql.SQL('SELECT id FROM {} WHERE ').format(sql.Identifier(table))+where,args).fetchone()
    cache[key]=found['id'] if found else add(table,nome=name,**kw)
   return cache[key]
  sources={}
  lots={}
  for name,url in [('ANCINE','https://www.gov.br/ancine/'),('Cinemateca','https://www.cinemateca.org.br/')]:
   sources[name]=named('fonte_dados',name,url=url,descricao='Registros públicos da '+name+'.')
   lots[name]=add('lote_importacao',fonte_id=sources[name],nome=data['manifesto']['execucao'],sha256=data['manifesto']['sha256_base'],observacao='Amostra dirigida da base integrada; não é amostra estatística do setor.')
  works={};records={}
  levels={'obra':'obra','serie':'serie','episodio':'episodio','temporada':'temporada'}
  for e in data['entidades']:
   works[e['id']]=add('obra',chave_tcc=e['id'],titulo_referencia=e['titulo'],nivel=levels.get(e['nivel'],'nao_especificado'),status=e['status'])
  for r in data['registros']:
   p=r['perfil'];o=r['original'];fields=o.get('campos',{});source=sources[r['fonte']]
   kind=o.get('TIPO_OBRA') if r['fonte']=='ANCINE' else fields.get('Categorias')
   kind_id=named('tipo_obra',str(kind)[:200]) if kind else None
   years=[v for v in p.get('anos',[]) if isinstance(v,int) and 1800<=v<=2100]
   durations=[v for v in p.get('duracoes',[]) if isinstance(v,(int,float)) and v>0]
   rid=add('registro_fonte',obra_id=works[r['entidade_id']],lote_id=lots[r['fonte']],tipo_obra_id=kind_id,chave_origem=r['id'],identificador_fonte=r.get('identificador_fonte'),ano=years[0] if years else None,duracao_minutos=durations[0] if durations else None,original_json=Jsonb(o),perfil_json=Jsonb(p),proveniencia_json=Jsonb(r['proveniencia']),observacao='Ano e duração: primeiro valor disponível no perfil; todos os valores permanecem no JSON.' if len(years)>1 or len(durations)>1 else None)
   records[r['id']]=rid
   title=o.get('TITULO_ORIGINAL') or o.get('titulo') or p.get('titulo_exibicao')
   seen=set()
   for value,kind in [(title,'declarado')]+[(t,'chave_normalizada') for t in p.get('titulos',[])]:
    if value and (value,kind) not in seen:add('titulo',registro_id=rid,valor=value,tipo=kind);seen.add((value,kind))
   seen=set()
   for cert in p.get('certificados_tipados',[]):
    code=cert.get('valor');role=cert.get('papel','nao_especificado')
    if not code or (code,role) in seen:continue
    seen.add((code,role));emission=o.get('DATA_EMISSAO_CPB')
    add('certificado',registro_id=rid,numero=code,esquema='CPB',papel=role,data_emissao=emission if emission and re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(emission)) else None,situacao=o.get('SITUACAO_OBRA'))
   # Nunca converter o município do requerente em local de produção.
   companies=[]
   if r['fonte']=='ANCINE' and o.get('REQUERENTE'):
    companies.append((o['REQUERENTE'],'requerente',o.get('CNPJ_REQUERENTE'),o.get('UF_REQUERENTE'),o.get('MUNICIPIO_REQUERENTE'),'REQUERENTE'))
   for line in str(fields.get('Produção','')).splitlines():
    if line.startswith('Companhia(s) produtora(s):'):
     for name in line.split(':',1)[1].split(';'):
      if name.strip():companies.append((name.strip(),'produtora',None,None,None,line))
   company_seen=set()
   for name,role,cnpj,uf,city,evidence in companies:
    if (name,role) in company_seen:continue
    company_seen.add((name,role))
    eid=named('empresa',name,fonte_id=source)
    c.execute('UPDATE empresa SET cnpj=COALESCE(cnpj,%s),uf=COALESCE(uf,%s),municipio=COALESCE(municipio,%s),observacao=%s WHERE id=%s',(cnpj,uf,city,'Nome literal por fonte; não representa desambiguação de homônimos.',eid))
    add('participacao_empresa',registro_id=rid,empresa_id=eid,papel=role,evidencia=evidence)
   people=[]
   for field in ['Direção','Argumento/roteiro','Fotografia','Montagem']:
    for line in str(fields.get(field,'')).splitlines():
     if ':' not in line:continue
     role,names=line.split(':',1)
     if role.strip() not in ['Direção','Roteiro','Argumento','Diálogos','Câmera','Direção de fotografia','Montagem']:continue
     for name in names.split(';'):
      if name.strip():people.append((name.strip(),role.strip(),None,line))
   for line in str(fields.get('Identidades/elenco','')).splitlines():
    if not line.strip():continue
    m=re.fullmatch(r'(.+?)\s*\(([^()]*)\)',line.strip())
    people.append(((m.group(1) if m else line).strip(),'Elenco',m.group(2) if m else None,line))
   seen=set()
   for name,role,character,evidence in people:
    if (name,role) in seen:continue
    seen.add((name,role))
    pid=named('pessoa',name,fonte_id=source,observacao='Nome literal por fonte; identidade da pessoa não foi desambiguada.')
    fid=named('funcao_credito',role)
    add('credito_pessoa',registro_id=rid,pessoa_id=pid,funcao_id=fid,personagem=character,evidencia=evidence)
   for line in str(fields.get('Data e local de produção','')).splitlines():
    if line.startswith('País:'):
     for name in re.split(r'[;/]',line.split(':',1)[1]):
      if name.strip():
       pid=named('pais',name.strip())
       c.execute('INSERT INTO obra_pais(registro_id,pais_id,evidencia) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(rid,pid,line))
   if fields.get('Gênero'):
    for name in str(fields['Gênero']).split('/'):
     if name.strip():
      gid=named('genero',name.strip()[:200]);c.execute('INSERT INTO obra_genero(registro_id,genero_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(rid,gid))
   # Material original é preservado como declaração completa, sem inferir bitola, cor ou som.
   if fields.get('Material original'):add('caracteristica_tecnica',registro_id=rid,nome='Material original',valor=fields['Material original'],unidade=None)
   if durations:add('caracteristica_tecnica',registro_id=rid,nome='Duração do perfil',valor=str(durations[0]),unidade='minutos')
  for rel in data['relacoes']:
   if rel['origem_id'] in works and rel['destino_id'] in works and rel['origem_id']!=rel['destino_id']:
    c.execute('INSERT INTO relacao_obra(origem_id,destino_id,tipo,status,evidencia_json) VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',(works[rel['origem_id']],works[rel['destino_id']],rel['tipo'],rel['status'],Jsonb(rel['evidencia'])))
  for d in data.get('decisoes',[]):
   if d['a'] in records and d['b'] in records:
    extra={'data_decisao':d['data']} if d.get('data') else {}
    add('decisao_integracao',registro_a_id=records[d['a']],registro_b_id=records[d['b']],parecer=d['parecer'],justificativa=d['justificativa'],responsavel=d['responsavel'],**extra)
  counts={name:c.execute('SELECT COUNT(*) AS n FROM '+name).fetchone()['n'] for name in TABLES}
 return {'tabelas':counts,'manifesto':data['manifesto']}

if __name__=='__main__':print(json.dumps(seed(),ensure_ascii=False,indent=2))

