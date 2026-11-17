# Pré-registro do teste às cegas — corpus v1

Registrado em 16/11/2026, ANTES de gerar o corpus v1.

## Ferramenta congelada

- `periciar_lote.py` no commit `69e65d4` (sha256 do arquivo começa com `7024e83577b65254`).
- Nenhuma alteração na ferramenta antes da primeira rodada no v1. A primeira rodada é o resultado cego e não se
  apaga, mesmo que seja ruim.

## O que o v1 traz de novo (a ferramenta não foi feita para isto)

Fraudes:
- **H1** assinatura reaproveitada, mas recortada e salva de novo: mesma imagem a olho, bytes diferentes.
- **H2** extrato com lançamento inventado, refeito inteiro num editor: uma versão só, sem a versão do banco dentro.
- **H3** comprovante alterado com os metadados apagados (antiperícia simples).
- **H4** extrato alterado por versão incremental, trocando só dígitos na mesma fonte e com o saldo ajustado para fechar.
- **H5** extrato com anacronismo sutil: criado ~40 dias antes do fim do período que mostra.
- Parte das ações tem H1 e H2 juntas (mesma operação).

Legítimos que podem enganar:
- logotipo do banco e da companhia de energia em todos os documentos;
- papel timbrado do escritório (imagem) repetido nas procurações de todos os clientes de um mesmo escritório;
- extratos legítimos "otimizados" (regravados inteiros por um compressor, sem mudar o conteúdo);
- datas de emissão realistas (variam por documento).

## Medidas

Por arquivo: precisão e revocação de RISCO contra o gabarito; falso alarme em legítimo; inconclusivos.
Por grupo: Jaccard das ações de cada grupo verdadeiro de operação (H1, H2, H3) contra o melhor grupo achado.

## Regra de leitura

Resultado cego = primeira rodada. Qualquer número depois de mexer na ferramenta é "após ajuste" e não é cego.
