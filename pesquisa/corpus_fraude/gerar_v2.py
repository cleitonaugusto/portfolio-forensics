"""Corpus fictício de fraude documental v2 — teste ÀS CEGAS do periciar-lote (ver pre-registro-v2.md).

Mesmas garantias do v0/v1 (tudo fictício, rodapé de treinamento em todas as páginas, CPF com dígito inválido,
determinístico para a mesma versão do Pillow). Novidades: assinaturas variadas, JPEG (digitalização), duas páginas.

Uso: python3 -I gerar_v2.py <pasta_saida>      (precisa do Pillow só para desenhar e codificar JPEG)
"""

import io
import json
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar import (CINZA, FONTES, P_BANCO, P_EDITOR_TEXTO, P_ENERGIA, RODAPE, Pdf, info,  # noqa: E402
                   itens_comprovante, pessoa, reais)

_info = Pdf._info
from gerar_v1 import P_OTIMIZADOR, emissao, imagem_padrao  # noqa: E402

SEMENTE = 20261118
FONTES_V2 = {**FONTES, "F4": "Arial"}
LARGURA_ARIAL = 556  # Arial tem as mesmas larguras médias da Helvetica; aqui uma largura única basta


def _s(texto: str) -> bytes:
    t = texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return b"(" + t.encode("cp1252", errors="replace") + b")"


def _ops(itens):
    ops, fontes, imagens = [], set(), []
    for it in itens:
        if it[0] == "T":
            _, texto, f, tam, x, y, *cor = it
            c = cor[0] if cor else (0, 0, 0)
            fontes.add(f)
            ops.append(b"BT /%s %g Tf %g %g %g rg %g %g Td " % (f.encode(), tam, *c, x, y) + _s(texto) + b" Tj ET")
        elif it[0] == "I":
            _, nome, x, y, w, h = it
            imagens.append(nome)
            ops.append(b"q %g 0 0 %g %g %g cm /%s Do Q" % (w, h, x, y, nome.encode()))
    return b"\n".join(ops), fontes, imagens


class PdfN:
    """PDF de N páginas. `salvar` grava a 1ª versão; `atualizar` acrescenta uma versão incremental que reescreve as
    páginas (a anterior continua dentro do arquivo). Imagens: {"nome": ("raw", w, h, px) | ("jpeg", w, h, bytes)}."""

    def __init__(self, caminho: Path, imagens: dict | None = None):
        self.caminho, self.imagens = caminho, imagens or {}
        self.dados, self.objs_fonte, self.objs_imagem = b"", {}, {}
        self.tamanho = self.ultimo_xref = self.npag = 0

    @staticmethod
    def _fonte_obj(f):
        if f == "F4":
            return (b"<< /Type /Font /Subtype /TrueType /BaseFont /Arial /Encoding /WinAnsiEncoding /FirstChar 32 "
                    b"/LastChar 255 /Widths [" + b" ".join([b"%d" % LARGURA_ARIAL] * 224) + b"] /FontDescriptor "
                    b"<< /Type /FontDescriptor /FontName /Arial /Flags 32 /FontBBox [-665 -325 2000 1006] /ItalicAngle 0 "
                    b"/Ascent 905 /Descent -212 /CapHeight 716 /StemV 80 /MissingWidth %d >> >>" % LARGURA_ARIAL)
        return b"<< /Type /Font /Subtype /Type1 /BaseFont /%s /Encoding /WinAnsiEncoding >>" % FONTES_V2[f].encode()

    def _img_obj(self, nome):
        tipo, w, h, dados = self.imagens[nome]
        filtro = b"/Filter /DCTDecode " if tipo == "jpeg" else b""
        return (b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceGray /BitsPerComponent 8 "
                % (w, h) + filtro + b"/Length %d >>\nstream\n" % len(dados) + dados + b"\nendstream")

    def _pagina(self, k):
        f = b" ".join(b"/%s %d 0 R" % (n.encode(), v) for n, v in sorted(self.objs_fonte.items()))
        i = b" ".join(b"/%s %d 0 R" % (n.encode(), v) for n, v in sorted(self.objs_imagem.items()))
        rec = b"/Font << " + f + b" >>" + (b" /XObject << " + i + b" >>" if i else b"")
        return (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents %d 0 R /Resources << " % (4 + 2 * k)
                + rec + b" >> >>")

    @staticmethod
    def _conteudo(itens):
        return _ops(itens + [("T", RODAPE, "F1", 6, 40, 20, CINZA)])

    def _novos_recursos(self, conteudos, n):
        novos = []
        for f in sorted(set().union(*(c[1] for c in conteudos)) - set(self.objs_fonte)):
            self.objs_fonte[f] = n
            novos.append((n, self._fonte_obj(f)))
            n += 1
        for im in dict.fromkeys(x for c in conteudos for x in c[2]):
            if im not in self.objs_imagem:
                self.objs_imagem[im] = n
                novos.append((n, self._img_obj(im)))
                n += 1
        return novos, n

    def _paginas_objs(self, conteudos):
        out = []
        for k, (ops, _, _) in enumerate(conteudos):
            out += [(3 + 2 * k, self._pagina(k)), (4 + 2 * k, b"<< /Length %d >>\nstream\n" % len(ops) + ops + b"\nendstream")]
        return out

    def salvar(self, paginas, inf) -> "PdfN":
        self.npag = len(paginas)
        conteudos = [self._conteudo(p) for p in paginas]
        kids = b" ".join(b"%d 0 R" % (3 + 2 * k) for k in range(self.npag))
        novos, n = self._novos_recursos(conteudos, 3 + 2 * self.npag)
        objs = [(1, b"<< /Type /Catalog /Pages 2 0 R >>"), (2, b"<< /Type /Pages /Kids [" + kids + b"] /Count %d >>" % self.npag)]
        objs += self._paginas_objs(conteudos) + novos + [(n, _info(inf))]
        objs.sort()
        saida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        pos = []
        for k, o in objs:
            pos.append(len(saida))
            saida += b"%d 0 obj\n" % k + o + b"\nendobj\n"
        xref = len(saida)
        saida += b"xref\n0 %d\n0000000000 65535 f \n" % (n + 1) + b"".join(b"%010d 00000 n \n" % p for p in pos)
        saida += b"trailer\n<< /Size %d /Root 1 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (n + 1, n, xref)
        self.dados, self.tamanho, self.ultimo_xref = bytes(saida), n + 1, xref
        self.caminho.write_bytes(self.dados)
        return self

    def atualizar(self, paginas, inf) -> "PdfN":
        assert len(paginas) == self.npag, "a versão incremental mantém o número de páginas"
        conteudos = [self._conteudo(p) for p in paginas]
        novos, n = self._novos_recursos(conteudos, self.tamanho)
        novos += self._paginas_objs(conteudos) + [(n, _info(inf))]
        saida = bytearray(self.dados)
        pos = {}
        for k, o in novos:
            pos[k] = len(saida)
            saida += b"%d 0 obj\n" % k + o + b"\nendobj\n"
        xref = len(saida)
        saida += b"xref\n0 1\n0000000000 65535 f \n" + b"".join(b"%d 1\n%010d 00000 n \n" % (k, pos[k]) for k in sorted(pos))
        saida += b"trailer\n<< /Size %d /Root 1 0 R /Info %d 0 R /Prev %d >>\nstartxref\n%d\n%%%%EOF\n" % (
            n + 1, n, self.ultimo_xref, xref)
        self.dados, self.tamanho, self.ultimo_xref = bytes(saida), n + 1, xref
        self.caminho.write_bytes(self.dados)
        return self


# ----------------------------------------------------------------------------------------------- imagens
def _tracos(semente: int, jitter: random.Random | None = None):
    """Parâmetros da assinatura de uma pessoa; `jitter` simula a mesma pessoa assinando de novo."""
    r = random.Random(semente)
    w, h = r.randint(110, 180), r.randint(36, 60)
    inclin = r.uniform(-0.35, 0.35)
    tracos = []
    x = r.randint(4, 12)
    for _ in range(r.randint(2, 4)):
        comp = r.randint(25, max(26, (w - x) // 2))
        tracos.append({"x0": x, "comp": comp, "amp": r.uniform(0.2, 0.45) * h, "freq": r.uniform(0.08, 0.35),
                       "fase": r.uniform(0, 6.28), "laco": r.random() < 0.5, "esp": r.randint(1, 3)})
        x += comp + r.randint(-6, 8)
        if x > w - 20:
            break
    if jitter:
        for t in tracos:
            t["amp"] *= jitter.uniform(0.85, 1.15)
            t["freq"] *= jitter.uniform(0.93, 1.07)
            t["fase"] += jitter.uniform(-0.35, 0.35)
            t["comp"] = int(t["comp"] * jitter.uniform(0.9, 1.1))
            t["x0"] += jitter.randint(-3, 3)
        inclin += jitter.uniform(-0.08, 0.08)
    return w, h, inclin, tracos


def assinatura_v2(semente: int, jitter: random.Random | None = None, fundo=255, ruido: random.Random | None = None):
    """Imagem PIL 'L' de uma assinatura com 2–4 traços, laços, inclinação e espessura variáveis."""
    w, h, inclin, tracos = _tracos(semente, jitter)
    img = Image.new("L", (w, h), fundo)
    d = ImageDraw.Draw(img)
    for t in tracos:
        pts = []
        for k in range(t["comp"]):
            y = h / 2 + t["amp"] * math.sin(k * t["freq"] + t["fase"])
            x = t["x0"] + k + (y - h / 2) * inclin
            if t["laco"]:
                x += 4 * math.cos(k * t["freq"] * 2)
            pts.append((x, y))
        d.line(pts, fill=25, width=t["esp"])
    if ruido:  # papel digitalizado: fundo levemente sujo
        px = img.load()
        for _ in range(w * h // 12):
            x, y = ruido.randrange(w), ruido.randrange(h)
            if px[x, y] > 200:
                px[x, y] = ruido.randint(215, 245)
    return img


def raw(img: Image.Image):
    return ("raw", img.width, img.height, img.tobytes())


def jpeg(img: Image.Image, qualidade: int):
    b = io.BytesIO()
    img.save(b, format="JPEG", quality=qualidade)
    return ("jpeg", img.width, img.height, b.getvalue())


def tela_jpeg(r: random.Random):
    """'Print de tela' de um extrato: página só imagem, sem camada de texto."""
    img = Image.new("L", (300, 424), 250)
    d = ImageDraw.Draw(img)
    d.rectangle((10, 10, 290, 40), fill=60)
    for y in range(60, 400, 14):
        d.rectangle((14, y, 14 + r.randint(120, 260), y + 6), fill=r.randint(90, 160))
    return jpeg(img, r.randint(70, 90))


def bruto(t):
    return ("raw", *t)


# ----------------------------------------------------------------------------------------------- documentos
def lancamentos_v2(r: random.Random, n: int):
    saldo_ant = r.randint(5_000, 300_000)
    tipos = [("CRED SALARIO EMPRESA EXEMPLO", 150_000, 600_000), ("PIX ENVIADO", -40_000, -2_000),
             ("PAGTO CONTA ENERGIA", -30_000, -8_000), ("COMPRA CARTAO DEBITO", -20_000, -1_000),
             ("PIX RECEBIDO", 1_000, 50_000), ("SAQUE TERMINAL", -20_000, -5_000), ("PAGTO BOLETO", -60_000, -5_000)]
    dias = sorted(r.randint(1, 31) for _ in range(n - 1))
    lanc = [(f"{d:02d}/03/2026", *(lambda t: (t[0], r.randint(t[1], t[2])))(r.choice(tipos))) for d in dias]
    lanc.insert(r.randrange(len(lanc) + 1), None)
    k = lanc.index(None)
    dia = int(lanc[k - 1][0][:2]) if k else 1
    lanc[k] = (f"{dia:02d}/03/2026", "TARIFA PACOTE SERVICOS", -r.choice([1_990, 2_490, 3_190]))
    return saldo_ant, lanc


def _cab_extrato(p, logo):
    return [("I", "Logo", 440, 790, 120, 40), ("T", "BANCO EXEMPLO S.A. (FICTICIO)", "F1", 14, 40, 790),
            ("T", "Extrato de conta corrente", "F1", 11, 40, 772),
            ("T", f"Cliente: {p['nome']}   CPF: {p['cpf']}", "F1", 9, 40, 752),
            ("T", "Agencia 0000-X   Conta 00000-0 (ficticias)   Periodo: 01/03/2026 a 31/03/2026", "F1", 9, 40, 738)][
        0 if logo else 1:]


def paginas_extrato(p, saldo_ant, lanc, por_pagina, saldo_final=None):
    """Lista de páginas. Página 1: saldo anterior e os primeiros lançamentos; última: saldo final."""
    saldo = saldo_ant + sum(v for *_, v in lanc) if saldo_final is None else saldo_final
    blocos = [lanc[i:i + por_pagina] for i in range(0, len(lanc), por_pagina)] or [[]]
    pags = []
    for n, bloco in enumerate(blocos):
        it = _cab_extrato(p, True)
        if len(blocos) > 1:
            it.append(("T", f"Pagina {n + 1} de {len(blocos)}", "F1", 8, 480, 772))
        y = 712
        if n == 0:
            it.append(("T", f"SALDO ANTERIOR {reais(saldo_ant)}", "F1", 9, 40, y))
        y = 694
        for d, h, v in bloco:
            it.append(("T", f"{d}   {h:<34} {reais(v):>16}", "F1", 9, 40, y))
            y -= 15
        if n == len(blocos) - 1:
            it.append(("T", f"SALDO EM 31/03/2026 {reais(saldo)}", "F1", 9, 40, y - 10))
        else:
            it.append(("T", "(continua na proxima pagina)", "F1", 8, 40, y - 10))
        pags.append(it)
    return pags


PODERES = ["para o foro em geral, com a clausula ad judicia et extra, podendo propor acoes, contestar, recorrer,",
           "transigir, desistir, receber e dar quitacao, firmar compromissos e substabelecer, com ou sem reserva,",
           "praticando todos os atos necessarios ao bom e fiel cumprimento deste mandato (texto ficticio)."]


def paginas_procuracao(p, escritorio, assin, w, h, duas_paginas):
    tim = [("I", "Tim", 40, 790, 120, 40)]
    corpo = [("T", "PROCURACAO AD JUDICIA", "F2", 14, 200, 770),
             ("T", f"Outorgante: {p['nome']}, CPF {p['cpf']}, residente em {p['endereco']}.", "F2", 10, 40, 745),
             ("T", f"Outorgado: {escritorio} (escritorio ficticio), com os poderes abaixo.", "F2", 10, 40, 730)]
    corpo += [("T", t, "F2", 10, 40, 712 - 15 * k) for k, t in enumerate(PODERES)]
    fim = [("T", "Cidade Exemplo, 05 de abril de 2026.", "F2", 10, 40, 600), ("I", "Ass", 40, 590 - h * 1.2, w * 1.2, h * 1.2),
           ("T", p["nome"], "F2", 9, 40, 578 - h * 1.2)]
    if duas_paginas:
        return [tim + corpo, tim + [("T", "PROCURACAO AD JUDICIA (continuacao)", "F2", 10, 200, 770)] + fim]
    return [tim + corpo + fim]


def comprovante_arial(p, valor):
    return [x if x[0] != "T" else (x[0], x[1], "F4", *x[3:]) for x in itens_comprovante(p, valor)]


# ----------------------------------------------------------------------------------------------- lote
def gerar(saida: Path) -> list[dict]:
    r = random.Random(SEMENTE)
    gab = []
    lote = saida / "lote"
    logo_banco, logo_energia = bruto(imagem_padrao(1)), bruto(imagem_padrao(2))
    escritorios = [{"nome": f"Escritorio Ficticio {k + 1:02d}", "timbre": bruto(imagem_padrao(200 + k))} for k in range(40)]
    pesos = [r.choice((1, 1, 2, 3, 5)) for _ in escritorios]
    fraude_esc = {"nome": "Escritorio Ficticio Padrao", "timbre": bruto(imagem_padrao(1999))}
    mestra = assinatura_v2(888_001, ruido=random.Random(888_002), fundo=246)

    ids = list(range(1, 501))
    emb = r.sample(ids, len(ids))
    j1 = set(emb[:50])
    j2 = set(emb[50:65]) | set(emb[:15])
    j4 = set(emb[65:85])
    j5 = set(emb[85:105])
    j3 = set(emb[105:130])
    otim = set(emb[130:145])
    trios = [emb[145 + 3 * k:148 + 3 * k] for k in range(10)]
    pessoa_de = {i: k for k, t in enumerate(trios) for i in t}
    pessoas_trio = [pessoa(random.Random(SEMENTE * 7 + k)) for k in range(10)]
    esc_trio = [r.choices(escritorios, weights=pesos)[0] for _ in range(10)]

    def reg(a, i, grupos, tipo, adulterado, sinais, explicacao, conclusivel=True):
        gab.append({"arquivo": str(a.relative_to(saida)), "acao": i, "grupos": grupos, "tipo": tipo,
                    "adulterado": adulterado, "conclusivel": conclusivel, "sinais": sinais, "explicacao": explicacao})

    for i in ids:
        rp = random.Random(SEMENTE * 1000 + i)
        p = pessoas_trio[pessoa_de[i]] if i in pessoa_de else pessoa(rp)
        d = lote / f"acao-{i:04d}"
        d.mkdir(parents=True)
        grupos = [g for g, s in (("J1", j1), ("J2", j2), ("J3", j3), ("J4", j4), ("J5", j5), ("ISCA-OTIM", otim),
                                 ("ISCA-PESSOA", set(pessoa_de))) if i in s]

        # ---- procuração
        a = d / "procuracao.pdf"
        duas = rp.random() < 0.4
        if i in j1:
            esc = fraude_esc
            m = mestra.crop((rp.randint(0, 2), rp.randint(0, 2), mestra.width - rp.randint(0, 2), mestra.height - rp.randint(0, 2)))
            ass = jpeg(m, rp.randint(60, 92))
        elif i in pessoa_de:
            k = pessoa_de[i]
            esc = esc_trio[k]
            img = assinatura_v2(SEMENTE + 50_000 + k, jitter=random.Random(SEMENTE * 3 + i))
            ass = raw(img)
        else:
            esc = rp.choices(escritorios, weights=pesos)[0]
            digitalizada = rp.random() < 0.4
            img = assinatura_v2(SEMENTE + i, ruido=random.Random(i) if digitalizada else None,
                                fundo=246 if digitalizada else 255)
            ass = jpeg(img, rp.randint(60, 92)) if digitalizada else raw(img)
        _, w, h, _ = ass
        PdfN(a, {"Tim": esc["timbre"], "Ass": ass}).salvar(
            paginas_procuracao(p, esc["nome"], "Ass", w, h, duas),
            info(P_EDITOR_TEXTO, f"2026-04-{rp.randint(1, 28):02d} {rp.randint(8, 18):02d}:{rp.randint(0, 59):02d}",
                 autor=esc["nome"].lower().replace(" ", "-")))
        if i in j1:
            reg(a, i, grupos, "procuracao", True, ["assinatura_igual_a_olho", "jpeg_recomprimido"],
                "A mesma assinatura digitalizada, recortada e recomprimida, em 50 procurações de pessoas diferentes.")
        elif i in pessoa_de:
            reg(a, i, grupos, "procuracao", False, [],
                "ISCA: a mesma pessoa (mesmo nome e CPF) tem 3 ações e assinou cada procuração de novo; as assinaturas "
                "são parecidas, não iguais. Legítimo.")
        else:
            reg(a, i, grupos, "procuracao", False, [], "Legítima.")

        # ---- comprovante
        a = d / "comprovante.pdf"
        valor = rp.randint(8_000, 40_000)
        logo = [("I", "Logo", 440, 780, 120, 40)]
        if i in j5:
            PdfN(a, {"Logo": logo_energia}).salvar([logo + comprovante_arial(p, valor)], info(P_ENERGIA, emissao(rp)))
            reg(a, i, grupos, "comprovante", True, ["fonte_fora_do_padrao", "produtor_falsificado"],
                "Refeito do zero com endereço trocado; o produtor foi falsificado para parecer o da companhia, "
                "mas a fonte (Arial) não é a do emissor.")
        else:
            PdfN(a, {"Logo": logo_energia}).salvar([logo + itens_comprovante(p, valor)], info(P_ENERGIA, emissao(rp)))
            reg(a, i, grupos, "comprovante", False, [], "Legítimo, emitido pelo sistema da companhia.")

        # ---- extrato
        a = d / "extrato.pdf"
        emit = emissao(rp)
        imgs = {"Logo": logo_banco}
        duas = i in j2 or i in j4 or rp.random() < 0.3
        sa, lanc = lancamentos_v2(rp, 14 if duas else 8)
        por = 8
        if i in j2:
            pag2 = lanc[por:]
            d0 = int(pag2[0][0][:2])
            linha = (f"{rp.randint(d0, 31):02d}/03/2026", "DEB SEGURO PRESTAMISTA NAO CONTRATADO", -rp.choice([9_990, 14_990]))
            falso = lanc[:por] + sorted(pag2 + [linha], key=lambda x: x[0])
            PdfN(a, imgs).salvar(paginas_extrato(p, sa, lanc, por), info(P_BANCO, emit)).atualizar(
                paginas_extrato(p, sa, falso, por),
                info(P_BANCO, emit, f"2026-04-{rp.randint(10, 28):02d} 20:{rp.randint(10, 59)}"))
            reg(a, i, grupos, "extrato", True, ["versao_anterior", "saldo_fecha_mesmo_assim", "duas_paginas"],
                "Extrato de duas páginas; lançamento inventado na página 2 numa segunda gravação, mesmo produtor, "
                "saldo recalculado. A versão anterior denuncia.")
        elif i in j4:
            certo = sa + sum(v for *_, v in lanc)
            PdfN(a, imgs).salvar(paginas_extrato(p, sa, lanc, por, saldo_final=certo + rp.randint(50_000, 200_000)),
                                 info(P_BANCO, emit))
            reg(a, i, grupos, "extrato", True, ["saldo_nao_fecha", "duas_paginas"],
                "Saldo final (página 2) não confere com o saldo anterior (página 1) mais os lançamentos.")
        elif i in j3:
            PdfN(a, {"Tela": tela_jpeg(rp)}).salvar([[("I", "Tela", 0, 0, 595, 842)]], info("ImagemParaPDF 1.0", emit))
            reg(a, i, grupos, "extrato", None, ["sem_camada_de_texto", "jpeg"],
                "Só imagem (print de tela em JPEG): o exame do arquivo não conclui; pedir o original ao banco.",
                conclusivel=False)
        elif i in otim:
            PdfN(a, imgs).salvar(paginas_extrato(p, sa, lanc, por), info(P_OTIMIZADOR, emit, "2026-04-25 13:00"))
            reg(a, i, grupos, "extrato", False, ["produtor_fora_do_padrao"],
                "ISCA: regravado inteiro por um otimizador, sem mudar conteúdo. Edição não é fraude.")
        else:
            PdfN(a, imgs).salvar(paginas_extrato(p, sa, lanc, por), info(P_BANCO, emit))
            reg(a, i, grupos, "extrato", False, [], "Legítimo, emitido pelo sistema do banco.")
    return gab


def main():
    saida = Path(sys.argv[1]).resolve()
    if saida.exists() and any(saida.iterdir()):
        sys.exit(f"{saida} não está vazia")
    saida.mkdir(parents=True, exist_ok=True)
    gab = gerar(saida)
    (saida / "gabarito.json").write_text(json.dumps(gab, ensure_ascii=False, indent=1), encoding="utf-8")
    cont = {}
    for g in gab:
        k = f"{g['tipo']}:{'inconclusivo' if g['adulterado'] is None else ('adulterado' if g['adulterado'] else 'legitimo')}"
        cont[k] = cont.get(k, 0) + 1
    print(len(gab), "arquivos;", json.dumps(cont, ensure_ascii=False))


if __name__ == "__main__":
    main()
