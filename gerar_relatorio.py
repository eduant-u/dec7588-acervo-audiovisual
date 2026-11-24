"""Relatório do trabalho final de Banco de Dados (DEC7588) em formato acadêmico limpo (ABNT).
Dependências de autoria: reportlab e Pillow; dispensadas para executar o sistema.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import json, math, textwrap, re, hashlib
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, NextPageTemplate,
    Paragraph, Spacer, PageBreak, Table, TableStyle, Image, Preformatted, KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from PIL import Image as PILImage, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / 'docs'
PORTRAIT_W = A4[0] - 5 * cm
LANDSCAPE_W = landscape(A4)[0] - 5 * cm
LANDSCAPE_H = landscape(A4)[1] - 5 * cm

fontdir = Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('ArialLocal', str(fontdir / 'arial.ttf')))
pdfmetrics.registerFont(TTFont('ArialLocalBold', str(fontdir / 'arialbd.ttf')))
pdfmetrics.registerFontFamily('ArialLocal', normal='ArialLocal', bold='ArialLocalBold')

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='Body', fontName='ArialLocal', fontSize=12, leading=18,
    alignment=TA_JUSTIFY, firstLineIndent=1.25 * cm, spaceAfter=4,
    textColor=colors.black, allowWidows=0, allowOrphans=0,
))
styles.add(ParagraphStyle(
    name='BodyKeep', parent=styles['Body'], keepWithNext=True,
))
styles.add(ParagraphStyle(
    name='H1', fontName='ArialLocalBold', fontSize=12, leading=18,
    spaceBefore=0, spaceAfter=14, keepWithNext=True,
))
styles.add(ParagraphStyle(
    name='H2', fontName='ArialLocalBold', fontSize=12, leading=18,
    spaceBefore=16, spaceAfter=10, keepWithNext=True,
))
styles.add(ParagraphStyle(
    name='FrontTitle', parent=styles['H1'], alignment=TA_CENTER, spaceAfter=18,
))
styles.add(ParagraphStyle(
    name='SmallBody', fontName='ArialLocal', fontSize=10, leading=13,
    alignment=TA_JUSTIFY, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name='Cell', fontName='ArialLocal', fontSize=9.5, leading=12, alignment=TA_LEFT,
))
styles.add(ParagraphStyle(
    name='CellBold', parent=styles['Cell'], fontName='ArialLocalBold',
))
styles.add(ParagraphStyle(
    name='CellCompact', fontName='ArialLocal', fontSize=8.8, leading=10.8, alignment=TA_LEFT,
))
styles.add(ParagraphStyle(
    name='CellCompactBold', parent=styles['CellCompact'], fontName='ArialLocalBold',
))
styles.add(ParagraphStyle(
    name='CellCompactRight', parent=styles['CellCompact'], alignment=TA_RIGHT,
))
styles.add(ParagraphStyle(
    name='CellCompactBoldRight', parent=styles['CellCompactBold'], alignment=TA_RIGHT,
))
styles.add(ParagraphStyle(
    name='CellRight', parent=styles['Cell'], alignment=TA_RIGHT,
))
styles.add(ParagraphStyle(
    name='CellBoldRight', parent=styles['CellBold'], alignment=TA_RIGHT,
))
styles.add(ParagraphStyle(
    name='CoverInst', fontName='ArialLocalBold', fontSize=12, leading=18, alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    name='CoverText', fontName='ArialLocal', fontSize=12, leading=18, alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    name='CoverTitle', fontName='ArialLocalBold', fontSize=14, leading=21, alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    name='CoverInfo', fontName='ArialLocal', fontSize=11, leading=16, alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    name='CodeLocal', fontName='Courier', fontSize=8.5, leading=11,
    spaceBefore=6, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name='Caption', fontName='ArialLocalBold', fontSize=10, leading=13,
    spaceBefore=10, spaceAfter=5, keepWithNext=True,
))
styles.add(ParagraphStyle(
    name='Source', fontName='ArialLocal', fontSize=9.5, leading=12,
    spaceBefore=4, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name='TOCLocal', fontName='ArialLocalBold', fontSize=11.5, leading=18, spaceBefore=5,
))
styles.add(ParagraphStyle(
    name='TOCSub', fontName='ArialLocal', fontSize=11, leading=16, leftIndent=16, spaceBefore=0,
))

QUADRO = 0
TABELA = 0
FIGURA = 0


class Story(list):
    def append(self, item):
        if isinstance(item, list):
            self.extend(item)
        else:
            super().append(item)

    def extend(self, items):
        for item in items:
            self.append(item)


class Report(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        p_frame = Frame(
            3 * cm, 2 * cm, PORTRAIT_W, A4[1] - 5 * cm,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='portrait_frame',
        )
        l_frame = Frame(
            3 * cm, 2 * cm, LANDSCAPE_W, LANDSCAPE_H,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='landscape_frame',
        )
        self.addPageTemplates([
            PageTemplate(id='portrait', frames=[p_frame], pagesize=A4),
            PageTemplate(id='landscape', frames=[l_frame], pagesize=landscape(A4)),
        ])

    def beforeDocument(self):
        self.text_started = False
        self.section_pages = {}

    def afterFlowable(self, f):
        if not isinstance(f, Paragraph) or not hasattr(f, 'toc_level'):
            return
        text = f.getPlainText()
        if f.toc_level == 0:
            self.text_started = True
        key = 'heading_' + hashlib.sha256(text.encode()).hexdigest()[:18]
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, f.toc_level)
        # Capa não entra na contagem (ABNT): página impressa = página PDF - 1
        self.notify('TOCEntry', (f.toc_level, text, self.page - 1, key))
        self.section_pages[text] = {'pagina_pdf': self.page, 'pagina_impressa': self.page - 1}

    def afterPage(self):
        if not self.text_started:
            return
        pw, ph = self.canv._pagesize
        self.canv.saveState()
        self.canv.setFont('ArialLocal', 10)
        self.canv.setFillColor(colors.black)
        self.canv.drawRightString(pw - 2 * cm, ph - 2 * cm, str(self.page - 1))
        self.canv.restoreState()


def P(text, style='Body', toc_level=None):
    p = Paragraph(escape(str(text)), styles[style])
    if toc_level is not None:
        p.toc_level = toc_level
    return p


def H1(text):
    clean = re.sub(r'^(\d+)\.\s+', r'\1 ', str(text)).upper()
    return P(clean, 'H1', toc_level=0)


def H2(text):
    clean = re.sub(r'^(\d+\.\d+)\.\s+', r'\1 ', str(text))
    return P(clean, 'H2', toc_level=1)


def make_table(title, headers, rows, widths, numeric_cols=(), is_tabela=False, avail_width=PORTRAIT_W, compact=False):
    global QUADRO, TABELA
    if is_tabela:
        TABELA += 1
        label = f'Tabela {TABELA}'
    else:
        QUADRO += 1
        label = f'Quadro {QUADRO}'

    st_h = 'CellCompactBold' if compact else 'CellBold'
    st_hr = 'CellCompactBoldRight' if compact else 'CellBoldRight'
    st_b = 'CellCompact' if compact else 'Cell'
    st_br = 'CellCompactRight' if compact else 'CellRight'
    vpad = 2.8 if compact else 4

    header_row = [
        P(h, st_hr if idx in numeric_cols else st_h)
        for idx, h in enumerate(headers)
    ]
    body_rows = [
        [
            P(v if v is not None else '—', st_br if idx in numeric_cols else st_b)
            for idx, v in enumerate(row)
        ]
        for row in rows
    ]
    col_widths = [w * avail_width / sum(widths) for w in widths]
    table = Table([header_row] + body_rows, colWidths=col_widths, repeatRows=1, hAlign='LEFT')
    rules = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEABOVE', (0, 0), (-1, 0), 0.9, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 0.6, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 0.9, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), vpad),
        ('BOTTOMPADDING', (0, 0), (-1, -1), vpad),
    ]
    if not is_tabela:
        rules.append(('GRID', (0, 0), (-1, -1), 0.35, colors.black))
    table.setStyle(TableStyle(rules))
    table.keepWithNext = True
    return [
        P(f'{label} — {title}', 'Caption'),
        table,
        P('Fonte: elaboração própria (2026).', 'Source'),
    ]


def make_image(name, max_width=PORTRAIT_W, max_height=520):
    path = DOCS / name
    im = PILImage.open(path)
    w, h = im.size
    scale = min(max_width / w, max_height / h)
    return Image(str(path), width=w * scale, height=h * scale, hAlign='CENTER')


def make_figure(name, title, note='', kind='Figura', max_width=PORTRAIT_W, max_height=510):
    global FIGURA
    if kind == 'Figura':
        FIGURA += 1
        n = FIGURA
    else:
        n = int(Path(name).stem.split('_')[-1])
    pic = make_image(name, max_width=max_width, max_height=max_height)
    pic.keepWithNext = True
    source_text = 'Fonte: elaboração própria (2026).' + (f' {note}' if note else '')
    return [
        P(f'{kind} {n} — {title}', 'Caption'),
        pic,
        P(source_text, 'Source'),
    ]


def render_chart_png(rows, out_path):
    """Gera gráfico de barras horizontais nítido em alta resolução para o relatório."""
    font_reg = ImageFont.truetype(str(fontdir / 'arial.ttf'), 23)
    font_bold = ImageFont.truetype(str(fontdir / 'arialbd.ttf'), 22)
    font_axis = ImageFont.truetype(str(fontdir / 'arial.ttf'), 20)
    font_leg = ImageFont.truetype(str(fontdir / 'arial.ttf'), 20)

    has_fonte = bool(rows) and 'fonte' in rows[0]
    has_papel_empresa = bool(rows) and 'empresa' in rows[0] and 'papel' in rows[0]

    items = []
    for r in rows:
        val = int(r['total_obras']) if float(r['total_obras']).is_integer() else float(r['total_obras'])
        if has_papel_empresa:
            emp = str(r['empresa'])
            if len(emp) > 44:
                emp = emp[:43] + '…'
            papel = str(r['papel'])
            label = f'{emp} ({papel})'
            group = papel
        else:
            parts = [str(v) for k, v in r.items() if k != 'total_obras']
            label = ' · '.join(parts)
            group = str(r.get('fonte', ''))
        items.append((label, val, group))

    tmp = ImageDraw.Draw(PILImage.new('RGB', (10, 10)))
    max_lbl_w = max((tmp.textbbox((0, 0), it[0], font=font_reg)[2] for it in items), default=120)

    W = 1650
    pad_l = 24
    gap_lbl = 18
    left = max(pad_l + max_lbl_w + gap_lbl, 240)
    right = 88
    plot_w = W - left - right
    show_legend = has_fonte or has_papel_empresa
    top = 56 if show_legend else 22
    row_h = 44 if len(items) <= 10 else 38
    bar_h = 26 if len(items) <= 10 else 23
    bottom = 86
    H = top + len(items) * row_h + bottom

    im = PILImage.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(im)

    max_val = max((it[1] for it in items), default=1)
    if max_val <= 5:
        step = 1
    elif max_val <= 12:
        step = 2
    elif max_val <= 30:
        step = 5
    elif max_val <= 60:
        step = 10
    elif max_val <= 120:
        step = 20
    else:
        step = 25
    axis_max = math.ceil(max_val / step) * step

    if has_fonte:
        legend = [('ANCINE', '#185f52'), ('Cinemateca', '#4f8f82')]
        secondary = 'Cinemateca'
    elif has_papel_empresa:
        legend = [('Produtora', '#185f52'), ('Requerente', '#4f8f82')]
        secondary = 'requerente'
    else:
        legend = []
        secondary = None

    if legend:
        lx = left
        for name, col in legend:
            d.rounded_rectangle([lx, 14, lx + 24, 34], radius=3, fill=col)
            d.text((lx + 32, 12), name, fill='#203632', font=font_leg)
            lx += 32 + tmp.textbbox((0, 0), name, font=font_leg)[2] + 28

    plot_bottom = top + len(items) * row_h
    v = 0
    while v <= axis_max:
        x = left + (v / axis_max) * plot_w
        col = '#8fa39b' if v == 0 else '#e3eae6'
        d.line([(x, top - 6), (x, plot_bottom + 6)], fill=col, width=2 if v == 0 else 1)
        t = str(v)
        tw = tmp.textbbox((0, 0), t, font=font_axis)[2]
        d.text((x - tw / 2, plot_bottom + 12), t, fill='#4c5d57', font=font_axis)
        v += step

    for i, (label, val, group) in enumerate(items):
        cy = top + i * row_h + row_h // 2
        y0 = cy - bar_h // 2
        y1 = cy + bar_h // 2
        bb = tmp.textbbox((0, 0), label, font=font_reg)
        lw, lh = bb[2] - bb[0], bb[3] - bb[1]
        d.text((left - gap_lbl - lw, cy - lh // 2 - 2), label, fill='#1c2b27', font=font_reg)
        bw = max(4, (val / axis_max) * plot_w)
        bar_col = '#4f8f82' if (secondary and group == secondary) else '#185f52'
        d.rounded_rectangle([left, y0, left + bw, y1], radius=3, fill=bar_col)
        vt = str(val)
        vb = tmp.textbbox((0, 0), vt, font=font_bold)
        vh = vb[3] - vb[1]
        d.text((left + bw + 12, cy - vh // 2 - 2), vt, fill='#1c2b27', font=font_bold)

    xtitle = 'Quantidade de obras distintas por categoria'
    xt_w = tmp.textbbox((0, 0), xtitle, font=font_axis)[2]
    d.text((left + (plot_w - xt_w) / 2, plot_bottom + 46), xtitle, fill='#3c4d47', font=font_axis)
    im.save(out_path, dpi=(300, 300))


def build_cover():
    title = 'SISTEMA DE GERENCIAMENTO E INTEGRAÇÃO DE DADOS DO SETOR AUDIOVISUAL BRASILEIRO'
    return [
        P('UNIVERSIDADE FEDERAL DE SANTA CATARINA', 'CoverInst'),
        P('CAMPUS ARARANGUÁ', 'CoverInst'),
        Spacer(1, 24),
        P('Disciplina: Banco de Dados (DEC7588) — Semestre 2026.2', 'CoverInfo'),
        P('Professor: Alexandre Leopoldo Gonçalves', 'CoverInfo'),
        Spacer(1, 68),
        P('EDUARDO ANTUNES', 'CoverText'),
        Spacer(1, 110),
        P(title, 'CoverTitle'),
        Spacer(1, 14),
        P('Relatório do Projeto Final de Banco de Dados', 'CoverInfo'),
        Spacer(1, 210),
        P('Araranguá', 'CoverText'),
        P('Novembro de 2026', 'CoverText'),
        PageBreak(),
    ]


def build_ddl_blocks(ddl_text):
    """Quebra o script DDL em blocos lógicos (CREATE TABLE / índices) sem partir definições no meio."""
    blocks = []
    current = []
    in_table = False
    for raw_line in ddl_text.splitlines():
        line = raw_line.rstrip()
        if line.startswith('CREATE TABLE '):
            if current:
                blocks.append('\n'.join(current))
                current = []
            in_table = True
            current.append(line)
        elif in_table:
            current.append(line)
            if line.strip() == ');':
                blocks.append('\n'.join(current))
                current = []
                in_table = False
        elif line.startswith('CREATE INDEX '):
            if current and not current[0].startswith('CREATE INDEX '):
                blocks.append('\n'.join(current))
                current = []
            current.append(line)
        else:
            if line or current:
                current.append(line)
    if current:
        blocks.append('\n'.join(current))

    flowables = []
    for blk in blocks:
        wrapped = []
        for l in blk.splitlines():
            wrapped.extend(
                textwrap.wrap(l, width=84, replace_whitespace=False, drop_whitespace=False, subsequent_indent='  ')
                or ['']
            )
        flowables.append(KeepTogether([Preformatted('\n'.join(wrapped), styles['CodeLocal'])]))
    return flowables


def main():
    global QUADRO, TABELA, FIGURA
    QUADRO = TABELA = FIGURA = 0

    meta = json.loads((DOCS / 'metadados.json').read_text(encoding='utf-8'))
    reports = json.loads((DOCS / 'resultados_consultas.json').read_text(encoding='utf-8'))

    # Regenera os PNGs dos 3 gráficos em alta legibilidade a partir dos resultados reais
    for i, r in enumerate(reports, 1):
        render_chart_png(r['rows'], DOCS / f'consulta_{i}.png')

    story = Story(build_cover())

    # Sumário (1 página limpa)
    story.append(P('SUMÁRIO', 'FrontTitle'))
    toc = TableOfContents()
    toc.levelStyles = [styles['TOCLocal'], styles['TOCSub']]
    toc.dotsMinLevel = 0
    story.extend([toc, PageBreak()])

    # 1. Objetivo geral do sistema (1 parágrafo completo, conforme item 1 do enunciado)
    story.append(H1('1. Objetivo geral do sistema'))
    story.append(P(
        'Desenvolver um sistema de banco de dados relacional capaz de integrar, organizar e consultar '
        'informações provenientes de bases públicas do setor audiovisual brasileiro, tendo como referência '
        'os registros da Cinemateca Brasileira e da Agência Nacional do Cinema (ANCINE). O sistema armazena '
        'de forma estruturada dados sobre obras audiovisuais, pessoas, empresas, créditos de produção, '
        'características técnicas e certificados administrativos, preservando os valores originais e a '
        'proveniência institucional de cada declaração, além de explicitar relações entre séries e episódios, '
        'divergências de atributos e pareceres humanos de integração. A solução reutiliza uma amostra dirigida '
        'do trabalho de conclusão de curso (TCC) do autor em uma instância PostgreSQL totalmente independente '
        'da base original — contendo 293 registros de origem associados a 191 entidades propostas — e oferece '
        'uma aplicação com operações completas de cadastro nas 19 tabelas, consultas analíticas com saída '
        'tabular e gráfica e apoio de inteligência artificial (IA) generativa para comparação de registros sob '
        'revisão humana.'
    ))

    # 2. Descrição detalhada e requisitos
    story.extend([PageBreak(), H1('2. Descrição detalhada e requisitos')])
    description = [
        'O sistema atende à necessidade de consultar e gerenciar descrições audiovisuais distribuídas entre fontes institucionais com finalidades distintas. A ANCINE fornece informações de registro administrativo, como Certificado de Produto Brasileiro (CPB), requerente, situação, data de emissão e características declaradas, enquanto a Filmografia da Cinemateca Brasileira reúne descrições filmográficas, incluindo títulos, créditos, gênero, material original e dados de produção. Essas diferenças explicam variações de cobertura e vocabulário; por isso, o modelo preserva a instituição de origem em vez de fundir silenciosamente declarações conflitantes em um valor único.',
        'A unidade central do domínio é a obra audiovisual proposta, que pode ser descrita por um ou mais registros de origem. Cada registro pertence a um lote de importação vinculado a uma fonte de dados. Atributos sujeitos a divergência entre instituições — como ano, duração e tipo de obra — permanecem no registro, permitindo comparações rastreáveis. O título de referência na tabela de obras facilita a localização, enquanto a tabela de títulos conserva a declaração original e chaves normalizadas de comparação. Um identificador técnico do TCC possibilita rastrear a seleção da amostra sem substituir os identificadores institucionais.',
        'Os créditos relacionam um registro a uma pessoa e a uma função explicitamente declarada (como direção, roteiro ou elenco). A participação de empresas preserva o papel declarado, distinguindo requerente de produtora. Pessoas e empresas são cadastradas por nome literal e fonte, respeitando que a igualdade nominal não comprova identidade entre homônimos. Gêneros e países associam-se aos registros por tabelas associativas próprias, e o município do requerente é mantido na tabela de empresas sem ser inferido como local de produção da obra.',
        'Os certificados vinculam-se às declarações dos registros com número, esquema, papel e data de emissão, diferenciando um certificado da própria obra de uma referência à série. Episódios e séries permanecem como obras distintas conectadas por relações tipadas e evidências. Já a tabela de decisões de integração registra o parecer humano sobre pares de registros (justificativa, responsável e data), sem disparar fusões automáticas nem alterar os dados originais da pesquisa.',
        'A aplicação desenvolvida em Python com PostgreSQL e Psycopg organiza-se em quatro módulos acessíveis por menu principal: Cadastros (inclusão, consulta, busca, paginação, atualização e exclusão nas 19 tabelas), Consultas e gráficos (execução das três consultas SQL agregadas com saída tabular e gráfica sincronizada), Comparar com IA (recuperação de dois registros e envio de campos selecionados a um grande modelo de linguagem para apoio à análise) e Banco de dados (visualização do DDL, criação das tabelas, carga da amostra e remoção do esquema exclusivo mediante confirmação).',
        'A integridade referencial é garantida diretamente pelo PostgreSQL com chaves estrangeiras configuradas com exclusão restrita (ON DELETE RESTRICT), bloqueando remoções que deixariam registros dependentes órfãos e retornando mensagens claras ao usuário. A carga inicial executa em transação única (com rollback automático em caso de falha) e recusa sobrescrever bases já populadas. Os registros originais, perfis e metadados de proveniência são preservados em colunas JSONB para auditoria, complementando a projeção relacional. A instância de demonstração opera localmente em loopback, com credenciais geradas apenas no ambiente local.',
    ]
    for text in description:
        story.append(P(text))

    reqs = [
        ('RF01', 'Gerenciar fontes, lotes e demais cadastros do domínio nas 19 tabelas do modelo.'),
        ('RF02', 'Preservar registros originais, perfis e proveniência institucional das declarações.'),
        ('RF03', 'Relacionar obras e registros sem sobrescrever divergências entre fontes.'),
        ('RF04', 'Representar créditos de pessoas, participações de empresas, classificações e características técnicas.'),
        ('RF05', 'Registrar certificados administrativos com seus respectivos papéis e relações entre obras.'),
        ('RF06', 'Executar três consultas SQL agregadas (≥ 3 tabelas) com exibição tabular e gráfica.'),
        ('RF07', 'Criar todas as tabelas a partir de banco vazio e carregar a amostra predefinida de arquivos externos.'),
        ('RF08', 'Eliminar todas as tabelas do esquema exclusivo da aplicação mediante confirmação explícita.'),
        ('RF09', 'Auxiliar a comparação de dois registros via integração com grande modelo de linguagem (LLM).'),
        ('RF10', 'Permitir consulta e manutenção das decisões humanas de integração entre registros.'),
    ]
    story.extend([
        H2('2.1 Requisitos funcionais'),
        make_table('Requisitos funcionais do sistema', ['Código', 'Requisito'], reqs, [58, 442]),
    ])

    # 3. Modelagem conceitual (com Figura 1 em página paisagem para leitura confortável!)
    story.extend([
        PageBreak(),
        H1('3. Modelagem conceitual'),
        P(
            'O modelo conceitual distingue 14 tipos de entidade de domínio e cinco associações com '
            'representação própria, atendendo com folga ao mínimo de 10 entidades e resultando em 19 tabelas '
            'na etapa lógica. O Quadro 2 sintetiza o significado de cada elemento, enquanto a Figura 1 '
            '(apresentada na página seguinte em formato paisagem para melhor leitura) exibe o diagrama completo '
            'com seus atributos e cardinalidades. Os diagramas editáveis e em formato vetorial acompanham a '
            'entrega em docs/modelos/.'
        ),
    ])

    meanings = {
        'fonte_dados': 'Instituição ou base responsável pela declaração.',
        'lote_importacao': 'Conjunto importado de uma fonte, com hash e data de execução.',
        'tipo_obra': 'Vocabulário de tipos/categorias efetivamente declarado nas fontes.',
        'obra': 'Identidade audiovisual proposta ou série referenciada.',
        'registro_fonte': 'Descrição institucional de uma obra em um lote de importação.',
        'titulo': 'Declaração de título ou chave normalizada de um registro.',
        'certificado': 'Identificador administrativo (como CPB) e seu papel no contexto.',
        'pessoa': 'Nome creditado por uma fonte, sem desambiguação de homônimos.',
        'empresa': 'Organização ou requerente cadastrado conforme a declaração de origem.',
        'funcao_credito': 'Papel exercido por uma pessoa no crédito (direção, elenco etc.).',
        'credito_pessoa': 'Associação ternária entre registro, pessoa e função, com personagem/evidência.',
        'participacao_empresa': 'Associação entre registro e empresa, preservando o papel declarado.',
        'pais': 'País explicitamente indicado pela fonte.',
        'obra_pais': 'Associação de país ao registro com evidência da produção.',
        'genero': 'Denominação de gênero declarada pela fonte.',
        'obra_genero': 'Associação de gênero ao registro.',
        'caracteristica_tecnica': 'Declaração de material, duração ou outra característica técnica.',
        'relacao_obra': 'Associação tipada entre obras distintas (por exemplo, episódio e série).',
        'decisao_integracao': 'Parecer humano sobre dois registros, com justificativa, autoria e data.',
    }
    assoc_set = {'credito_pessoa', 'participacao_empresa', 'obra_pais', 'obra_genero', 'relacao_obra'}
    story.append(make_table(
        'Entidades e associações do modelo conceitual',
        ['Elemento', 'Tipo', 'Significado'],
        [(t['label'], 'Associação' if t['name'] in assoc_set else 'Entidade', meanings[t['name']]) for t in meta],
        [140, 68, 292],
        compact=True,
    ))

    # Troca para página paisagem exclusivamente para a Figura 1!
    story.extend([
        NextPageTemplate('landscape'),
        PageBreak(),
        make_figure(
            'modelos/conceitual.png',
            'Modelo conceitual completo',
            'Retângulos: entidades (14); losangos: associações (5). Versão vetorial em docs/modelos/conceitual.svg.',
            kind='Figura',
            max_width=LANDSCAPE_W,
            max_height=LANDSCAPE_H - 58,
        ),
        NextPageTemplate('portrait'),
        PageBreak(),
    ])

    story.append(H2('3.1 Principais regras de relacionamento e cardinalidade'))
    relations = [
        'Uma fonte fornece zero ou muitos lotes; cada lote pertence a exatamente uma fonte (1 : 0..N).',
        'Uma obra recebe zero ou muitos registros; cada registro descreve exatamente uma obra e pertence a exatamente um lote. O tipo de obra é opcional no registro (0..1 : 0..N).',
        'Um registro recebe zero ou muitos títulos, certificados e características técnicas, sendo cada declaração vinculada a exatamente um registro.',
        'Crédito de pessoa constitui uma associação ternária entre registro, pessoa e função, com unicidade para cada combinação (registro, pessoa, função).',
        'Participação de empresa associa um registro a uma empresa preservando o papel declarado. Países e gêneros mantêm relacionamentos N:N com registros por meio de associações próprias.',
        'Relação entre obras conecta duas obras distintas (origem e destino), mantendo episódio e série como identidades separadas.',
        'Cada decisão de integração referencia dois registros diferentes e armazena parecer, justificativa, responsável e data, permitindo múltiplas revisões ao longo do tempo.',
    ]
    for text in relations:
        story.append(P(text))

    # 4. Modelagem lógica e derivação
    story.extend([
        PageBreak(),
        H1('4. Modelagem lógica e derivação'),
        P(
            'Na passagem do modelo conceitual para o lógico relacional, cada entidade e associação com atributos '
            'ou multiplicidade N:N foi convertida em tabela com chave primária substituta do tipo bigint gerada '
            'por identidade (GENERATED BY DEFAULT AS IDENTITY). Os relacionamentos 1:N foram implementados por '
            'chaves estrangeiras no lado N, e restrições UNIQUE impedem duplicações indevidas em combinações '
            'como (registro, pessoa, função) e (registro, empresa, papel). Todas as chaves estrangeiras adotam '
            'ON DELETE RESTRICT para explicitar as dependências durante a manutenção dos dados.'
        ),
        P(
            'Para evitar redundância, o nome da fonte não é repetido em cada registro, sendo obtido pela cadeia '
            'registro_fonte → lote_importacao → fonte_dados. Pessoas e empresas guardam referência direta à fonte '
            'declarante, e listas multivaloradas (títulos, créditos, países e gêneros) foram decompostas em linhas '
            'próprias. Colunas JSONB preservam os documentos originais e perfis de proveniência para auditoria, '
            'complementando as colunas relacionais usadas nas consultas e restrições. Para facilitar a leitura, '
            'as Figuras 2, 3 e 4 apresentam o modelo lógico dividido em três recortes temáticos (tabelas '
            'compartilhadas entre recortes são reapresentadas apenas para manter o contexto).'
        ),
    ])

    for idx, (group, title) in enumerate([
        ('identificacao', 'Identificação e proveniência'),
        ('agentes', 'Pessoas, empresas e créditos'),
        ('classificacao_integracao', 'Classificação e integração'),
    ], 1):
        if idx > 1:
            story.append(PageBreak())
        story.extend([
            H2(f'4.{idx} {title}'),
            P(
                f'A Figura {FIGURA + 1} detalha o recorte de {title.lower()}, evidenciando chaves primárias '
                '(PK), chaves estrangeiras (FK), tipos de dados e cardinalidades.',
                'BodyKeep',
            ),
            make_figure(
                f'modelos/logico_{group}.png',
                f'Modelo lógico: {title.lower()}',
                'PK: chave primária; FK: chave estrangeira. Versão vetorial em docs/modelos/.',
                kind='Figura',
                max_width=PORTRAIT_W,
                max_height=520,
            ),
        ])

    # 4.4 Resumo compacto das 19 tabelas (substitui as 7 páginas redundantes de 4.4.1–4.4.19!)
    story.extend([
        PageBreak(),
        H2('4.4 Resumo das tabelas implementadas'),
        P(
            'O Quadro 3 consolida as 19 tabelas derivadas do modelo conceitual, indicando a quantidade de colunas, '
            'as referências estrangeiras e o volume de registros carregados na amostra inicial. O detalhamento '
            'completo de cada coluna, tipo e restrição consta no script DDL (Seção 5) e no dicionário de dados '
            'em docs/MODELO_LOGICO.md.'
        ),
    ])
    summary_rows = []
    for t in meta:
        fks = sorted({f['target'] for f in t['fields'] if f['target']})
        summary_rows.append((
            t['name'],
            str(len(t['fields'])),
            ', '.join(fks) if fks else '—',
            str(t['count']),
        ))
    story.append(make_table(
        'Resumo das 19 tabelas do modelo lógico e volume na carga inicial',
        ['Tabela', 'Colunas', 'Referências (FK)', 'Linhas'],
        summary_rows,
        [140, 62, 240, 58],
        numeric_cols=(1, 3),
        compact=True,
    ))

    # 5. Script DDL (com KeepTogether por CREATE TABLE para evitar quebras feias)
    story.extend([
        PageBreak(),
        H1('5. Script DDL'),
        P(
            'O script a seguir corresponde exatamente ao arquivo sql/01_schema.sql utilizado pela aplicação. '
            'Ele cria o esquema exclusivo audiovisual no banco audiovisual_dec7588 (PostgreSQL), definindo as '
            '19 tabelas, restrições de chave primária, chave estrangeira (ON DELETE RESTRICT), unicidade, '
            'validação (CHECK) e índices auxiliares. A operação de limpeza da aplicação executa '
            'DROP SCHEMA audiovisual CASCADE exclusivamente sobre esse esquema mediante confirmação.'
        ),
    ])
    ddl_text = (ROOT / 'sql/01_schema.sql').read_text(encoding='utf-8')
    story.extend(build_ddl_blocks(ddl_text))

    # 6. Consultas agregadas e gráficos
    story.extend([
        PageBreak(),
        H1('6. Consultas agregadas e gráficos'),
        P(
            'As três consultas a seguir utilizam quatro tabelas cada e projetam três colunas, empregando a '
            'função de agregação COUNT(DISTINCT ...). Os resultados foram executados diretamente no PostgreSQL '
            'sobre a carga inicial e correspondem exatamente às consultas executadas dinamicamente pela aplicação, '
            'atualizando tabelas e gráficos conforme os cadastros são modificados.'
        ),
    ])

    col_labels = {
        'fonte': 'Fonte',
        'decada': 'Década',
        'total_obras': 'Total de obras',
        'empresa': 'Empresa',
        'papel': 'Papel declarado',
    }
    for i, r in enumerate(reports, 1):
        if i > 1:
            story.append(PageBreak())
        story.extend([
            H2(f'6.{i} {r["titulo"]}'),
            P(f'{r["objetivo"]} Unidade de contagem: {r["unidade"]}. {r["nota"]}'),
        ])
        code_lines = []
        for line in r['sql'].splitlines():
            code_lines.extend(textwrap.wrap(line, width=84, subsequent_indent='  ') or [''])
        story.append(KeepTogether([Preformatted('\n'.join(code_lines), styles['CodeLocal'])]))

        cols = list(r['rows'][0])
        num_cols = tuple(idx for idx, k in enumerate(cols) if k in ('decada', 'total_obras'))
        widths = [275, 125, 100] if 'empresa' in cols else [180, 180, 140]
        total_rows = len(r['rows'])
        sample_rows = r['rows'][:10]
        story.append(make_table(
            r['titulo'],
            [col_labels.get(k, k) for k in cols],
            [[row[k] for k in cols] for row in sample_rows],
            widths,
            numeric_cols=num_cols,
            is_tabela=True,
        ))
        if total_rows > 10:
            note_sample = (
                f'Amostra tabular: 10 primeiras linhas das {total_rows} retornadas pela consulta. '
                f'O Gráfico {i} apresenta todas as {total_rows} linhas obtidas.'
            )
        else:
            note_sample = (
                f'A tabela acima exibe todas as {total_rows} linhas retornadas pela consulta, '
                f'também representadas visualmente no Gráfico {i}.'
            )
        story.append(P(note_sample, 'SmallBody'))
        chart_max_h = 340 if i == 1 else (290 if i == 2 else 220)
        story.append(KeepTogether(make_figure(
            f'consulta_{i}.png',
            r['titulo'],
            'Dados obtidos via consulta SQL na instância PostgreSQL da disciplina.',
            kind='Gráfico',
            max_width=PORTRAIT_W,
            max_height=chart_max_h,
        )))

    # 7. Visão geral da aplicação e execução (enxuta, objetiva, sem log de testes ou hashes crus)
    story.extend([
        PageBreak(),
        H1('7. Aplicação, execução e considerações finais'),
        P(
            'A aplicação prática referente ao item 7 do enunciado acompanha esta entrega no mesmo arquivo '
            'compactado, com ponto de entrada em INICIAR_TRABALHO.cmd e instruções de reprodução em README.md '
            'e LEIA_PRIMEIRO_ENTREGA.txt. Ao ser iniciada, prepara uma instância PostgreSQL local exclusiva, '
            'cria o esquema audiovisual caso ainda não exista, realiza a carga da amostra em data/amostra.json '
            'e abre a interface web principal com acesso aos quatro módulos: Cadastros (CRUD nas 19 tabelas com '
            'respeito às chaves estrangeiras), Consultas e gráficos, Comparar com IA e Banco de dados (criação, '
            'carga e remoção completa das tabelas mediante confirmação).'
        ),
        P(
            'No módulo de IA generativa, o usuário seleciona dois registros armazenados no banco e envia apenas '
            'os metadados relevantes para um grande modelo de linguagem (validado com Gemini e compatível também '
            'com OpenAI ou Ollama local). O modelo destaca compatibilidades e divergências entre as fontes (como '
            'título, ano, CPB e duração) para apoiar a análise, sem executar fusões automáticas no banco de dados. '
            'Por segurança, nenhuma chave de API acompanha o pacote entregue; o usuário informa sua credencial '
            'localmente ao executar novas comparações, e um exemplo real de resposta sem credenciais está '
            'registrado em evidencias/IA_REAL.json.'
        ),
        P(
            'Por tratar-se de uma amostra dirigida derivada de pesquisa em andamento no TCC (293 registros '
            'associados a 191 entidades propostas), os resultados quantitativos refletem o recorte carregado '
            'para demonstração e não a distribuição populacional completa do audiovisual brasileiro. A modelagem '
            'cumpre integralmente o propósito de gerenciar cadastros, preservar a proveniência institucional e '
            'apoiar análises comparativas com integridade referencial.'
        ),
    ])

    doc = Report(
        str(DOCS / 'RELATORIO.pdf'),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=3 * cm,
        topMargin=3 * cm,
        bottomMargin=2 * cm,
        title='Sistema de gerenciamento e integração de dados do setor audiovisual brasileiro',
        author='Eduardo Antunes',
    )
    doc.multiBuild(story)
    (DOCS / 'paginas_relatorio.json').write_text(
        json.dumps(doc.section_pages, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    print('Relatório PDF gerado:', DOCS / 'RELATORIO.pdf')


if __name__ == '__main__':
    main()
