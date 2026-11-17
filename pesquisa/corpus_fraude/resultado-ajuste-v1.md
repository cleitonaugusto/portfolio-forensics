# periciar-lote APÓS AJUSTE (não cego) — 16/11/2026

O resultado cego continua sendo o de `resultado-cego-v1.md` (precisão 0,200; revocação 0,667). Estes números vêm
DEPOIS de mexer na ferramenta olhando as falhas do v1 — servem para ver se a correção funcionou, não como taxa de erro.

## O que mudou

1. Imagem no cabeçalho (15% superiores da página) = timbre/logotipo do emissor, fora da busca de reaproveitamento.
2. Comparação visual de imagens por máscara de tinta com tolerância a deslocamento; limiar 0,80 escolhido num conjunto
   de CALIBRAÇÃO separado (`calibrar_assinatura.py`, semente própria): 0% de cópias perdidas, 0,10% de confusão.
3. Lançamento (linha que começa com data) não pode ser posterior à criação do arquivo.
4. Grupo "produtor estranho em série" (REVISAR): vários documentos feitos fora do emissor, sem versão anterior —
   triagem para pedir os originais, não acusação.

## Números

| | v1 cego | v1 após ajuste | v0 após ajuste (regressão) |
|---|---|---|---|
| Precisão | 0,200 | 0,893 | 0,925 |
| Revocação (RISCO) | 0,667 | 0,758 | 1,000 |
| Triagem (RISCO ou REVISAR) | 0,909 | 1,000 | 1,000 |
| Falsos alarmes | 439 | 15 | 15 |
| Grupo H1 (assinatura recodificada) | pego pelo timbre (motivo errado) | pego pela assinatura, Jaccard 1,0 | — |

## O que ainda falha

- 15 falsos alarmes em cada corpus = 5 trios de assinaturas legítimas parecidas (a confusão de 0,1% por par vira
  grupos pequenos num lote de 500). Hipótese a testar num v2 cego: tratar grupo só "visualmente igual" e pequeno como
  REVISAR (comparar a olho) em vez de RISCO.
- H2 (extrato refeito inteiro num editor) fica em REVISAR: sem versão anterior, o arquivo sozinho não prova a fraude.
  Isso é limite do método, não defeito: o laudo pede o original ao banco.
- O gerador de assinaturas fictícias tem pouca variedade (curvas parecidas); assinaturas reais variam mais.
