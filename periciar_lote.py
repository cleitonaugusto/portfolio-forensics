"""periciar-lote — perícia documental de uma carteira inteira de processos (PDF), com agrupamento entre arquivos.

Uso:
    python3 periciar_lote.py <pasta_do_lote> [--saida DIR] [--gabarito gabarito.json] [--processos N]

Organização esperada (v0): <pasta>/<acao>/<tipo>.pdf — o nome do arquivo sem extensão é a FAMÍLIA do documento
(procuracao, comprovante, extrato...). Cada família tem o seu "padrão" (produtor dominante, fontes), aprendido do
próprio lote: o que foge do padrão vira sinal, nunca acusação sozinho.

Dois níveis:
1. Exame individual: versões anteriores com conteúdo diferente, texto escondido, produtor trocado entre versões,
   documento criado antes das datas que contém, ordem cronológica quebrada, saldo que não fecha (regra de exemplo
   para extratos), fonte fora do padrão da família, página-imagem (inconclusivo).
2. Entre arquivos: a mesma imagem em vários documentos (assinatura/carimbo reaproveitado), o mesmo modelo
   (produtor+autor+data de criação idênticos fora do padrão), a mesma edição em série; e as ações que caem em
   mais de um grupo.

O laudo descreve o que os ARQUIVOS mostram. Não rotula pessoas nem escritórios.
"""

import argparse
import collections
import hashlib
import json
import os
import re
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.environ.get("AUDITAR_MCP_SRC", str(Path.home() / "kit-auditoria-mcp" / "src")))
from twolayers import linha_do_tempo, peca  # noqa: E402

RE_DATA = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
RE_VALOR = re.compile(r"(-?)R\$\s*([\d.]+,\d{2})")
RE_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
MIN_GRUPO = 3            # menor grupo entre arquivos que vale reportar
TETO_COMUM = 0.5         # imagem em mais da metade da família = logotipo/modelo do emissor, não reaproveitamento
FOLGA_DATA = 90          # dias: datas no texto até aqui depois da criação são vencimento/prazo, não anacronismo
FAIXA_CABECALHO = 0.15   # imagem cujo topo está nos 15% superiores da página = timbre/logotipo (material do emissor)
SEMELHANCA_MIN = 0.80    # sobreposição mínima das máscaras de tinta para "a mesma imagem a olho" (calibrado à parte)


# ------------------------------------------------------------------------------------------- exame individual
def _valor(sinal: str, numero: str) -> int:
    v = int(numero.replace(".", "").replace(",", ""))
    return -v if sinal else v


def _ler_paginas(caminho: Path) -> dict:
    """Fontes por linha, imagens (hash do conteúdo decodificado) e cobertura de imagem, via pdfminer."""
    from pdfminer.converter import PDFPageAggregator
    from pdfminer.layout import LAParams, LTChar, LTImage, LTFigure, LTTextLine, LTTextBox
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage
    from pdfminer.pdftypes import resolve1
    from pdfminer.psparser import literal_name

    class _FonteDeclarada(PDFResourceManager):
        """O pdfminer troca o nome de fontes 'equivalentes' (Arial vira Helvetica, pelas métricas). Para a perícia
        vale o nome declarado no dicionário da fonte (/BaseFont), que é o que o programa gerador escreveu."""

        def get_font(self, objid, spec):
            fonte = super().get_font(objid, spec)
            bf = resolve1(spec.get("BaseFont")) if hasattr(spec, "get") else None
            if bf is not None:
                fonte.fontname = literal_name(bf) if not isinstance(bf, bytes) else bf.decode("latin-1")
            return fonte

    linhas, imagens, cabecalho, area_img, area_pag = [], {}, set(), 0.0, 0.0
    rm = _FonteDeclarada()
    dev = PDFPageAggregator(rm, laparams=LAParams())
    interp = PDFPageInterpreter(rm, dev)

    def _imagens(el, altura):
        for filho in (el if isinstance(el, LTFigure) else []):
            yield from _imagens(filho, altura)
        if isinstance(el, LTImage):
            dados = el.stream.get_data()
            h = hashlib.sha256(dados).hexdigest()
            imagens[h] = _hash_perceptual(el.stream, dados)
            if el.y1 >= altura * (1 - FAIXA_CABECALHO):  # faixa superior: timbre/logotipo do emissor
                cabecalho.add(h)

    with open(caminho, "rb") as f:
        for pagina in PDFPage.get_pages(f):
            x0, y0, x1, y1 = pagina.mediabox
            area_pag += (x1 - x0) * (y1 - y0)
            interp.process_page(pagina)
            for el in dev.get_result():
                if isinstance(el, (LTImage, LTFigure)):
                    area_img = max(area_img, el.width * el.height)
                    list(_imagens(el, y1 - y0))
                if isinstance(el, LTTextBox):
                    for ln in el:
                        if isinstance(ln, LTTextLine):
                            fontes = collections.Counter(c.fontname for c in ln if isinstance(c, LTChar))
                            if fontes:
                                linhas.append({"texto": ln.get_text().strip(), "fonte": fontes.most_common(1)[0][0],
                                               "tam": round(max(c.size for c in ln if isinstance(c, LTChar)), 1)})
    return {"linhas": linhas, "imagens": imagens, "cabecalho": sorted(cabecalho),
            "cobertura_imagem": round(area_img / area_pag, 2) if area_pag else 0}


GRADE_TINTA = (64, 24)   # colunas x linhas da máscara de tinta
FOLGA_LINHA = 4          # bits vazios no fim de cada linha da máscara, para deslocar sem "vazar" para a linha vizinha
DESLOC_MAX = 2           # células de deslocamento toleradas na comparação


def _hash_perceptual(stream, dados: bytes) -> str | None:
    """Máscara de tinta: a imagem é reduzida a uma grade 64x24 e cada célula vira 1 se tem traço escuro (<128).
    Feita para traço fino sobre fundo claro (assinatura, rubrica, carimbo). A comparação (_semelhanca) engrossa o
    traço e procura a melhor sobreposição com deslocamento, para reconhecer a mesma assinatura recortada de novo.
    Imagens em cinza ou RGB; JPEG (digitalização) é decodificado com o Pillow. Sem o Pillow, ou em JPX/CCITT/JBIG2,
    devolve None e a imagem só agrupa por bytes idênticos (limite declarado)."""
    w, h = stream.attrs.get("Width"), stream.attrs.get("Height")
    try:
        w, h = int(w), int(h)
    except (TypeError, ValueError):
        return None
    if dados[:2] == b"\xff\xd8":  # o pdfminer entrega o JPEG (DCTDecode) ainda codificado
        try:
            import io
            from PIL import Image
            img = Image.open(io.BytesIO(dados)).convert("L")
        except Exception:  # sem Pillow ou JPEG ruim: fica no limite declarado
            return None
        w, h, dados = img.width, img.height, img.tobytes()
    canais = len(dados) // (w * h) if w and h else 0
    if canais not in (1, 3) or len(dados) != w * h * canais:
        return None
    gx, gy = GRADE_TINTA
    celulas = [0] * (gx * gy)
    for y in range(h):
        cy = min(gy - 1, y * gy // h)
        for x in range(w):
            i = (y * w + x) * canais
            v = dados[i] if canais == 1 else (dados[i] + dados[i + 1] + dados[i + 2]) // 3
            if v < 128:
                celulas[cy * gx + min(gx - 1, x * gx // w)] += 1
    largura = gx + FOLGA_LINHA
    v = 0
    for cy in range(gy):
        for cx in range(gx):
            if celulas[cy * gx + cx]:
                v |= 1 << (cy * largura + cx + FOLGA_LINHA // 2)
    return f"{v:x}"


def _engrossar(m: int) -> int:
    largura = GRADE_TINTA[0] + FOLGA_LINHA
    m |= (m << 1) | (m >> 1)
    return m | (m << largura) | (m >> largura)


def _semelhanca(a: str, b: str) -> float:
    """Maior sobreposição (interseção/união) entre as máscaras engrossadas, deslocando b até DESLOC_MAX células."""
    largura = GRADE_TINTA[0] + FOLGA_LINHA
    ma, mb = _engrossar(int(a, 16)), _engrossar(int(b, 16))
    ca, cb = bin(ma).count("1"), bin(mb).count("1")
    if not ca or not cb or min(ca, cb) / max(ca, cb) < 0.6:
        return 0.0
    melhor = 0.0
    for dy in range(-DESLOC_MAX, DESLOC_MAX + 1):
        for dx in range(-DESLOC_MAX, DESLOC_MAX + 1):
            s = dy * largura + dx
            mbs = mb << s if s >= 0 else mb >> -s
            melhor = max(melhor, bin(ma & mbs).count("1") / bin(ma | mbs).count("1"))
    return melhor


def _data_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s[:19])
    except ValueError:
        return None


def examinar(caminho: str) -> dict:
    """Exame de UM arquivo. Roda em processo separado; não depende do resto do lote."""
    p = Path(caminho)
    dados = p.read_bytes()
    r = {"arquivo": caminho, "sha256": hashlib.sha256(dados).hexdigest(), "sinais": {}, "erro": None}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            lt = linha_do_tempo.pdf(p, Path(tmp))
        rev = lt["revisoes"]
        primeira, ultima = rev[0]["info"], rev[-1]["info"]
        r["versoes"] = len(rev)
        r["meta"] = {"produtor": ultima.get("Producer"), "produtor_original": primeira.get("Producer"),
                     "autor": ultima.get("Author"), "criado": ultima.get("CreationDate"),
                     "modificado": ultima.get("ModDate")}
        mudancas = [l for v in rev[1:] for l in v.get("mudou_em_relacao_a_anterior", [])]
        if mudancas:
            r["sinais"]["conteudo_mudou_entre_versoes"] = mudancas[:12]
        elif len(rev) > 1:
            r["sinais"]["regravado_sem_mudar_conteudo"] = len(rev)
        if primeira.get("Producer") and ultima.get("Producer") and primeira["Producer"] != ultima["Producer"]:
            r["sinais"]["produtor_trocado_entre_versoes"] = [primeira["Producer"], ultima["Producer"]]

        pag = _ler_paginas(p)
        r["fontes_linhas"] = collections.Counter(l["fonte"] for l in pag["linhas"])
        # só imagens fora do cabeçalho entram na busca de reaproveitamento (assinatura, carimbo, rubrica)
        r["imagens"] = {h: ph for h, ph in pag["imagens"].items() if h not in pag["cabecalho"]}
        r["imagens_cabecalho"] = pag["cabecalho"]
        texto = "\n".join(l["texto"] for l in pag["linhas"])
        palavras = len(texto.split())
        # titular = 1º CPF do texto, guardado só como hash: duas assinaturas parecidas da MESMA pessoa não são
        # reaproveitamento (a pessoa assinou de novo); o laudo não precisa do CPF em claro
        cpf = RE_CPF.search(texto)
        r["titular"] = hashlib.sha256(re.sub(r"\D", "", cpf.group()).encode()).hexdigest()[:16] if cpf else None
        if pag["cobertura_imagem"] >= 0.9 and palavras < 40:
            r["sinais"]["pagina_e_imagem"] = {"cobertura": pag["cobertura_imagem"], "palavras": palavras}

        ocultos = peca.ocultos_relevantes(peca.extrair_pdf(p))
        if ocultos:
            r["sinais"]["texto_escondido"] = [f"{t.motivo}: {t.texto.strip()[:90]}" for t in ocultos][:5]

        criado = _data_iso(r["meta"]["criado"])
        datas = []
        for d, m, a in RE_DATA.findall(texto):
            try:
                datas.append(datetime(int(a), int(m), int(d)))
            except ValueError:
                pass
        # vencimento e prazo são datas futuras legítimas: só conta o que passa de FOLGA_DATA dias da criação
        if criado and datas and (max(datas) - criado).days > FOLGA_DATA:
            r["sinais"]["criado_antes_das_datas_do_texto"] = {"criado": criado.date().isoformat(),
                                                             "maior_data_no_texto": max(datas).date().isoformat()}
        # lançamentos: linhas que começam com data
        lanc = []
        for l in pag["linhas"]:
            m = RE_DATA.match(l["texto"])
            v = RE_VALOR.findall(l["texto"])
            if m and v:
                lanc.append((datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))), _valor(*v[-1])))
        if len(lanc) >= 3 and any(b[0] < a[0] for a, b in zip(lanc, lanc[1:])):
            r["sinais"]["ordem_cronologica_quebrada"] = True
        # lançamento é fato passado: não pode ser posterior à criação do arquivo (sem folga, além de 1 dia de fuso)
        if criado and lanc and (max(d for d, _ in lanc) - criado).days >= 1 \
                and "criado_antes_das_datas_do_texto" not in r["sinais"]:
            r["sinais"]["criado_antes_das_datas_do_texto"] = {"criado": criado.date().isoformat(),
                                                             "lancamento_mais_recente": max(d for d, _ in lanc).date().isoformat()}
        # regra de exemplo para extratos: saldo anterior + lançamentos = saldo final
        ant = [l for l in pag["linhas"] if "SALDO ANTERIOR" in l["texto"].upper()]
        fim = [l for l in pag["linhas"] if l["texto"].upper().startswith("SALDO EM")]
        if ant and fim and lanc:
            va, vf = RE_VALOR.findall(ant[0]["texto"]), RE_VALOR.findall(fim[-1]["texto"])
            if va and vf:
                esperado = _valor(*va[-1]) + sum(v for _, v in lanc)
                if esperado != _valor(*vf[-1]):
                    r["sinais"]["saldo_nao_fecha"] = {"esperado_centavos": esperado, "informado_centavos": _valor(*vf[-1])}
    except Exception as e:  # um arquivo ruim não derruba o lote
        r["erro"] = f"{type(e).__name__}: {e}"
    r["fontes_linhas"] = dict(r.get("fontes_linhas", {}))
    return r


# ------------------------------------------------------------------------------------------- entre arquivos
def _familia(caminho: str) -> str:
    return Path(caminho).stem.lower()


def _acao(caminho: str, raiz: Path) -> str:
    rel = Path(caminho).relative_to(raiz)
    return rel.parts[0] if len(rel.parts) > 1 else rel.stem


def agrupar(exames: list[dict], raiz: Path) -> tuple[list[dict], dict]:
    por_familia = collections.defaultdict(list)
    for e in exames:
        if not e["erro"]:
            por_familia[_familia(e["arquivo"])].append(e)
    padrao, grupos = {}, []
    for fam, docs in por_familia.items():
        prod = collections.Counter(d["meta"]["produtor"] for d in docs).most_common(1)[0][0]
        fontes_dom = collections.Counter()
        for d in docs:
            fontes_dom.update(d["fontes_linhas"])
        padrao[fam] = {"produtor_dominante": prod, "documentos": len(docs),
                       "fontes": [f for f, _ in fontes_dom.most_common()]}
        # fonte fora do padrão: a fonte da linha aparece em menos de 10% dos documentos da família
        presenca = collections.Counter(f for d in docs for f in d["fontes_linhas"])
        for d in docs:
            raras = [f for f in d["fontes_linhas"] if presenca[f] / len(docs) < 0.10]
            if raras:
                d["sinais"]["fonte_fora_do_padrao_da_familia"] = raras
            if d["meta"]["produtor"] != prod:
                d["sinais"]["produtor_fora_do_padrao_da_familia"] = d["meta"]["produtor"]
        # mesma imagem (idêntica ou visualmente igual) fora do cabeçalho em vários documentos
        # refs: [máscara representante ou None, documentos, variantes de bytes, sha representante]
        refs: list[list] = []
        por_byte = collections.defaultdict(list)
        for d in docs:
            for h, ph in d["imagens"].items():
                por_byte[(h, ph)].append(d)
        for (h, ph), ds in por_byte.items():
            if ph:
                alvo = next((rf for rf in refs if rf[0] and _semelhanca(rf[0], ph) >= SEMELHANCA_MIN), None)
            else:  # imagem que não dá para comparar a olho: só bytes idênticos
                alvo = next((rf for rf in refs if rf[0] is None and rf[3] == h), None)
            if alvo:
                alvo[1].extend(ds)
                alvo[2].add(h)
            else:
                refs.append([ph, list(ds), {h}, h])
        for _, ds, variantes, chave in refs:
            ds = list({id(x): x for x in ds}.values())
            pessoas = {x.get("titular") or id(x) for x in ds}  # sem CPF no texto, cada documento conta como uma pessoa
            if MIN_GRUPO <= len(pessoas) and len(ds) <= TETO_COMUM * len(docs):
                modo = "bytes idênticos" if len(variantes) == 1 else f"{len(variantes)} cópias com bytes diferentes, visualmente iguais"
                grupos.append({"tipo": "imagem_reaproveitada", "familia": fam, "chave": chave[:16], "docs": ds,
                               "leitura": f"a mesma imagem fora do cabeçalho ({modo}) aparece em {len(ds)} "
                                          f"documentos '{fam}' de {len(pessoas)} titulares diferentes (CPF)"})
        # produtor estranho em série (sem prova de alteração): triagem para pedir os originais ao emissor
        por_estranho = collections.defaultdict(list)
        for d in docs:
            if d["meta"]["produtor"] not in (prod, None) and d["versoes"] == 1 and "pagina_e_imagem" not in d["sinais"]:
                por_estranho[d["meta"]["produtor"]].append(d)
        for k, ds in por_estranho.items():
            if len(ds) >= MIN_GRUPO:
                grupos.append({"tipo": "produtor_estranho_em_serie", "familia": fam, "chave": k, "docs": ds,
                               "leitura": f"{len(ds)} documentos '{fam}' gerados por '{k}' e não pelo emissor habitual "
                                          f"({prod}), sem versão anterior dentro: o arquivo sozinho não prova "
                                          f"alteração — pedir os originais ao emissor"})
        # mesmo modelo: produtor+autor+data de criação idênticos, em documentos que JÁ NASCERAM fora do emissor
        # habitual (o editado depois guarda a data de criação do original e não é modelo)
        por_modelo = collections.defaultdict(list)
        for d in docs:
            m = d["meta"]
            if m["produtor_original"] != prod and "pagina_e_imagem" not in d["sinais"]:
                por_modelo[(m["produtor"], m["autor"], m["criado"])].append(d)
        for k, ds in por_modelo.items():
            if len(ds) >= MIN_GRUPO:
                grupos.append({"tipo": "mesmo_modelo", "familia": fam, "chave": " | ".join(map(str, k)), "docs": ds,
                               "leitura": f"{len(ds)} documentos '{fam}' com o mesmo produtor, autor e data de "
                                          f"criação, diferente do emissor habitual ({prod})"})
        # mesma edição em série: conteúdo mudou entre versões e o mesmo produtor fez a última gravação
        por_edicao = collections.defaultdict(list)
        for d in docs:
            if "conteudo_mudou_entre_versoes" in d["sinais"]:
                por_edicao[(d["meta"]["produtor_original"], d["meta"]["produtor"])].append(d)
        for k, ds in por_edicao.items():
            if len(ds) >= MIN_GRUPO:
                grupos.append({"tipo": "edicao_em_serie", "familia": fam, "chave": " -> ".join(map(str, k)), "docs": ds,
                               "leitura": f"{len(ds)} documentos '{fam}' emitidos por '{k[0]}' e alterados depois "
                                          + (f"em '{k[1]}'" if k[0] != k[1] else "pelo mesmo programa (que se identifica "
                                             "como o emissor)") + ", com mudança de conteúdo entre as versões"})
    for i, g in enumerate(grupos, 1):
        g["id"] = f"L{i}"
        g["acoes"] = sorted({_acao(d["arquivo"], raiz) for d in g["docs"]})
        for d in g["docs"]:
            d.setdefault("grupos", []).append(g["id"])
    return grupos, padrao


# ------------------------------------------------------------------------------------------- conclusão por arquivo
FORTES = {"conteudo_mudou_entre_versoes", "texto_escondido", "criado_antes_das_datas_do_texto", "saldo_nao_fecha"}
FRACOS = {"produtor_trocado_entre_versoes", "regravado_sem_mudar_conteudo", "produtor_fora_do_padrao_da_familia",
          "fonte_fora_do_padrao_da_familia", "ordem_cronologica_quebrada"}


def concluir(d: dict, grupos_por_id: dict) -> str:
    if d["erro"]:
        return "ERRO"
    s = set(d["sinais"])
    if s & FORTES:
        return "RISCO"
    if "pagina_e_imagem" in s:  # sem texto nem histórico: metadado sozinho não sustenta acusação
        return "INCONCLUSIVO"
    if any(grupos_por_id[g]["tipo"] in ("imagem_reaproveitada", "mesmo_modelo") for g in d.get("grupos", [])):
        return "RISCO"
    if s & FRACOS:
        return "REVISAR"
    return "OK"


# ------------------------------------------------------------------------------------------- medição
def medir(exames: list[dict], grupos: list[dict], raiz: Path, gabarito: Path) -> dict:
    gab = {str((gabarito.parent / g["arquivo"]).resolve()): g for g in json.loads(gabarito.read_text(encoding="utf-8"))}
    m = collections.Counter()
    erros_ex = {"falsos_alarmes": [], "perdidos": []}
    for d in exames:
        g = gab.get(str(Path(d["arquivo"]).resolve()))
        if not g:
            continue
        c = d["conclusao"]
        if g["adulterado"] is None:
            m["inconclusivo_certo" if c == "INCONCLUSIVO" else "inconclusivo_errado"] += 1
        elif g["adulterado"]:
            m["vp" if c == "RISCO" else "fn"] += 1
            m["adulterado_em_revisar"] += c == "REVISAR"
            if c != "RISCO":
                erros_ex["perdidos"].append(d["arquivo"])
        else:
            m["fp" if c == "RISCO" else "vn"] += 1
            m["revisar_em_legitimo"] += c == "REVISAR"
            if c == "RISCO":
                erros_ex["falsos_alarmes"].append(d["arquivo"])
    prec = m["vp"] / (m["vp"] + m["fp"]) if m["vp"] + m["fp"] else None
    rec = m["vp"] / (m["vp"] + m["fn"]) if m["vp"] + m["fn"] else None
    # recuperação dos grupos verdadeiros: melhor Jaccard entre as ações do grupo verdadeiro e de algum grupo achado
    verdade = collections.defaultdict(set)
    for g in gab.values():
        for gr in g.get("grupos", []):
            verdade[gr].add(f"acao-{g['acao']:04d}")
    rec_grupos = {}
    for gr, acoes in sorted(verdade.items()):
        melhor = max(((len(acoes & set(x["acoes"])) / len(acoes | set(x["acoes"])), x["id"]) for x in grupos),
                     default=(0, None))
        rec_grupos[gr] = {"acoes": len(acoes), "melhor_grupo": melhor[1], "jaccard": round(melhor[0], 3)}
    tri = (m["vp"] + m["adulterado_em_revisar"]) / (m["vp"] + m["fn"]) if m["vp"] + m["fn"] else None
    return {"contagem": dict(m), "precisao": prec and round(prec, 3), "revocacao": rec and round(rec, 3),
            "triagem_risco_ou_revisar": tri and round(tri, 3),
            "grupos": rec_grupos, "exemplos_de_erro": {k: v[:10] for k, v in erros_ex.items()}}


# ------------------------------------------------------------------------------------------- relatório
def relatorio_md(raiz, exames, grupos, padrao, medicao) -> str:
    c = collections.Counter(d["conclusao"] for d in exames)
    out = [f"# Perícia em lote — {raiz.name}", "",
           f"{len(exames)} arquivos examinados: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())), "",
           "## Padrão de cada família (aprendido do próprio lote)", ""]
    for fam, p in sorted(padrao.items()):
        out.append(f"- **{fam}** ({p['documentos']} docs): emissor habitual `{p['produtor_dominante']}`; fontes {', '.join(p['fontes'])}")
    out += ["", "## Grupos entre arquivos", ""]
    for g in grupos:
        out.append(f"- **{g['id']}** ({g['tipo']}): {g['leitura']}. Ações: {len(g['acoes'])}.")
    multi = collections.defaultdict(set)
    for g in grupos:
        for a in g["acoes"]:
            multi[a].add(g["id"])
    ligadas = {a: s for a, s in multi.items() if len(s) > 1}
    if ligadas:
        combos = collections.Counter(" + ".join(sorted(s)) for s in ligadas.values())
        out += ["", "## Ações em mais de um grupo", ""] + [f"- {k}: {v} ações" for k, v in combos.most_common()]
    if medicao:
        out += ["", "## Medição contra o gabarito", "", "```", json.dumps(medicao, ensure_ascii=False, indent=1), "```"]
    out += ["", "## Limites", "",
            "- O laudo descreve o que os arquivos mostram; não identifica autoria de pessoas.",
            "- Regravação sem mudança de conteúdo e produtor diferente são REVISAR, não RISCO (edição não é fraude).",
            "- Página que é só imagem é INCONCLUSIVO: pedir o original ao emissor.",
            "- A regra de saldo vale para extratos com 'SALDO ANTERIOR' e 'SALDO EM'; outros formatos precisam de regra própria.",
            "- Imagem presente em mais da metade da família é tratada como logotipo/modelo do emissor e não agrupa.",
            "- Assinatura reaproveitada conta titulares distintos pelo 1º CPF do texto; documento cujo 1º CPF não é o "
            "de quem assina precisa de regra própria.",
            "- JPEG é comparado a olho só com o Pillow instalado; JPX, CCITT e JBIG2 só agrupam por bytes idênticos.",
            "- A fonte é a declarada no PDF (/BaseFont), não o nome normalizado pela biblioteca de extração."]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pasta", type=Path)
    ap.add_argument("--saida", type=Path)
    ap.add_argument("--gabarito", type=Path)
    ap.add_argument("--processos", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    raiz = a.pasta.resolve()
    arquivos = sorted(str(p) for p in raiz.rglob("*.pdf"))
    with ProcessPoolExecutor(a.processos) as ex:
        exames = list(ex.map(examinar, arquivos, chunksize=8))
    grupos, padrao = agrupar(exames, raiz)
    gid = {g["id"]: g for g in grupos}
    for d in exames:
        d["conclusao"] = concluir(d, gid)
    medicao = medir(exames, grupos, raiz, a.gabarito) if a.gabarito else None
    saida = a.saida or Path.cwd() / f"laudo-lote-{raiz.name}"
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "exames.json").write_text(json.dumps(exames, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (saida / "grupos.json").write_text(json.dumps([{k: v for k, v in g.items() if k != "docs"} | {
        "arquivos": [d["arquivo"] for d in g["docs"]]} for g in grupos], ensure_ascii=False, indent=1), encoding="utf-8")
    (saida / "relatorio.md").write_text(relatorio_md(raiz, exames, grupos, padrao, medicao), encoding="utf-8")
    c = collections.Counter(d["conclusao"] for d in exames)
    print(f"{len(exames)} arquivos; {dict(c)}; {len(grupos)} grupos; laudo em {saida}")
    if medicao:
        print(json.dumps({k: medicao[k] for k in ("contagem", "precisao", "revocacao", "grupos")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
