# Resultado CEGO do periciar-lote no corpus v1 — 16/11/2026

Ferramenta congelada em `69e65d4` (pré-registro `cdcfed0`). Rodada única, sem nenhum ajuste antes. Não apagar.

| Medida | Valor |
|---|---|
| Arquivos | 1500 (165 adulterados, 1335 legítimos) |
| Precisão (RISCO) | **0,200** (110 certos, 439 falsos alarmes) |
| Revocação | **0,667** (110 de 165) |
| Legítimos em REVISAR | 15 (as 15 iscas do otimizador — comportamento certo) |

## O que falhou

1. **439 falsos alarmes em procurações legítimas:** o papel timbrado do escritório se repete em todos os clientes
   dele e a regra de "imagem reaproveitada" não distingue timbre de assinatura. Nenhum logotipo de banco/companhia
   gerou alarme (o teto de 50% da família funcionou), mas o timbre fica abaixo do teto.
2. **H1 acertado pelo motivo ERRADO:** as 60 procurações da fraude caíram em grupo pelo TIMBRE do escritório, não pela
   assinatura. A assinatura recortada e salva de novo (bytes diferentes) não foi reconhecida.
3. **H2 perdido (40):** extrato refeito inteiro num editor, sem versão anterior → só "produtor fora do padrão" (REVISAR).
4. **H5 perdido (15):** anacronismo de ~40 dias ficou dentro da folga de 90 dias da regra de datas.

## O que funcionou às cegas

- H3 (metadados apagados, 30/30): pego como "mesmo modelo" (todos sem metadados) + fonte e produtor fora do padrão.
- H4 (tarifa dobrada com saldo recalculado, 20/20): a versão anterior denuncia.
- Logotipos repetidos de banco e companhia: zero falso alarme.
- Iscas do otimizador: REVISAR, nenhuma acusada.
