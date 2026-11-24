# Modelo lógico implementado

PostgreSQL; 19 tabelas. PK: chave primária. FK: chave estrangeira. Todas as FKs usam ON DELETE RESTRICT.

## Fontes de dados (`fonte_dados`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| nome | character varying | Sim | - |
| url | text | Não / padrão | - |
| descricao | text | Não / padrão | - |

## Lotes de importação (`lote_importacao`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| fonte_id | bigint | Sim | fonte_dados |
| nome | character varying | Sim | - |
| sha256 | character varying | Sim | - |
| data_importacao | timestamp with time zone | Não / padrão | - |
| observacao | text | Não / padrão | - |

## Tipos de obra (`tipo_obra`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| nome | character varying | Sim | - |
| descricao | text | Não / padrão | - |

## Obras audiovisuais (`obra`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| chave_tcc | text | Não / padrão | - |
| titulo_referencia | text | Sim | - |
| nivel | character varying | Não / padrão | - |
| status | character varying | Não / padrão | - |
| observacao | text | Não / padrão | - |

## Registros das fontes (`registro_fonte`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| obra_id | bigint | Sim | obra |
| lote_id | bigint | Sim | lote_importacao |
| tipo_obra_id | bigint | Não / padrão | tipo_obra |
| chave_origem | text | Sim | - |
| identificador_fonte | text | Não / padrão | - |
| ano | integer | Não / padrão | - |
| duracao_minutos | numeric | Não / padrão | - |
| original_json | jsonb | Não / padrão | - |
| perfil_json | jsonb | Não / padrão | - |
| proveniencia_json | jsonb | Não / padrão | - |
| observacao | text | Não / padrão | - |

## Títulos (`titulo`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| registro_id | bigint | Sim | registro_fonte |
| valor | text | Sim | - |
| tipo | character varying | Não / padrão | - |

## Certificados (`certificado`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| registro_id | bigint | Sim | registro_fonte |
| numero | character varying | Sim | - |
| esquema | character varying | Não / padrão | - |
| papel | character varying | Não / padrão | - |
| data_emissao | date | Não / padrão | - |
| situacao | text | Não / padrão | - |

## Pessoas (`pessoa`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| fonte_id | bigint | Sim | fonte_dados |
| nome | text | Sim | - |
| observacao | text | Não / padrão | - |

## Empresas (`empresa`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| fonte_id | bigint | Sim | fonte_dados |
| nome | text | Sim | - |
| cnpj | character varying | Não / padrão | - |
| uf | character varying | Não / padrão | - |
| municipio | text | Não / padrão | - |
| observacao | text | Não / padrão | - |

## Funções de crédito (`funcao_credito`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| nome | character varying | Sim | - |
| descricao | text | Não / padrão | - |

## Créditos de pessoas (`credito_pessoa`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| registro_id | bigint | Sim | registro_fonte |
| pessoa_id | bigint | Sim | pessoa |
| funcao_id | bigint | Sim | funcao_credito |
| personagem | text | Não / padrão | - |
| evidencia | text | Não / padrão | - |

## Participações de empresas (`participacao_empresa`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| registro_id | bigint | Sim | registro_fonte |
| empresa_id | bigint | Sim | empresa |
| papel | character varying | Sim | - |
| evidencia | text | Não / padrão | - |

## Países (`pais`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| nome | character varying | Sim | - |

## Países de produção (`obra_pais`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| registro_id | bigint | Sim | registro_fonte |
| pais_id | bigint | Sim | pais |
| evidencia | text | Não / padrão | - |

## Gêneros (`genero`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| nome | character varying | Sim | - |

## Gêneros por registro (`obra_genero`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| registro_id | bigint | Sim | registro_fonte |
| genero_id | bigint | Sim | genero |

## Características técnicas (`caracteristica_tecnica`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| registro_id | bigint | Sim | registro_fonte |
| nome | character varying | Sim | - |
| valor | text | Sim | - |
| unidade | character varying | Não / padrão | - |

## Relações entre obras (`relacao_obra`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| origem_id | bigint | Sim | obra |
| destino_id | bigint | Sim | obra |
| tipo | character varying | Sim | - |
| status | character varying | Sim | - |
| evidencia_json | jsonb | Não / padrão | - |

## Decisões de integração (`decisao_integracao`)

| Campo | Tipo | Obrigatório na criação | Referência |
|---|---|---|---|
| id | bigint | Não / padrão | PK automática |
| registro_a_id | bigint | Sim | registro_fonte |
| registro_b_id | bigint | Sim | registro_fonte |
| parecer | character varying | Sim | - |
| justificativa | text | Sim | - |
| responsavel | character varying | Sim | - |
| data_decisao | timestamp with time zone | Não / padrão | - |
