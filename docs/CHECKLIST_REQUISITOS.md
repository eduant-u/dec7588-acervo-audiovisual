# Correspondência com o enunciado DEC7588

O relatório principal é `docs/RELATORIO.pdf` (22 páginas). O código-fonte acompanha integralmente esta entrega. Os números de página desta tabela indicam a posição no arquivo PDF. A paginação impressa segue o padrão ABNT, sem contar a capa.

| Item | Conteúdo solicitado | Onde conferir |
|---|---|---|
| 1 | Objetivo geral do sistema | Relatório, seção 1, página 3 |
| 2 | Descrição detalhada e requisitos | Relatório, seção 2, páginas 4–5 |
| 3 | Modelagem conceitual com pelo menos 10 entidades | Relatório, seção 3, páginas 6–8; 14 entidades de domínio e cinco associações; Figura 1 em página paisagem e `docs/modelos/conceitual.svg` |
| 4 | Modelo lógico derivado do conceitual | Relatório, seção 4, páginas 9–13; 19 tabelas; `docs/modelos/logico_completo.svg` e `docs/MODELO_LOGICO.md` |
| 5 | Script DDL | Relatório, seção 5, páginas 14–16; arquivo completo `sql/01_schema.sql` |
| 6 | Três consultas com pelo menos três tabelas, agregação, descrição, resultado e gráfico | Relatório, seção 6, páginas 17–21; `sql/02_consultas.sql`; `docs/resultados_consultas.json`; gráficos em `docs/consulta_*.svg` e PNG |
| 7a | Conexão a PostgreSQL ou MySQL | PostgreSQL; `preparar_banco.py`, `config.py` e `banco.py` |
| 7b | Inserção, consulta, atualização e exclusão em cada tabela, considerando dependências | Tela Cadastros; `banco.py`, `servidor.py`, `static/app.js`; verificações nas 19 tabelas em `tests/test_integracao.py` |
| 7c | Executar consultas e exibir tabela e gráfico | Tela Consultas e gráficos; `banco.py`, `graficos.py`, `static/app.js` |
| 7d | Módulo principal/menu para acessar as operações | Navegação da aplicação em `static/index.html` |
| 7e | Criar tabelas a partir de banco vazio, carregar valores predefinidos e eliminar tabelas | Tela Banco de dados; `banco.py`, `importar.py`, `data/amostra.json`; confirmação para remover o esquema exclusivo |
| 7f | Integração com IA generativa para auxiliar uma atividade do domínio | Tela Comparar com IA; `ia.py`; comparação de metadados com Gemini validada em `evidencias/IA_REAL.json` |

Cada consulta implementada utiliza quatro tabelas, projeta três colunas e emprega `COUNT(DISTINCT ...)`. A tabela e o gráfico são produzidos a partir do mesmo resultado no PostgreSQL.

O relatório inclui capa completa (título, autor, disciplina, professor e data), sumário em página única e apresenta os itens 1 a 6 como seções, além de uma seção 7 sintética sobre execução e escopo. Os diagramas vetoriais ampliados e as fontes editáveis acompanham o PDF. A aplicação é iniciada por `INICIAR_TRABALHO.cmd`; as instruções estão no [README](../README.md).

A IA exige configuração de credencial e disponibilidade do provedor para uma nova chamada. As credenciais, o banco local gerado e as dependências instaladas não fazem parte do arquivo de entrega.
