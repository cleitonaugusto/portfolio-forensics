# Resultado CEGO — corpus v2 (17/11/2026)

Ferramenta congelada: `periciar_lote.py` do commit `8056c38` (sha256 `6443b91809ee0ecf…`), sem nenhuma alteração.
Pré-registro: `pre-registro-v2.md` (commit `3a14f67`). Gerador: `gerar_v2.py` (commit `99b6329`, semente 20261118,
determinístico; conferido gerando duas vezes). Corpus e laudo em `/mnt/nqf_lab/auditar-mcp/corpus-fraude/v2`.
Uma única rodada, 1500 PDFs em 19 s.

## Números

| Medida | v1 cego | **v2 cego** |
|---|---|---|
| Precisão (RISCO) | 0,200 | **1,000** (0 falsos alarmes) |
| Revocação (RISCO) | 0,667 | **0,417** (50 de 120) |
| Triagem (RISCO ou REVISAR) | 0,909 | **0,417** |
| Inconclusivos certos | — | 25 de 25 |
| REVISAR em legítimos | — | 15 (as 15 iscas do otimizador, como desenhado) |

## Por grupo, contra as previsões

| Grupo | Previsto | Aconteceu |
|---|---|---|
| J1 assinatura reaproveitada em JPEG (50) | perder quase tudo | **perdeu 50 de 50** (nem REVISAR) |
| J2 lançamento inventado na pág. 2, versão incremental (30) | pegar | pegou 30 de 30; grupo achado com Jaccard 1,0 |
| J3 extrato só imagem JPEG (25) | INCONCLUSIVO | 25 de 25 INCONCLUSIVO |
| J4 saldo não fecha entre páginas (20) | pegar | pegou 20 de 20 |
| J5 comprovante em Arial com produtor falsificado (20) | no máximo REVISAR | **OK em 20 de 20** — previsão errada (ver causa) |
| ISCA-PESSOA, mesma pessoa assina 3 vezes (30) | risco de falso alarme | 0 falsos alarmes — previsão errada, a favor |
| ISCA-OTIM (15) | REVISAR | REVISAR, grupo de triagem com Jaccard 1,0 |

## Causas (diagnóstico depois da rodada; não muda o número cego)

1. **J1 — limite já declarado no código:** a máscara de tinta só é calculada para imagem não comprimida; JPEG
   (DCTDecode) só agrupa com bytes idênticos. Em carteira real, procuração digitalizada é a regra, não a exceção:
   este é o defeito mais caro da ferramenta hoje.
2. **J5 — defeito que eu não conhecia:** os 20 arquivos têm `/BaseFont /Arial`, mas o pdfminer (20260107) trata Arial
   como apelido de Helvetica (`fontmetrics.py`, `FONT_METRICS["Arial"] = FONT_METRICS["Helvetica"]`) e devolve o
   nome "Helvetica". A ferramenta nunca vê a fonte declarada. Lição para o laudo: o nome da fonte deve
   ser lido do dicionário do PDF, não do que a biblioteca de extração "normaliza".
3. **ISCA-PESSOA sem falso alarme:** as assinaturas variadas do v2 da mesma pessoa ficaram abaixo do limiar de 0,80.
   Bom para a precisão, mas é também um aviso: o limiar foi calibrado com cópias quase idênticas; não se sabe ainda
   quão longe fica de uma fraude que redesenha a assinatura.
4. **Precisão 1,0 não é mérito sozinho:** a ferramenta só acusou o que tem rastro forte (versão anterior, saldo).
   Ela ficou conservadora; a revocação caiu de 0,667 para 0,417 porque o v2 trouxe dois tipos de fraude que ela não lê.

## Leitura honesta

- O que é estrutural (versões, saldo, página-imagem) generalizou bem para duas páginas e para dados novos.
- O que é visual (assinatura) e tipográfico (fonte) não generalizou: um por limite declarado, outro por defeito
  escondido na biblioteca.
- Próximos ajustes candidatos (fora do resultado cego): decodificar JPEG para a máscara de tinta; ler a fonte do
  dicionário `/BaseFont`; conferir o nome do outorgante antes de chamar duas assinaturas parecidas de reaproveitamento.
