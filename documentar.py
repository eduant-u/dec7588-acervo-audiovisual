"""Exporta metadados, modelos DOT e resultados reais para a documentação."""
from config import ROOT
import banco,graficos,json
from pathlib import Path

GROUPS={
 'identificacao':['fonte_dados','lote_importacao','tipo_obra','obra','registro_fonte','titulo','certificado','caracteristica_tecnica'],
 'agentes':['fonte_dados','registro_fonte','pessoa','empresa','funcao_credito','credito_pessoa','participacao_empresa'],
 'classificacao_integracao':['obra','registro_fonte','pais','genero','obra_pais','obra_genero','relacao_obra','decisao_integracao']
}
ASSOCIATIONS={'credito_pessoa','participacao_empresa','obra_pais','obra_genero','relacao_obra'}
CONCEPT_ATTRIBUTES={
 'fonte_dados':'nome, endereço, descrição','lote_importacao':'nome, hash, data de importação',
 'tipo_obra':'nome, descrição','obra':'título de referência, nível, status',
 'registro_fonte':'identificador, ano, duração, proveniência','titulo':'valor, tipo',
 'certificado':'número, esquema, papel, emissão','pessoa':'nome declarado, observação',
 'empresa':'nome, CNPJ, UF, município','funcao_credito':'nome, descrição',
 'credito_pessoa':'personagem, evidência','participacao_empresa':'papel, evidência',
 'pais':'nome declarado','genero':'nome declarado','obra_pais':'evidência',
 'obra_genero':'associação por registro','caracteristica_tecnica':'nome, valor, unidade',
 'relacao_obra':'tipo, status, evidência','decisao_integracao':'parecer, justificativa, responsável, data'
}
def dot(meta,subset=None,conceptual=False):
 subset=set(subset or [t['name'] for t in meta]);lines=['digraph G {','graph [rankdir=LR, bgcolor="white", pad="0.25", nodesep="0.35", ranksep="0.7", splines=polyline];','node [shape=plain, fontname="Arial", fontsize=12];','edge [fontname="Arial", fontsize=10, color="#65796d", arrowsize=0.7];']
 from html import escape
 for t in meta:
  if t['name'] not in subset:continue
  if conceptual:
   title=t['label']+'\n'+CONCEPT_ATTRIBUTES[t['name']];shape='box' if t['name'] not in ASSOCIATIONS else 'diamond'
   lines.append(f'"{t["name"]}" [shape={shape},style="rounded,filled",fillcolor="#edf3ee",label={json.dumps(title,ensure_ascii=False)},fontname="Arial",fontsize=15];')
  else:
   rows=[f'<TR><TD BGCOLOR="#185f52" ALIGN="LEFT"><FONT COLOR="white"><B>{t["name"]}</B></FONT></TD></TR>']
   for f in t['fields']:
    desc=f['name']+' : '+f['type'].replace('timestamp with time zone','timestamptz').replace('character varying','varchar')
    if f['name']=='id':desc+=' [PK]'
    if f['target']:desc+=' [FK]'
    rows.append(f'<TR><TD ALIGN="LEFT">{escape(desc)}</TD></TR>')
   lines.append(f'"{t["name"]}" [label=<<TABLE BORDER="1" COLOR="#bccbbf" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6">'+''.join(rows)+'</TABLE>>];')
 for t in meta:
  if t['name'] not in subset:continue
  for f in t['fields']:
   if f['target'] in subset:
    # Pai pode ter zero ou muitos filhos; cada filho exige um pai quando FK é NOT NULL.
    parent='1' if f['required'] else '0..1'
    lines.append(f'"{f["target"]}" -> "{t["name"]}" [label="{f["name"].replace("_id", "")}\\n{parent} : 0..N",dir=none];')
 lines.append('}')
 return '\n'.join(lines)

def main():
 docs=ROOT/'docs';models=docs/'modelos';models.mkdir(parents=True,exist_ok=True)
 meta=banco.metadata();reports=[]
 (docs/'metadados.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
 for i in range(3):
  r=banco.report(i);reports.append(r);(docs/f'consulta_{i+1}.svg').write_text(graficos.svg(r['rows'],r['titulo']),encoding='utf-8')
 (docs/'resultados_consultas.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
 (models/'conceitual.dot').write_text(dot(meta,conceptual=True),encoding='utf-8')
 (models/'logico_completo.dot').write_text(dot(meta),encoding='utf-8')
 for group,names in GROUPS.items():
  (models/f'logico_{group}.dot').write_text(dot(meta,names),encoding='utf-8')
 # Mermaid editável em qualquer ferramenta compatível, sem depender de renderização externa.
 mermaid=['erDiagram']
 for t in meta:
  mermaid.append('    '+t['name'].upper()+' {')
  for f in t['fields']:
   kind=f['type'].replace(' ','_');key=' PK' if f['name']=='id' else ' FK' if f['target'] else ''
   mermaid.append(f'        {kind} {f["name"]}{key}')
  mermaid.append('    }')
 for t in meta:
  for f in t['fields']:
   if f['target']:
    mermaid.append('    '+f['target'].upper()+(' ||--o{ ' if f['required'] else ' |o--o{ ')+t['name'].upper()+' : '+f['name'])
 (models/'modelo_logico.mmd').write_text('\n'.join(mermaid),encoding='utf-8')
 rows=['# Modelo lógico implementado','', 'PostgreSQL; 19 tabelas. PK: chave primária. FK: chave estrangeira. Todas as FKs usam ON DELETE RESTRICT.','']
 for t in meta:
  rows.extend(['## '+t['label']+' (`'+t['name']+'`)','','| Campo | Tipo | Obrigatório na criação | Referência |','|---|---|---|---|'])
  for f in t['fields']:rows.append(f'| {f["name"]} | {f["type"]} | {"Sim" if f["required"] else "Não / padrão"} | {f["target"] or ("PK automática" if f["name"]=="id" else "-")} |')
  rows.append('')
 (docs/'MODELO_LOGICO.md').write_text('\n'.join(rows),encoding='utf-8')
 print('Documentação extraída do PostgreSQL: 19 tabelas, três consultas e cinco diagramas DOT.')

if __name__=='__main__':main()

