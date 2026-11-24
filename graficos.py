"""Gráficos SVG a partir dos mesmos resultados SQL exibidos em tabela."""
from html import escape

def svg(rows,title='Resultado da consulta'):
 rows=list(rows)
 width=1050;left=480;right=80;top=55;bar=28;height=max(110,top+len(rows)*bar+38)
 maximum=max((float(r.get('total_obras',0)) for r in rows),default=0) or 1
 parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title,quote=True)}"><title>{escape(title)}</title><rect width="100%" height="100%" fill="white"/><g font-family="Segoe UI,Arial,sans-serif" font-size="13" fill="#203632">',f'<text x="20" y="25" font-size="17" font-weight="600">{escape(title)}</text>']
 for i,row in enumerate(rows):
  label=' · '.join(str(v) for k,v in row.items() if k!='total_obras');value=float(row.get('total_obras',0));y=top+i*bar
  shown=label[:62]+'…' if len(label)>63 else label
  parts.extend([f'<text x="20" y="{y+15}"><title>{escape(label)}</title>{escape(shown)}</text>',f'<rect x="{left}" y="{y}" width="{value/maximum*(width-left-right):.2f}" height="19" rx="2" fill="#185f52"/>',f'<text x="{left+value/maximum*(width-left-right)+8:.2f}" y="{y+15}">{value:g}</text>'])
 if not rows:parts.append('<text x="20" y="70">Nenhum resultado para os dados atuais.</text>')
 parts.append(f'<text x="{left}" y="{height-8}" fill="#5b6965">Quantidade de obras distintas por categoria</text></g></svg>')
 return ''.join(parts)

