# Perícia em lote — lote

1500 arquivos examinados: OK 1305, REVISAR 55, RISCO 140

## Padrão de cada família (aprendido do próprio lote)

- **comprovante** (500 docs): emissor habitual `SisFatura CEE 5.1`; fontes Helvetica, Times-Roman
- **extrato** (500 docs): emissor habitual `SistemaExtrato BancoExemplo 3.2`; fontes Helvetica
- **procuracao** (500 docs): emissor habitual `EditorTexto 16.0 \(exportar PDF\)`; fontes Times-Roman, Helvetica

## Grupos entre arquivos

- **L1** (mesmo_modelo): 30 documentos 'comprovante' com o mesmo produtor, autor e data de criação, diferente do emissor habitual (SisFatura CEE 5.1). Ações: 30.
- **L2** (produtor_estranho_em_serie): 40 documentos 'extrato' gerados por 'PDF-Online-Editor 2.1' e não pelo emissor habitual (SistemaExtrato BancoExemplo 3.2), sem versão anterior dentro: o arquivo sozinho não prova alteração — pedir os originais ao emissor. Ações: 40.
- **L3** (produtor_estranho_em_serie): 15 documentos 'extrato' gerados por 'OtimizadorPDF 4.0' e não pelo emissor habitual (SistemaExtrato BancoExemplo 3.2), sem versão anterior dentro: o arquivo sozinho não prova alteração — pedir os originais ao emissor. Ações: 15.
- **L4** (edicao_em_serie): 20 documentos 'extrato' emitidos por 'SistemaExtrato BancoExemplo 3.2' e alterados depois em 'SistemaExtrato BancoExemplo 3.2', com mudança de conteúdo. Ações: 20.
- **L5** (imagem_reaproveitada): a mesma imagem fora do cabeçalho (60 cópias com bytes diferentes, visualmente iguais) aparece em 60 documentos 'procuracao' de ações diferentes. Ações: 60.
- **L6** (imagem_reaproveitada): a mesma imagem fora do cabeçalho (3 cópias com bytes diferentes, visualmente iguais) aparece em 3 documentos 'procuracao' de ações diferentes. Ações: 3.
- **L7** (imagem_reaproveitada): a mesma imagem fora do cabeçalho (3 cópias com bytes diferentes, visualmente iguais) aparece em 3 documentos 'procuracao' de ações diferentes. Ações: 3.
- **L8** (imagem_reaproveitada): a mesma imagem fora do cabeçalho (3 cópias com bytes diferentes, visualmente iguais) aparece em 3 documentos 'procuracao' de ações diferentes. Ações: 3.
- **L9** (imagem_reaproveitada): a mesma imagem fora do cabeçalho (3 cópias com bytes diferentes, visualmente iguais) aparece em 3 documentos 'procuracao' de ações diferentes. Ações: 3.
- **L10** (imagem_reaproveitada): a mesma imagem fora do cabeçalho (3 cópias com bytes diferentes, visualmente iguais) aparece em 3 documentos 'procuracao' de ações diferentes. Ações: 3.

## Ações em mais de um grupo

- L2 + L5: 20 ações
- L1 + L8: 1 ações
- L1 + L10: 1 ações
- L2 + L6: 1 ações

## Medição contra o gabarito

```
{
 "contagem": {
  "vn": 1320,
  "revisar_em_legitimo": 15,
  "vp": 125,
  "adulterado_em_revisar": 40,
  "fn": 40,
  "fp": 15
 },
 "precisao": 0.893,
 "revocacao": 0.758,
 "triagem_risco_ou_revisar": 1.0,
 "grupos": {
  "H1": {
   "acoes": 60,
   "melhor_grupo": "L5",
   "jaccard": 1.0
  },
  "H2": {
   "acoes": 40,
   "melhor_grupo": "L2",
   "jaccard": 1.0
  },
  "H3": {
   "acoes": 30,
   "melhor_grupo": "L1",
   "jaccard": 1.0
  },
  "H4": {
   "acoes": 20,
   "melhor_grupo": "L4",
   "jaccard": 1.0
  },
  "H5": {
   "acoes": 15,
   "melhor_grupo": "L9",
   "jaccard": 0.059
  },
  "ISCA": {
   "acoes": 15,
   "melhor_grupo": "L3",
   "jaccard": 1.0
  }
 },
 "exemplos_de_erro": {
  "falsos_alarmes": [
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0039/procuracao.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0056/procuracao.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0059/procuracao.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0118/procuracao.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0123/procuracao.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0171/procuracao.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0181/procuracao.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0194/procuracao.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0270/procuracao.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0304/procuracao.pdf"
  ],
  "perdidos": [
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0006/extrato.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0013/extrato.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0032/extrato.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0038/extrato.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0039/extrato.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0073/extrato.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0075/extrato.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0086/extrato.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0104/extrato.pdf",
   "/mnt/nqf_lab/auditar-mcp/corpus-fraude/v1/lote/acao-0111/extrato.pdf"
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
