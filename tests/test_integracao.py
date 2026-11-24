"""Testes reais contra o PostgreSQL exclusivo da disciplina; não acessam a pesquisa."""
import sys,json,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import banco,importar,graficos,ia
from unittest.mock import patch
import psycopg

class Integracao(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  banco.initialize();cls.mark='TESTE_'+uuid.uuid4().hex[:10]

 def test_01_esquema_dados_reais_e_restricoes(self):
  meta=banco.metadata();self.assertEqual(len(meta),19)
  self.assertTrue(all(t['count']>0 for t in meta))
  with banco.connect() as c:
   self.assertEqual(c.execute('SELECT current_database() AS nome').fetchone()['nome'],'audiovisual_dec7588')
   n=c.execute("SELECT COUNT(*) AS n FROM information_schema.table_constraints WHERE table_schema='audiovisual' AND constraint_type='FOREIGN KEY'").fetchone()['n']
   self.assertGreaterEqual(n,20)

 def test_02_crud_das_dezenove_tabelas_e_dependencias(self):
  created=[];ids={};mark=self.mark
  def create(table,values):
   row=banco.save_row(table,values);created.append((table,row['id']));ids[table]=row['id'];return row
  def check(table,values,field,new):
   row=create(table,values);row=banco.save_row(table,{field:new},row['id']);self.assertEqual(str(row[field]),str(new))
   with banco.connect() as c:self.assertIsNotNone(c.execute('SELECT id FROM '+table+' WHERE id=%s',(row['id'],)).fetchone())
   self.assertGreater(banco.list_rows(table)['total'],0)
  try:
   check('fonte_dados',{'nome':mark},'descricao','Fonte de teste')
   check('lote_importacao',{'fonte_id':ids['fonte_dados'],'nome':mark,'sha256':'a'*64},'observacao','Atualizado')
   check('tipo_obra',{'nome':mark},'descricao','Atualizado')
   check('obra',{'titulo_referencia':mark,'nivel':'obra'},'observacao','Atualizado')
   other=create('obra',{'titulo_referencia':mark+'_outra'})['id']
   # create() guardou a outra como último id; restaurar a obra principal para as referências abaixo.
   main=created[-2][1];ids['obra']=main
   check('registro_fonte',{'obra_id':main,'lote_id':ids['lote_importacao'],'tipo_obra_id':ids['tipo_obra'],'chave_origem':mark,'ano':2001,'duracao_minutos':'2,5'},'observacao','Atualizado')
   rid=ids['registro_fonte']
   check('titulo',{'registro_id':rid,'valor':mark,'tipo':'declarado'},'valor',mark+'_editado')
   check('certificado',{'registro_id':rid,'numero':mark,'papel':'obra'},'situacao','Conferido')
   check('pessoa',{'fonte_id':ids['fonte_dados'],'nome':mark},'observacao','Atualizado')
   check('empresa',{'fonte_id':ids['fonte_dados'],'nome':mark},'observacao','Atualizado')
   check('funcao_credito',{'nome':mark},'descricao','Atualizado')
   check('credito_pessoa',{'registro_id':rid,'pessoa_id':ids['pessoa'],'funcao_id':ids['funcao_credito']},'evidencia','Atualizado')
   check('participacao_empresa',{'registro_id':rid,'empresa_id':ids['empresa'],'papel':'produtora'},'evidencia','Atualizado')
   check('pais',{'nome':mark},'nome',mark+'_editado')
   check('obra_pais',{'registro_id':rid,'pais_id':ids['pais']},'evidencia','Atualizado')
   check('genero',{'nome':mark},'nome',mark+'_editado')
   second_genre=create('genero',{'nome':mark+'_segundo'})['id'];first_genre=created[-2][1]
   check('obra_genero',{'registro_id':rid,'genero_id':first_genre},'genero_id',second_genre)
   check('caracteristica_tecnica',{'registro_id':rid,'nome':'Duração','valor':'2.5','unidade':'minutos'},'valor','3.5')
   check('relacao_obra',{'origem_id':main,'destino_id':other,'tipo':'episodio_da_serie','status':'teste'},'status','conferido')
   second_record=create('registro_fonte',{'obra_id':other,'lote_id':ids['lote_importacao'],'chave_origem':mark+'_b'})['id']
   check('decisao_integracao',{'registro_a_id':rid,'registro_b_id':second_record,'parecer':'incerto','justificativa':'Sem evidência suficiente','responsavel':'Teste automatizado'},'justificativa','Dados insuficientes')
   with self.assertRaises((psycopg.errors.ForeignKeyViolation,psycopg.errors.RestrictViolation)):banco.delete_row('obra',main)
   with self.assertRaises(psycopg.errors.CheckViolation):banco.save_row('registro_fonte',{'duracao_minutos':-1},rid)
   with self.assertRaises(psycopg.errors.CheckViolation):banco.save_row('relacao_obra',{'origem_id':main,'destino_id':main,'tipo':'teste','status':'teste'})
  finally:
   # Dependências podem apontar a um registro criado posteriormente: decisões primeiro.
   ordered=[r for r in reversed(created) if r[0]=='decisao_integracao']+[r for r in reversed(created) if r[0]!='decisao_integracao']
   # obra_genero referencia ambos os gêneros; apagar associação antes dos gêneros.
   ordered.sort(key=lambda r:0 if r[0] in ('decisao_integracao','obra_genero') else 1)
   for table,rid in ordered:banco.delete_row(table,rid)

 def test_03_sql_consultas_e_graficos(self):
  for i in range(3):
   r=banco.report(i);self.assertGreaterEqual(r['sql'].upper().count('JOIN '),2)
   self.assertIn('COUNT(DISTINCT',r['sql']);self.assertTrue(r['rows']);self.assertGreaterEqual(len(r['rows'][0]),2)
   chart=graficos.svg(r['rows'],r['titulo']);self.assertIn('<svg',chart);self.assertNotIn('<script',chart)
  with banco.connect() as c:
   expected=c.execute('''SELECT f.nome,(r.ano/10)*10 AS decada,COUNT(DISTINCT r.obra_id) AS n
    FROM registro_fonte r JOIN lote_importacao l ON l.id=r.lote_id JOIN fonte_dados f ON f.id=l.fonte_id
    WHERE r.ano IS NOT NULL GROUP BY f.nome,(r.ano/10)*10''').fetchall()
  self.assertEqual(sum(r['n'] for r in expected),sum(r['total_obras'] for r in banco.report(0)['rows']))

 def test_04_injecao_json_duplicatas_e_erros(self):
  self.assertEqual(banco.list_rows('obra',"' OR 1=1 --")['total'],0)
  with self.assertRaises(ValueError):banco.list_rows('obra; DROP SCHEMA audiovisual CASCADE')
  with self.assertRaises(ValueError):banco.save_row('obra',{'coluna_inexistente':'x'})
  with self.assertRaises(ValueError):banco.drop_schema('texto incorreto')
  with self.assertRaises(ValueError):importar.seed()

 def test_05_ia_sem_credencial_nao_simula_resposta(self):
  with patch('ia.configured_key',return_value=''):
   with self.assertRaises(ValueError):ia.compare(1,2,'gemini','modelo','')
  with self.assertRaises(ValueError):ia.compare(1,1,'ollama','modelo')
  class Response:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,*args):return json.dumps({'response':'Resposta de TESTE de transporte, não é inferência real.'}).encode()
  with patch('urllib.request.urlopen',return_value=Response()) as call:
   result=ia.compare(1,2,'ollama','modelo_teste')
   self.assertEqual(result['provider'],'ollama');self.assertIn('TESTE',result['resposta']);self.assertTrue(call.called)

if __name__=='__main__':unittest.main(verbosity=2)

