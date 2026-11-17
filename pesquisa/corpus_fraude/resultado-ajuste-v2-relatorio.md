# Perícia em lote — lote

1500 arquivos examinados: INCONCLUSIVO 25, OK 1340, REVISAR 35, RISCO 100

## Padrão de cada família (aprendido do próprio lote)

- **comprovante** (500 docs): emissor habitual `SisFatura CEE 5.1`; fontes Helvetica, Arial
- **extrato** (500 docs): emissor habitual `SistemaExtrato BancoExemplo 3.2`; fontes Helvetica
- **procuracao** (500 docs): emissor habitual `EditorTexto 16.0 \(exportar PDF\)`; fontes Times-Roman, Helvetica

## Grupos entre arquivos

- **L1** (produtor_estranho_em_serie): 15 documentos 'extrato' gerados por 'OtimizadorPDF 4.0' e não pelo emissor habitual (SistemaExtrato BancoExemplo 3.2), sem versão anterior dentro: o arquivo sozinho não prova alteração — pedir os originais ao emissor. Ações: 15.
- **L2** (edicao_em_serie): 30 documentos 'extrato' emitidos por 'SistemaExtrato BancoExemplo 3.2' e alterados depois pelo mesmo programa (que se identifica como o emissor), com mudança de conteúdo entre as versões. Ações: 30.
- **L3** (imagem_reaproveitada): a mesma imagem fora do cabeçalho (50 cópias com bytes diferentes, visualmente iguais) aparece em 50 documentos 'procuracao' de 50 titulares diferentes (CPF). Ações: 50.

## Ações em mais de um grupo

- L2 + L3: 15 ações

## Medição contra o gabarito

```
{
 "contagem": {
  "vn": 1355,
  "revisar_em_legitimo": 15,
  "inconclusivo_certo": 25,
  "vp": 100,
  "adulterado_em_revisar": 20,
  "fn": 20
 },
 "precisao": 1.0,
 "revocacao": 0.833,
 "triagem_risco_ou_revisar": 1.0,
 "grupos": {
  "ISCA-OTIM": {
   "acoes": 15,
   "melhor_grupo": "L1",
   "jaccard": 1.0
  },
  "ISCA-PESSOA": {
   "acoes": 30,
   "melhor_grupo": "L3",
   "jaccard": 0.0
  },
  "J1": {
   "acoes": 50,
   "melhor_grupo": "L3",
   "jaccard": 1.0
  },
  "J2": {
   "acoes": 30,
   "melhor_grupo": "L2",
   "jaccard": 1.0
  },
  "J3": {
   "acoes": 25,
   "melhor_grupo": "L3",
   "jaccard": 0.0
  },
  "J4": {
   "acoes": 20,
   "melhor_grupo": "L3",
   "jaccard": 0.0
  },
  "J5": {
   "acoes": 20,
   "melhor_grupo": "L3",
   "jaccard": 0.0
  }
 },
 "exemplos_de_erro": {
  "falsos_alarmes": [],
  "perdidos": [
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v2/lote/acao-0014/comprovante.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v2/lote/acao-0075/comprovante.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v2/lote/acao-0092/comprovante.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v2/lote/acao-0094/comprovante.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v2/lote/acao-0137/comprovante.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v2/lote/acao-0155/comprovante.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v2/lote/acao-0170/comprovante.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v2/lote/acao-0179/comprovante.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v2/lote/acao-0208/comprovante.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v2/lote/acao-0216/comprovante.pdf"
  ]
 }
}
```

## Limites

- O laudo descreve o que os arquivos mostram; não identifica autoria de pessoas.
- Regravação sem mudança de conteúdo e produtor diferente são REVISAR, não RISCO (edição não é fraude).
- Página que é só imagem é INCONCLUSIVO: pedir o original ao emissor.
- A regra de saldo vale para extratos com 'SALDO ANTERIOR' e 'SALDO EM'; outros formatos precisam de regra própria.
- Imagem presente em mais da metade da família é tratada como logotipo/modelo do emissor e não agrupa.
- Assinatura reaproveitada conta titulares distintos pelo 1º CPF do texto; documento cujo 1º CPF não é o de quem assina precisa de regra própria.
- JPEG é comparado a olho só com o Pillow instalado; JPX, CCITT e JBIG2 só agrupam por bytes idênticos.
- A fonte é a declarada no PDF (/BaseFont), não o nome normalizado pela biblioteca de extração.
