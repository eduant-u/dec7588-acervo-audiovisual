-- Q1: Quantas obras descritas por fonte existem em cada década?
-- Uma obra presente nas duas fontes participa de ambas as séries; não somar como obras únicas.
SELECT f.nome AS fonte, (r.ano/10)*10 AS decada,
 COUNT(DISTINCT o.id) AS total_obras
FROM audiovisual.obra o
JOIN audiovisual.registro_fonte r ON r.obra_id=o.id
JOIN audiovisual.lote_importacao l ON l.id=r.lote_id
JOIN audiovisual.fonte_dados f ON f.id=l.fonte_id
WHERE r.ano IS NOT NULL
GROUP BY f.nome,(r.ano/10)*10
ORDER BY decada,fonte;

-- Q2: Quais empresas têm mais obras na amostra, por papel declarado?
-- Requerente e produtora são papéis diferentes. Nomes são literais por fonte.
SELECT e.nome AS empresa, p.papel, COUNT(DISTINCT r.obra_id) AS total_obras
FROM audiovisual.empresa e
JOIN audiovisual.participacao_empresa p ON p.empresa_id=e.id
JOIN audiovisual.registro_fonte r ON r.id=p.registro_id
JOIN audiovisual.obra o ON o.id=r.obra_id
GROUP BY e.id,e.nome,p.papel
ORDER BY total_obras DESC,empresa,p.papel
LIMIT 15;

-- Q3: Quantas obras têm CPB de cada papel, por fonte?
-- A mesma obra pode ter certificados com papéis distintos: contagens não são aditivas.
SELECT f.nome AS fonte,c.papel,COUNT(DISTINCT r.obra_id) AS total_obras
FROM audiovisual.certificado c
JOIN audiovisual.registro_fonte r ON r.id=c.registro_id
JOIN audiovisual.lote_importacao l ON l.id=r.lote_id
JOIN audiovisual.fonte_dados f ON f.id=l.fonte_id
WHERE c.esquema='CPB'
GROUP BY f.nome,c.papel
ORDER BY fonte,papel;

