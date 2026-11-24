# Sistema de gerenciamento e integração de dados do setor audiovisual brasileiro

Trabalho final de Banco de Dados (DEC7588), UFSC Araranguá, 2026.2. Autor: Eduardo Antunes.

O sistema integra uma amostra da Cinemateca Brasileira e da ANCINE no PostgreSQL. Cada registro preserva os dados declarados pela sua fonte e pode ser associado a um cadastro de obra em comum. A amostra contém 293 registros de origem e 191 cadastros de obra.

## Relatório e arquivos

| Conteúdo | Arquivo |
| --- | --- |
| Relatório completo | [PDF](docs/RELATORIO.pdf) |
| Modelo conceitual | [Diagrama ampliado](docs/modelos/conceitual.svg) |
| Modelo lógico | [Diagrama das 19 tabelas](docs/modelos/logico_completo.svg) e [dicionário de tabelas](docs/MODELO_LOGICO.md) |
| Criação das tabelas e consultas | [DDL comentado](sql/01_schema.sql), [três consultas](sql/02_consultas.sql) e [SQL para pgAdmin](CONSULTAS_PGADMIN.sql) |
| Gráficos das consultas | [Obras por década e fonte](docs/consulta_1.png), [empresas e papéis](docs/consulta_2.png) e [CPB por fonte e papel](docs/consulta_3.png) |
| Funcionalidades e requisitos | [Correspondência com o enunciado](docs/CHECKLIST_REQUISITOS.md) |

## Como executar no Windows

1. Instale Python 3.10 ou superior e PostgreSQL 15 ou superior.
2. Clone o repositório ou use **Code → Download ZIP** e extraia os arquivos em uma pasta gravável.
3. Abra `INICIAR_TRABALHO.cmd`. Mantenha o terminal aberto e acesse [o sistema local](http://127.0.0.1:8768/).

O iniciador prepara uma instância do PostgreSQL exclusiva para o projeto e carrega a amostra. O primeiro uso pode precisar de internet para instalar o driver Python. Se a instalação do PostgreSQL estiver em outro local, defina `PG_BIN` com o caminho da pasta `bin`. Para encerrar, feche o terminal da aplicação e execute `PARAR_BANCO.cmd`.

## Onde ver as consultas e os gráficos

No menu **Consultas e gráficos**, escolha uma das três consultas. A tela mostra o gráfico, a tabela de resultados e a opção **Ver SQL da consulta**. A função `svg()` recebe as linhas retornadas pelo PostgreSQL e gera o gráfico em [`graficos.py`](graficos.py). A rota `/api/report` chama essa função em [`servidor.py`](servidor.py).

## Comparação com Gemini

Em **Comparar com IA**, selecione os dois registros de **ABC, BRASIL** para repetir o exemplo. Use uma chave própria no campo de credencial ou em um arquivo `.env.txt` local, com `GEMINI_API_KEY` e, opcionalmente, `GEMINI_MODEL`. Uma nova chamada depende da disponibilidade e dos limites do provedor. A resposta serve para revisão dos registros. O resultado de um teste real está em [`evidencias/IA_REAL.json`](evidencias/IA_REAL.json).

## Dados e testes

A [amostra](data/amostra.json) é acompanhada de [um manifesto](data/manifesto.json). Na versão pública, os caminhos de proveniência foram reduzidos aos nomes dos arquivos e um endereço de e-mail em uma observação foi omitido.

Com o banco inicializado e a amostra carregada, execute `python -B -m unittest discover -s tests -v` na raiz para rodar os testes de integração.
