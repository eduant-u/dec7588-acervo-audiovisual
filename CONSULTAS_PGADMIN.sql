-- 1. Ver as 19 tabelas do esquema
-- information_schema mostra informações sobre a estrutura do banco.
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'audiovisual'
ORDER BY table_name;

-- 2. Ver as últimas obras cadastradas
-- DESC coloca os maiores IDs primeiro. LIMIT retorna até 10 linhas.
SELECT *
FROM audiovisual.obra
ORDER BY id DESC
LIMIT 10;

-- 3. Conferir as quantidades de obras e registros
-- COUNT(*) conta as linhas de cada tabela.
-- Uma obra pode estar ligada a vários registros de fontes diferentes.
SELECT COUNT(*) AS obras FROM audiovisual.obra;
SELECT COUNT(*) AS registros FROM audiovisual.registro_fonte;

-- 4. Consultar obras com CPB por fonte e papel
-- Os JOINs ligam certificado, registro, lote e fonte.
-- O filtro mantém apenas certificados do esquema CPB.
-- GROUP BY separa os resultados por fonte e papel do certificado.
-- COUNT(DISTINCT) evita repetir a obra dentro de cada grupo.
-- A mesma obra pode aparecer em grupos diferentes.
SELECT f.nome AS fonte, c.papel,
       COUNT(DISTINCT r.obra_id) AS total_obras
FROM audiovisual.certificado c
JOIN audiovisual.registro_fonte r ON r.id = c.registro_id
JOIN audiovisual.lote_importacao l ON l.id = r.lote_id
JOIN audiovisual.fonte_dados f ON f.id = l.fonte_id
WHERE c.esquema = 'CPB'
GROUP BY f.nome, c.papel
ORDER BY fonte, papel;

-- 5. ABC, BRASIL nas duas fontes
-- Cada linha é um registro de origem. obra_id mostra o cadastro em comum.
-- A duração continua sendo a que cada fonte declarou.
SELECT r.id AS registro_id, r.obra_id, o.titulo_referencia AS obra,
       f.nome AS fonte, r.duracao_minutos
FROM audiovisual.registro_fonte r
JOIN audiovisual.obra o ON o.id = r.obra_id
JOIN audiovisual.lote_importacao l ON l.id = r.lote_id
JOIN audiovisual.fonte_dados f ON f.id = l.fonte_id
WHERE r.obra_id = 1
ORDER BY r.id;
