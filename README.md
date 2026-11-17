# portfolio-forensics

Batch forensic examination of litigation document portfolios (PDF), evaluated with preregistered blind rounds.
This repository is the reproducibility package of the article *"Examining the portfolio, not the document: batch
forensics of litigation evidence under preregistered blind evaluation"* (under review).

Everything here is **fictitious**: generated people, banks, utilities and law firms; identity numbers with invalid
check digits; every page carries a training footer. No court, case-management system or personal data were used.
Internal notes, preregistrations and result files are in Portuguese, as they were written at the time.

## Contents

| Path | What it is |
|---|---|
| `periciar_lote.py` | the batch examination tool (per-file signals, family baselines, cross-file groups, conclusions, metrics) |
| `pesquisa/corpus_fraude/gerar.py` | corpus v0 generator (development) |
| `pesquisa/corpus_fraude/gerar_v1.py` | corpus v1 generator (blind round 1) |
| `pesquisa/corpus_fraude/gerar_v2.py` | corpus v2 generator (blind round 2; needs Pillow) |
| `pesquisa/corpus_fraude/calibrar_assinatura.py` | threshold calibration on a separate set (own seeds) |
| `pesquisa/corpus_fraude/pre-registro-v*.md` | preregistrations, committed before each blind corpus |
| `pesquisa/corpus_fraude/resultado-cego-v*.md` | blind results (first run, never overwritten) |
| `pesquisa/corpus_fraude/resultado-ajuste-v*.md` | results after adjustment (not blind) |
| `frozen/periciar_lote_v1_blind.py`, `frozen/periciar_lote_v2_blind.py` | the exact tool files used in each blind round (same SHA-256 as above) |

## Frozen tool versions

The preregistrations identify the frozen tool by the SHA-256 of `periciar_lote.py`. Commit ids in this repository
differ from the ones quoted inside the Portuguese documents (the history was filtered from a private research
repository; dates and file contents are unchanged).

| Round | Tool SHA-256 (prefix) | Commit here | Quoted in documents as |
|---|---|---|---|
| v1 blind | `7024e83577b65254` | `7adaf1d` | `69e65d4` |
| v2 blind (= v1 after adjustment) | `6443b91809ee0ecf` | `6f678d2` | `8056c38` |
| v2 after adjustment (current) | `0d6a11ffc04d54da` | `a9e959c` | `5d04077` |

Preregistration timestamps are git commit times in the author's repository; they are not externally timestamped.

## Reproducing

Requirements: Python ≥ 3.10, `pdfminer.six==20260107`, `Pillow==12.3.0`, and the `twolayers` package
(https://github.com/cleitonaugusto/twolayers, commit `787d133`, v0.19.1; during anonymous review, use the second link given in the manuscript), from which the tool uses the PDF revision
timeline and hidden-text modules.

```bash
git clone https://github.com/cleitonaugusto/twolayers && git -C twolayers checkout 787d133
python3 -m venv .venv && .venv/bin/pip install pdfminer.six==20260107 Pillow==12.3.0
export AUDITAR_MCP_SRC=$PWD/twolayers/src

# generate a corpus (deterministic: same seed, same bytes) and examine it
.venv/bin/python -I pesquisa/corpus_fraude/gerar_v2.py /tmp/v2
.venv/bin/python periciar_lote.py /tmp/v2/lote --saida /tmp/v2/laudo --gabarito /tmp/v2/gabarito.json

# repeat the v2 blind round with the frozen tool (expected: precision 1.0, recall 0.417)
.venv/bin/python frozen/periciar_lote_v2_blind.py /tmp/v2/lote --saida /tmp/v2/laudo-cego --gabarito /tmp/v2/gabarito.json
```

## License

AGPL-3.0 (see `LICENSE`). For other licensing terms, contact the author.
