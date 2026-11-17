# Pré-registro do teste às cegas — corpus v2

Registrado em 17/11/2026, ANTES de escrever o gerador do v2 e antes de gerar o corpus.

## Ferramenta congelada

- `periciar_lote.py` no commit `8056c38` (sha256 do arquivo começa com `6443b91809ee0ecf`).
- Nenhuma alteração antes da primeira rodada no v2. A primeira rodada é o resultado cego e não se apaga.
- Limite conhecido do desenho: quem escreve o corpus conhece a ferramenta. Para reduzir o viés, as novidades do v2
  são as que já tinham sido anunciadas como "próximo passo" ao fim do v1 (assinaturas mais variadas, JPEG, várias
  páginas) e fenômenos comuns em carteiras reais, não fraquezas escolhidas a dedo. O teste de verdade continua sendo
  um corpus feito por outra pessoa.

## O que o v2 traz de novo

Realismo (vale para legítimos e fraudes):
- assinaturas com vários traços, inclinação, espessura e tamanho variáveis (o gerador do v0/v1 era pobre);
- parte das procurações legítimas é **digitalizada**: a assinatura entra como JPEG;
- extratos e procurações com **duas páginas** em parte da carteira;
- papel timbrado e logotipos como no v1.

Fraudes (500 ações, 3 documentos cada):
- **J1** (50) a mesma assinatura reaproveitada em procurações de pessoas diferentes, como JPEG recomprimido em
  qualidade diferente a cada vez (bytes nunca iguais).
- **J2** (30) extrato de duas páginas com um lançamento inventado na página 2 por versão incremental, mesmo
  produtor do banco, saldo recalculado para fechar. 15 das ações J2 também estão em J1 (mesma operação).
- **J4** (20) extrato de duas páginas cujo saldo final (página 2) não fecha com o saldo anterior (página 1); uma versão.
- **J5** (20) comprovante refeito do zero com o produtor falsificado igual ao da companhia, mas outra fonte (Arial).
- **J3** (25) extrato que é só imagem JPEG ("print de tela"): o gabarito é INCONCLUSIVO, não adulterado.

Legítimos que podem enganar:
- **ISCA-PESSOA**: 10 pessoas com 3 ações cada; cada procuração foi assinada de verdade de novo, então as 3 assinaturas
  da mesma pessoa são parecidas, mas não iguais. Isto é legítimo (mesma pessoa, mesmo nome e CPF).
- **ISCA-OTIM** (15): extratos legítimos regravados inteiros por um otimizador, sem mudar o conteúdo.
- extratos e procurações legítimos de duas páginas; assinaturas legítimas em JPEG.

## Previsões (feitas antes de rodar)

- J1: a ferramenta não compara JPEG a olho (só bytes idênticos) → espero perder quase todo o J1.
- J2: depende de a linha do tempo comparar o conteúdo de todas as páginas; espero pegar.
- J3: espero INCONCLUSIVO (página coberta por imagem, sem texto).
- J4: espero pegar (a regra de saldo lê o texto do arquivo inteiro).
- J5: espero no máximo REVISAR (fonte fora do padrão), sem RISCO.
- ISCA-PESSOA: risco de falso alarme como "imagem reaproveitada", porque a ferramenta não confere o nome de quem assina.

## Medidas

As mesmas do v1: precisão e revocação de RISCO por arquivo, triagem (RISCO ou REVISAR) dos adulterados,
inconclusivos certos, falsos alarmes e Jaccard por grupo verdadeiro (J1, J2, J4, J5).

## Regra de leitura

Resultado cego = primeira rodada. Qualquer número depois de mexer na ferramenta é "após ajuste" e não é cego.
