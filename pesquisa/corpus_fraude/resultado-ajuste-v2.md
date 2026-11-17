# Após ajuste (NÃO cego) — depois do resultado cego do v2 (17/11/2026)

O número cego do v2 continua sendo o de `resultado-cego-v2.md` (precisão 1,0, revocação 0,417). Tudo abaixo foi
medido depois de mexer na ferramenta, sabendo onde ela errou.

## O que mudou no `periciar_lote.py`

1. **JPEG comparado a olho:** o JPEG (DCTDecode) é decodificado com o Pillow e entra na máscara de tinta. Sem o
   Pillow, volta ao limite declarado (só bytes idênticos). Pillow 12.3.0 instalado no venv do kit.
2. **Fonte declarada:** o nome da fonte vem do `/BaseFont` do PDF, não do nome normalizado pelo pdfminer
   (que transformava Arial em Helvetica).
3. **Titular por CPF:** o agrupamento de assinatura reaproveitada conta titulares distintos (1º CPF do texto, guardado
   só como hash); a mesma pessoa assinando de novo não forma grupo sozinha.

## Calibração (conjunto separado, `calibrar_assinatura.py`, sementes 9_500_000+k e 5_550_002)

Limiar mantido em 0,80. No estilo v2 com JPEG: perde 4,2% dos pares de cópias recomprimidas, junta 11,3% dos pares
"mesma pessoa assinando de novo" (por isso a regra do CPF) e confunde 0,00% de pessoas diferentes.

## Números

| Corpus | Precisão | Revocação | Triagem | Falsos alarmes |
|---|---|---|---|---|
| v2 cego | 1,000 | 0,417 | 0,417 | 0 |
| **v2 após ajuste** | **1,000** | **0,833** | **1,000** | 0 |
| v1 após ajuste (regressão) | 0,893 | 0,758 | 1,000 | 15 (igual ao antes) |
| v0 após ajuste (regressão) | 0,925 | 1,000 | 1,000 | 15 (igual ao antes) |

No v2: J1 50/50 em RISCO (grupo achado com Jaccard 1,0); J5 20/20 em REVISAR (só a fonte denuncia; produtor
falsificado e uma versão só: o arquivo sozinho não prova, pedir o original); J2, J4 e J3 como no cego.

## Limites que continuam

- J5 fica em REVISAR, e é o certo: fonte diferente é indício, não prova.
- O efeito isolado da regra do CPF não foi medido no v2 (as assinaturas da ISCA-PESSOA já não formavam grupo sem ela);
  a calibração mostra que ela é necessária com assinaturas mais parecidas.
- Os 15 falsos alarmes do v0/v1 (trios de assinaturas legítimas do gerador antigo, de pessoas diferentes) continuam.
- Corpus e ferramenta continuam do mesmo autor. O próximo nível de prova é um corpus feito por outra pessoa.
