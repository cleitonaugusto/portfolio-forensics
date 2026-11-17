# Resultado do periciar-lote no corpus v0 (16/11/2026)

ATENÇÃO: corpus e ferramenta feitos pelo mesmo autor, conhecendo os sinais — este número é teste de
funcionamento, NÃO taxa de erro publicável. Medida válida exige corpus v1 às cegas (variações que a ferramenta não conhece).

1ª rodada: precisão 0,186, revocação 0,568 (3 defeitos: data futura legítima, tipo da imagem mal lido, edição tratada como modelo).
2ª rodada (após correção):

## Grupos entre arquivos

- **L1** (mesmo_modelo): 50 documentos 'comprovante' com o mesmo produtor, autor e data de criação, diferente do emissor habitual (SisFatura CEE 5.1). Ações: 50.
- **L2** (edicao_em_serie): 40 documentos 'extrato' emitidos por 'SistemaExtrato BancoExemplo 3.2' e alterados depois em 'PDF-Online-Editor 2.1', com mudança de conteúdo. Ações: 40.
- **L3** (imagem_reaproveitada): a mesma imagem (bytes idênticos) aparece em 80 documentos 'procuracao' de ações diferentes. Ações: 80.

## Ações em mais de um grupo

- L2 + L3: 20 ações

## Medição contra o gabarito

```
{
 "contagem": {
  "vn": 1300,
  "revisar_em_legitimo": 10,
  "vp": 185,
  "inconclusivo_certo": 15
 },
 "precisao": 1.0,
 "revocacao": 1.0,
 "grupos": {
  "G1": {
   "acoes": 80,
   "melhor_grupo": "L3",
   "jaccard": 1.0
  },
  "G2": {
   "acoes": 50,
   "melhor_grupo": "L1",
   "jaccard": 1.0
  },
  "G3": {
   "acoes": 40,
   "melhor_grupo": "L2",
   "jaccard": 1.0
  },
  "G4": {
   "acoes": 15,
   "melhor_grupo": "L3",
   "jaccard": 0.0
  },
  "G5": {
   "acoes": 15,
   "melhor_grupo": "L3",
   "jaccard": 0.0
  },
  "ISCA": {
   "acoes": 10,
   "melhor_grupo": "L3",
   "jaccard": 0.0
  }
 },
 "exemplos_de_erro": {
  "falsos_alarmes": [],
  "perdidos": []
 }
}
```

## Limites

- O laudo descreve o que os arquivos mostram; não identifica autoria de pessoas.
- Regravação sem mudança de conteúdo e produtor diferente são REVISAR, não RISCO (edição não é fraude).
- Página que é só imagem é INCONCLUSIVO: pedir o original ao emissor.
- A regra de saldo vale para extratos com 'SALDO ANTERIOR' e 'SALDO EM'; outros formatos precisam de regra própria.
- Imagem presente em mais da metade da família é tratada como logotipo/modelo do emissor e não agrupa.
