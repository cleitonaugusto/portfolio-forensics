"""Corpus fictício de fraude documental (v0) — pesquisa de perícia em lote.

Tudo é inventado: Banco Exemplo, Companhia de Energia Exemplo, Tribunal Fictício, pessoas e CPFs (com dígito
verificador propositalmente INVÁLIDO). Todo documento leva o rodapé "DOCUMENTO FICTÍCIO - MATERIAL DE TREINAMENTO".
Nada vem de sistema judicial ou de processo real. Determinístico: mesma semente → mesmos bytes.

Uso: python3 -I gerar.py <pasta_saida>
Saída: modulo4/ (casos individuais), decisoes/ (golpe do falso advogado), lote/ (carteira de 500 ações),
gabarito.json (a verdade de cada arquivo) e LEIAME.md.
"""

import json
import math
import random
import sys
from pathlib import Path

SEMENTE = 20261116
RODAPE = "DOCUMENTO FICTÍCIO - MATERIAL DE TREINAMENTO - não representa pessoa, empresa ou processo real"
FONTES = {"F1": "Helvetica", "F2": "Times-Roman", "F3": "Courier"}
PRETO, CINZA, BRANCO = (0, 0, 0), (0.45, 0.45, 0.45), (1, 1, 1)

# Produtores fictícios (o campo /Producer é o que a perícia lê)
P_BANCO = "SistemaExtrato BancoExemplo 3.2"
P_ENERGIA = "SisFatura CEE 5.1"
P_TRIBUNAL = "SisDecisao TribunalFicticio 2.0"
P_EDITOR_TEXTO = "EditorTexto 16.0 (exportar PDF)"
P_EDITOR_ONLINE = "PDF-Online-Editor 2.1"
P_IMAGEM = "ImagemParaPDF 1.0"


# ----------------------------------------------------------------------------------------------- PDF mínimo
def _s(texto: str) -> bytes:
    t = texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return b"(" + t.encode("cp1252", errors="replace") + b")"


def _data(d: str) -> str:
    """'2026-04-02 10:15' → D:20260402101500-03'00'"""
    return "D:" + d.replace("-", "").replace(" ", "").replace(":", "") + "00-03'00'"


def _ops(itens) -> tuple[bytes, set, list]:
    """itens: ("T", texto, fonte, tam, x, y[, cor]) | ("R", x, y, w, h, cor) | ("I", nome, x, y, w, h)"""
    ops, fontes, imagens = [], set(), []
    for it in itens:
        if it[0] == "T":
            _, texto, f, tam, x, y, *cor = it
            c = cor[0] if cor else PRETO
            fontes.add(f)
            ops.append(b"BT /%s %g Tf %g %g %g rg %g %g Td " % (f.encode(), tam, *c, x, y) + _s(texto) + b" Tj ET")
        elif it[0] == "R":
            _, x, y, w, h, c = it
            ops.append(b"%g %g %g rg %g %g %g %g re f" % (*c, x, y, w, h))
        elif it[0] == "I":
            _, nome, x, y, w, h = it
            imagens.append(nome)
            ops.append(b"q %g 0 0 %g %g %g cm /%s Do Q" % (w, h, x, y, nome.encode()))
    return b"\n".join(ops), fontes, imagens


class Pdf:
    """Monta um PDF de uma página; `salvar` grava a 1ª versão e `atualizar` acrescenta versões incrementais
    (a versão anterior continua dentro do arquivo, como num editor que 'salva por cima')."""

    def __init__(self, caminho: Path, imagens: dict[str, tuple[int, int, bytes]] | None = None):
        self.caminho, self.imagens = caminho, imagens or {}
        self.dados = b""
        self.objs_fonte: dict[str, int] = {}
        self.objs_imagem: dict[str, int] = {}
        self.tamanho = 0
        self.ultimo_xref = 0

    def _img_obj(self, nome):
        w, h, px = self.imagens[nome]
        return b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceGray /BitsPerComponent 8 " \
               b"/Length %d >>\nstream\n" % (w, h, len(px)) + px + b"\nendstream"

    def _pagina(self):
        f = b" ".join(b"/%s %d 0 R" % (k.encode(), v) for k, v in sorted(self.objs_fonte.items()))
        i = b" ".join(b"/%s %d 0 R" % (k.encode(), v) for k, v in sorted(self.objs_imagem.items()))
        rec = b"/Font << " + f + b" >>" + (b" /XObject << " + i + b" >>" if i else b"")
        return b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << " + rec + b" >> >>"

    @staticmethod
    def _info(info):
        return b"<< " + b" ".join(b"/" + k.encode() + b" " + _s(v) for k, v in info.items()) + b" >>"

    def salvar(self, itens, info) -> "Pdf":
        conteudo, fontes, imagens = _ops(itens + [("T", RODAPE, "F1", 6, 40, 20, CINZA)])
        n = 5
        extras = []
        for f in sorted(fontes):
            self.objs_fonte[f] = n
            extras.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /%s /Encoding /WinAnsiEncoding >>" % FONTES[f].encode())
            n += 1
        for im in dict.fromkeys(imagens):
            self.objs_imagem[im] = n
            extras.append(self._img_obj(im))
            n += 1
        objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>", self._pagina(),
                b"<< /Length %d >>\nstream\n" % len(conteudo) + conteudo + b"\nendstream"] + extras + [self._info(info)]
        info_n = len(objs)
        saida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        pos = []
        for k, o in enumerate(objs, 1):
            pos.append(len(saida))
            saida += b"%d 0 obj\n" % k + o + b"\nendobj\n"
        xref = len(saida)
        saida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % p for p in pos)
        saida += b"trailer\n<< /Size %d /Root 1 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, info_n, xref)
        self.dados, self.tamanho, self.ultimo_xref = bytes(saida), len(objs) + 1, xref
        self.caminho.write_bytes(self.dados)
        return self

    def atualizar(self, itens, info) -> "Pdf":
        conteudo, fontes, imagens = _ops(itens + [("T", RODAPE, "F1", 6, 40, 20, CINZA)])
        novos: list[tuple[int, bytes]] = []
        n = self.tamanho
        for f in sorted(fontes - set(self.objs_fonte)):
            self.objs_fonte[f] = n
            novos.append((n, b"<< /Type /Font /Subtype /Type1 /BaseFont /%s /Encoding /WinAnsiEncoding >>" % FONTES[f].encode()))
            n += 1
        for im in dict.fromkeys(imagens):
            if im not in self.objs_imagem:
                self.objs_imagem[im] = n
                novos.append((n, self._img_obj(im)))
                n += 1
        info_n = n
        novos += [(3, self._pagina()), (4, b"<< /Length %d >>\nstream\n" % len(conteudo) + conteudo + b"\nendstream"),
                  (info_n, self._info(info))]
        saida = bytearray(self.dados)
        pos = {}
        for k, o in novos:
            pos[k] = len(saida)
            saida += b"%d 0 obj\n" % k + o + b"\nendobj\n"
        xref = len(saida)
        saida += b"xref\n0 1\n0000000000 65535 f \n" + b"".join(b"%d 1\n%010d 00000 n \n" % (k, pos[k]) for k in sorted(pos))
        saida += b"trailer\n<< /Size %d /Root 1 0 R /Info %d 0 R /Prev %d >>\nstartxref\n%d\n%%%%EOF\n" % (
            info_n + 1, info_n, self.ultimo_xref, xref)
        self.dados, self.tamanho, self.ultimo_xref = bytes(saida), info_n + 1, xref
        self.caminho.write_bytes(self.dados)
        return self


def info(produtor, criado, modificado=None, autor=None, criador=None):
    d = {"Producer": produtor, "CreationDate": _data(criado), "ModDate": _data(modificado or criado)}
    if autor:
        d["Author"] = autor
    if criador:
        d["Creator"] = criador
    return d


# ----------------------------------------------------------------------------------------------- dados fictícios
NOMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fabio", "Gisele", "Heitor", "Iara", "Joao", "Karina", "Lucas",
         "Marta", "Nelson", "Olivia", "Paulo", "Quiteria", "Rafael", "Sonia", "Tiago", "Ursula", "Vitor", "Wanda",
         "Xavier", "Yara", "Zeca", "Aurora", "Benicio", "Celia", "Dario"]
SOBRENOMES = ["Amaral", "Barreto", "Cordeiro", "Damasceno", "Esteves", "Falcao", "Guimaraes", "Holanda", "Itaborai",
              "Jacinto", "Lacerda", "Magalhaes", "Nogueira", "Orlando", "Pimentel", "Quaresma", "Rezende", "Sampaio",
              "Teixeira", "Uchoa", "Valadares", "Wanderley", "Xisto", "Zanetti", "Bittencourt", "Correia", "Drummond"]
RUAS = ["Rua das Acacias", "Avenida dos Ipes", "Travessa do Sol", "Rua Projetada Um", "Alameda das Palmeiras",
        "Rua Sete de Exemplo", "Avenida Ficticia", "Rua do Treinamento"]


def cpf_ficticio(r: random.Random) -> str:
    """CPF com dígitos verificadores propositalmente errados: não pode coincidir com CPF real válido."""
    base = [r.randint(0, 9) for _ in range(9)]
    s1 = sum(d * p for d, p in zip(base, range(10, 1, -1))) % 11
    d1 = 0 if s1 < 2 else 11 - s1
    s2 = sum(d * p for d, p in zip(base + [d1], range(11, 1, -1))) % 11
    d2 = 0 if s2 < 2 else 11 - s2
    d2 = (d2 + 1 + r.randint(0, 8)) % 10  # nunca o dígito certo
    b = "".join(map(str, base))
    return f"{b[:3]}.{b[3:6]}.{b[6:]}-{d1}{d2}"


def reais(centavos: int) -> str:
    s = f"{abs(centavos) / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if centavos < 0 else "") + "R$ " + s


def assinatura(semente: int) -> tuple[int, int, bytes]:
    """Imagem 96x32 em tons de cinza com um traço 'manuscrito' próprio da semente."""
    r = random.Random(semente)
    w, h = 96, 32
    px = bytearray([255] * (w * h))
    a, b, c = r.uniform(2.5, 6), r.uniform(0.15, 0.45), r.uniform(0, 6.28)
    for x in range(6, w - 6):
        y = int(h / 2 + (h / 3) * math.sin(x * b + c) * math.cos(x / a))
        for dy in (-1, 0, 1):
            if 0 <= y + dy < h:
                px[(y + dy) * w + x] = 30
    return w, h, bytes(px)


def pessoa(r: random.Random) -> dict:
    return {"nome": f"{r.choice(NOMES)} {r.choice(SOBRENOMES)} {r.choice(SOBRENOMES)}", "cpf": cpf_ficticio(r),
            "endereco": f"{r.choice(RUAS)}, {r.randint(10, 999)} - Cidade Exemplo/EX"}


# ----------------------------------------------------------------------------------------------- documentos
def lancamentos_extrato(r: random.Random) -> tuple[int, list]:
    saldo_ant = r.randint(5_000, 300_000)
    hist = [("CRED SALARIO EMPRESA EXEMPLO", r.randint(150_000, 600_000)), ("PIX ENVIADO", -r.randint(2_000, 40_000)),
            ("PAGTO CONTA ENERGIA", -r.randint(8_000, 30_000)), ("COMPRA CARTAO DEBITO", -r.randint(1_000, 20_000)),
            ("TARIFA PACOTE SERVICOS", -r.choice([1_990, 2_490, 3_190])), ("PIX RECEBIDO", r.randint(1_000, 50_000)),
            ("SAQUE TERMINAL", -r.choice([5_000, 10_000, 20_000]))]
    r.shuffle(hist)
    return saldo_ant, [(f"{d:02d}/03/2026", h, v) for d, (h, v) in zip(sorted(r.sample(range(1, 31), len(hist))), hist)]


def itens_extrato(p, saldo_ant, lanc, saldo_final=None, fonte_linha=None):
    """fonte_linha: {índice: fonte} para linhas reescritas em outra fonte (sinal de edição)."""
    fonte_linha = fonte_linha or {}
    saldo = saldo_ant + sum(v for *_, v in lanc) if saldo_final is None else saldo_final
    it = [("T", "BANCO EXEMPLO S.A. (FICTICIO)", "F1", 14, 40, 790), ("T", "Extrato de conta corrente", "F1", 11, 40, 772),
          ("T", f"Cliente: {p['nome']}   CPF: {p['cpf']}", "F1", 9, 40, 752),
          ("T", "Agencia 0000-X   Conta 00000-0 (ficticias)   Periodo: 01/03/2026 a 31/03/2026", "F1", 9, 40, 738),
          ("T", f"SALDO ANTERIOR {reais(saldo_ant)}", "F1", 9, 40, 712)]
    y = 694
    for k, (d, h, v) in enumerate(lanc):
        f = fonte_linha.get(k, "F1")
        it.append(("T", f"{d}   {h:<34} {reais(v):>16}", f, 9, 40, y))
        y -= 15
    it.append(("T", f"SALDO EM 31/03/2026 {reais(saldo)}", "F1", 9, 40, y - 10))
    return it


def itens_comprovante(p, valor, fonte_end="F1", corretivo=False, endereco_original=None):
    it = [("T", "COMPANHIA DE ENERGIA EXEMPLO (FICTICIA)", "F1", 13, 40, 790),
          ("T", "Fatura de energia eletrica - referencia 03/2026", "F1", 10, 40, 772),
          ("T", f"Titular: {p['nome']}", "F1", 9, 40, 750)]
    if corretivo:  # endereço original coberto por retângulo branco e reescrito por cima
        it += [("T", f"Endereco: {endereco_original}", "F1", 9, 40, 736), ("R", 38, 733, 420, 12, BRANCO),
               ("T", f"Endereco: {p['endereco']}", fonte_end, 9, 40, 736)]
    else:
        it.append(("T", f"Endereco: {p['endereco']}", fonte_end, 9, 40, 736))
    it += [("T", "Unidade consumidora 0000000 (ficticia)   Vencimento 15/04/2026", "F1", 9, 40, 722),
           ("T", f"Total a pagar: {reais(valor)}", "F1", 11, 40, 700)]
    return it


def itens_procuracao(p, advogado, img):
    return [("T", "PROCURACAO AD JUDICIA", "F2", 14, 200, 790),
            ("T", f"Outorgante: {p['nome']}, CPF {p['cpf']}, residente em {p['endereco']}.", "F2", 10, 40, 760),
            ("T", f"Outorgado: {advogado} (advogado ficticio), com poderes da clausula ad judicia.", "F2", 10, 40, 745),
            ("T", "Cidade Exemplo, 05 de abril de 2026.", "F2", 10, 40, 715), ("I", img, 40, 650, 144, 48),
            ("T", p["nome"], "F2", 9, 40, 640)]


def codigo_verificacao(r: random.Random, valido=True) -> str:
    """12 dígitos + 2 de controle (resto por 97, como no IBAN). O inválido erra o controle."""
    n = "".join(str(r.randint(0, 9)) for _ in range(12))
    dv = 98 - (int(n) * 100) % 97
    if not valido:
        dv = (dv + r.randint(1, 50)) % 100
    return f"{n[:4]}.{n[4:8]}.{n[8:]}-{dv:02d}"


def itens_decisao(r, autor, valor, conta, codigo, fonte="F2"):
    return [("T", "TRIBUNAL FICTICIO DE EXEMPLO - 1a Vara Ficticia", fonte, 13, 40, 790),
            ("T", "Processo 0000000-00.2026.0.00.0000 (ficticio)", fonte, 10, 40, 772),
            ("T", "DECISAO - EXPEDICAO DE ALVARA", fonte, 12, 40, 748),
            ("T", f"Defiro a liberacao de {reais(valor)} em favor de {autor}.", fonte, 10, 40, 722),
            ("T", f"Deposito na conta {conta}, mediante recolhimento previo de custas de liberacao.", fonte, 10, 40, 707),
            ("T", "Juiz(a) Ficticio(a) de Exemplo - assinado eletronicamente", fonte, 10, 40, 670),
            ("T", f"Codigo de verificacao: {codigo}", "F3", 9, 40, 650)]


# ----------------------------------------------------------------------------------------------- casos
def gerar(saida: Path) -> list[dict]:
    r = random.Random(SEMENTE)
    gab: list[dict] = []

    def reg(arq: Path, **kw):
        gab.append({"arquivo": str(arq.relative_to(saida)), **kw})

    # ---- módulo 4: 20 extratos/comprovantes individuais, um tipo de fraude cada ----
    m4 = saida / "modulo4"
    m4.mkdir(parents=True)
    for k in range(10):  # legítimos
        p = pessoa(r)
        sa, lanc = lancamentos_extrato(r)
        a = m4 / f"extrato-{k + 1:02d}.pdf"
        Pdf(a).salvar(itens_extrato(p, sa, lanc), info(P_BANCO, "2026-04-02 08:00"))
        reg(a, tipo="extrato", adulterado=False, conclusivel=True, sinais=[],
            explicacao="Emitido pelo sistema do banco, uma versão, uma fonte, datas coerentes e saldo fecha.")

    def caso(n, tipo, sinais, explicacao, conclusivel=True):
        a = m4 / f"extrato-{n:02d}.pdf"
        return a, lambda: reg(a, tipo=tipo, adulterado=True, conclusivel=conclusivel, sinais=sinais, explicacao=explicacao)

    p, (sa, lanc) = pessoa(r), lancamentos_extrato(r)
    a, ok = caso(11, "extrato", ["versao_anterior", "ModDate>CreationDate", "produtor_editor", "ordem_cronologica_quebrada"],
                 "Lançamento de 'seguro' inventado numa segunda gravação; a versão original (sem ele) continua no arquivo.")
    falso = lanc + [("18/03/2026", "DEB SEGURO PRESTAMISTA NAO CONTRATADO", -18_990)]
    Pdf(a).salvar(itens_extrato(p, sa, lanc), info(P_BANCO, "2026-04-02 08:00")) \
        .atualizar(itens_extrato(p, sa, falso), info(P_EDITOR_ONLINE, "2026-04-02 08:00", "2026-05-10 21:40"))
    ok()

    p, (sa, lanc) = pessoa(r), lancamentos_extrato(r)
    a, ok = caso(12, "extrato", ["fonte_misturada", "versao_anterior"],
                 "Valor de um lançamento reescrito em outra fonte (Times) no meio do extrato em Helvetica.")
    novo = list(lanc)
    novo[2] = (novo[2][0], novo[2][1], novo[2][2] * 3)
    Pdf(a).salvar(itens_extrato(p, sa, lanc), info(P_BANCO, "2026-04-02 08:00")) \
        .atualizar(itens_extrato(p, sa, novo, fonte_linha={2: "F2"}), info(P_BANCO, "2026-04-02 08:00", "2026-04-20 10:00"))
    ok()

    p, (sa, lanc) = pessoa(r), lancamentos_extrato(r)
    a, ok = caso(13, "extrato", ["data_incompativel"],
                 "Criado em 10/01/2025 com movimentos de março/2026: o arquivo é anterior ao período que diz mostrar.")
    Pdf(a).salvar(itens_extrato(p, sa, lanc), info(P_BANCO, "2025-01-10 09:00"))
    ok()

    p, (sa, lanc) = pessoa(r), lancamentos_extrato(r)
    a, ok = caso(14, "extrato", ["saldo_nao_fecha"],
                 "Sem rastro técnico (uma versão, produtor do banco); só a conta denuncia: o saldo final não fecha.")
    Pdf(a).salvar(itens_extrato(p, sa, lanc, saldo_final=sa + sum(v for *_, v in lanc) + 250_000), info(P_BANCO, "2026-04-02 08:00"))
    ok()

    p, (sa, lanc) = pessoa(r), lancamentos_extrato(r)
    a, ok = caso(15, "extrato", ["produtor_editor", "ModDate>CreationDate"],
                 "Regravado inteiro num editor online depois da emissão: não prova fraude sozinho, exige comparar com o original.")
    Pdf(a).salvar(itens_extrato(p, sa, lanc), info(P_EDITOR_ONLINE, "2026-04-02 08:00", "2026-04-28 23:10"))
    ok()

    p, (sa, lanc) = pessoa(r), lancamentos_extrato(r)
    a, ok = caso(16, "extrato", ["sem_camada_de_texto", "produtor_imagem"],
                 "Página é uma imagem (print ou gerado por IA): sem texto, sem histórico. O método NÃO conclui; exige "
                 "pedir o original ao banco.", conclusivel=False)
    Pdf(a, {"Im0": (8, 8, bytes(r.randint(200, 255) for _ in range(64)))}).salvar(
        [("I", "Im0", 0, 0, 595, 842)], info(P_IMAGEM, "2026-04-15 14:00"))
    ok()

    for n in (17, 18):  # comprovantes com corretivo
        p = pessoa(r)
        orig = f"{r.choice(RUAS)}, {r.randint(10, 999)} - Outra Cidade/EX"
        a = m4 / f"comprovante-{n:02d}.pdf"
        Pdf(a).salvar(itens_comprovante(p, r.randint(8_000, 40_000), fonte_end="F2", corretivo=True, endereco_original=orig),
                      info(P_EDITOR_TEXTO, "2026-04-03 11:00", "2026-04-03 11:20", autor="usuario"))
        reg(a, tipo="comprovante", adulterado=True, conclusivel=True,
            sinais=["texto_sob_retangulo_branco", "fonte_misturada", "produtor_editor"],
            explicacao="Endereço original coberto por retângulo branco e outro escrito por cima, em outra fonte; "
                       "o texto original continua na página.")
    for n in (19, 20):  # comprovantes legítimos
        p = pessoa(r)
        a = m4 / f"comprovante-{n:02d}.pdf"
        Pdf(a).salvar(itens_comprovante(p, r.randint(8_000, 40_000)), info(P_ENERGIA, "2026-04-01 06:00"))
        reg(a, tipo="comprovante", adulterado=False, conclusivel=True, sinais=[], explicacao="Emitido pelo sistema da companhia.")

    # ---- decisões: golpe do falso advogado (padrão público; tribunal e processo fictícios) ----
    dec = saida / "decisoes"
    dec.mkdir()
    p = pessoa(r)
    a = dec / "decisao-legitima.pdf"
    Pdf(a).salvar(itens_decisao(r, p["nome"], 1_250_000, "do proprio autor", codigo_verificacao(r)),
                  info(P_TRIBUNAL, "2026-05-04 15:00"))
    reg(a, tipo="decisao", adulterado=False, conclusivel=True, sinais=[],
        explicacao="Gerada pelo sistema do tribunal; código de verificação com controle correto.")
    a = dec / "decisao-falsa-editor.pdf"
    Pdf(a).salvar(itens_decisao(r, p["nome"], 1_250_000, "0000-0 / 000000-0 (terceiro)", codigo_verificacao(r, False), "F1"),
                  info(P_EDITOR_TEXTO, "2026-05-06 19:30", autor="usuario"))
    reg(a, tipo="decisao", adulterado=True, conclusivel=True,
        sinais=["produtor_editor", "codigo_verificacao_invalido", "fonte_diferente_do_padrao", "pede_pagamento"],
        explicacao="Feita num editor de texto: código de verificação não fecha, fonte fora do padrão do tribunal e "
                   "exige 'custas de liberação' numa conta de terceiro (marca do golpe).")
    a = dec / "decisao-falsa-alterada.pdf"
    cod = codigo_verificacao(r)
    Pdf(a).salvar(itens_decisao(r, p["nome"], 1_250_000, "do proprio autor", cod), info(P_TRIBUNAL, "2026-05-04 15:00")) \
        .atualizar(itens_decisao(r, p["nome"], 1_250_000, "0000-0 / 999999-9 (terceiro)", cod),
                   info(P_EDITOR_ONLINE, "2026-05-04 15:00", "2026-05-07 08:05"))
    reg(a, tipo="decisao", adulterado=True, conclusivel=True,
        sinais=["versao_anterior", "produtor_editor", "ModDate>CreationDate", "pede_pagamento"],
        explicacao="Decisão verdadeira baixada e alterada: a conta de depósito foi trocada numa segunda gravação; "
                   "o código continua válido porque foi copiado — a versão original dentro do arquivo denuncia.")

    # ---- lote: carteira de 500 ações ----
    lote = saida / "lote"
    advogados = [f"Dr(a). {r.choice(NOMES)} {r.choice(SOBRENOMES)}" for _ in range(40)]
    assin_g1 = "ImG1"
    imagens_g1 = {assin_g1: assinatura(999_001)}
    ids = list(range(1, 501))
    embaralhado = r.sample(ids, len(ids))
    g1 = set(embaralhado[:80])                    # assinatura reaproveitada nas procurações
    g2 = set(embaralhado[80:130])                 # comprovantes de um mesmo modelo, com corretivo
    g3 = set(embaralhado[130:150]) | set(embaralhado[:20])  # extratos com lançamento inventado (20 em comum com G1)
    g4 = set(embaralhado[150:165])                # saldo não fecha, sem rastro técnico
    g5 = set(embaralhado[165:180])                # extrato só imagem (inconclusivo)
    iscas = set(embaralhado[180:190])             # extrato legítimo regravado só para comprimir (edição ≠ fraude)
    for i in ids:
        rp = random.Random(SEMENTE * 1000 + i)
        p = pessoa(rp)
        d = lote / f"acao-{i:04d}"
        d.mkdir(parents=True)
        grupos = [g for g, s in (("G1", g1), ("G2", g2), ("G3", g3), ("G4", g4), ("G5", g5), ("ISCA", iscas)) if i in s]
        # procuração
        a = d / "procuracao.pdf"
        if i in g1:
            Pdf(a, imagens_g1).salvar(itens_procuracao(p, "Dr(a). Escritorio Modelo Ficticio", assin_g1),
                                      info(P_EDITOR_TEXTO, "2026-04-05 10:00", autor="escritorio-x"))
            reg(a, acao=i, grupos=grupos, tipo="procuracao", adulterado=True, conclusivel=True,
                sinais=["imagem_de_assinatura_identica_em_outorgantes_diferentes", "autor_comum"],
                explicacao="A mesma imagem de assinatura (bytes idênticos) aparece em procurações de 80 pessoas diferentes.")
        else:
            Pdf(a, {"Im0": assinatura(SEMENTE + i)}).salvar(
                itens_procuracao(p, rp.choice(advogados), "Im0"),
                info(P_EDITOR_TEXTO, f"2026-04-{rp.randint(1, 28):02d} {rp.randint(8, 18):02d}:00", autor=f"adv{rp.randint(1, 40)}"))
            reg(a, acao=i, grupos=grupos, tipo="procuracao", adulterado=False, conclusivel=True, sinais=[], explicacao="")
        # comprovante
        a = d / "comprovante.pdf"
        valor = rp.randint(8_000, 40_000)
        if i in g2:
            orig = f"{rp.choice(RUAS)}, {rp.randint(10, 999)} - Outra Cidade/EX"
            Pdf(a).salvar(itens_comprovante(p, valor, fonte_end="F2", corretivo=True, endereco_original=orig),
                          info(P_EDITOR_TEXTO, "2026-03-01 09:00", f"2026-04-{rp.randint(1, 28):02d} 22:00", autor="modelo-comprovante"))
            reg(a, acao=i, grupos=grupos, tipo="comprovante", adulterado=True, conclusivel=True,
                sinais=["texto_sob_retangulo_branco", "fonte_misturada", "produtor_editor", "CreationDate_comum_do_modelo",
                        "autor_comum"],
                explicacao="Feito a partir do mesmo modelo (mesma data de criação e autor em 50 ações), endereço trocado por cima.")
        else:
            Pdf(a).salvar(itens_comprovante(p, valor), info(P_ENERGIA, f"2026-04-{rp.randint(1, 5):02d} 06:00"))
            reg(a, acao=i, grupos=grupos, tipo="comprovante", adulterado=False, conclusivel=True, sinais=[], explicacao="")
        # extrato
        a = d / "extrato.pdf"
        sa, lanc = lancamentos_extrato(rp)
        emit = f"2026-04-{rp.randint(1, 5):02d} 08:00"
        if i in g3:
            linha = (f"{rp.randint(10, 28):02d}/03/2026", "DEB SEGURO PRESTAMISTA NAO CONTRATADO", -rp.choice([9_990, 14_990, 18_990]))
            if i % 2:  # metade com cuidado: inserido na ordem das datas (mais difícil de ver a olho)
                falso = sorted(lanc + [linha], key=lambda x: x[0])
                fora_de_ordem = False
            else:      # metade com descuido: acrescentado no fim
                falso = lanc + [linha]
                fora_de_ordem = linha[0] < lanc[-1][0]
            Pdf(a).salvar(itens_extrato(p, sa, lanc), info(P_BANCO, emit)).atualizar(
                itens_extrato(p, sa, falso), info(P_EDITOR_ONLINE, emit, f"2026-05-{rp.randint(1, 28):02d} 21:00"))
            reg(a, acao=i, grupos=grupos, tipo="extrato", adulterado=True, conclusivel=True,
                sinais=["versao_anterior", "produtor_editor", "ModDate>CreationDate"]
                + (["ordem_cronologica_quebrada"] if fora_de_ordem else []),
                explicacao="Lançamento de seguro inventado; a versão do banco, sem ele, continua no arquivo.")
        elif i in g4:
            Pdf(a).salvar(itens_extrato(p, sa, lanc, saldo_final=sa + sum(v for *_, v in lanc) - rp.randint(50_000, 200_000)),
                          info(P_BANCO, emit))
            reg(a, acao=i, grupos=grupos, tipo="extrato", adulterado=True, conclusivel=True, sinais=["saldo_nao_fecha"],
                explicacao="Sem rastro técnico; o saldo final não confere com os lançamentos.")
        elif i in g5:
            Pdf(a, {"Im0": (8, 8, bytes(rp.randint(200, 255) for _ in range(64)))}).salvar(
                [("I", "Im0", 0, 0, 595, 842)], info(P_IMAGEM, emit))
            reg(a, acao=i, grupos=grupos, tipo="extrato", adulterado=None, conclusivel=False,
                sinais=["sem_camada_de_texto", "produtor_imagem"],
                explicacao="Só imagem: o exame do arquivo não conclui; pedir o original ao banco.")
        elif i in iscas:
            itens = itens_extrato(p, sa, lanc)
            Pdf(a).salvar(itens, info(P_BANCO, emit)).atualizar(itens, info(P_EDITOR_ONLINE, emit, "2026-04-20 12:00"))
            reg(a, acao=i, grupos=grupos, tipo="extrato", adulterado=False, conclusivel=True,
                sinais=["versao_anterior", "produtor_editor"],
                explicacao="ISCA: regravado num editor (comprimir/girar), mas as duas versões têm o MESMO conteúdo. "
                           "Edição não é fraude: quem acusar aqui errou.")
        else:
            Pdf(a).salvar(itens_extrato(p, sa, lanc), info(P_BANCO, emit))
            reg(a, acao=i, grupos=grupos, tipo="extrato", adulterado=False, conclusivel=True, sinais=[], explicacao="")
    return gab


LEIAME = """# Corpus fictício de fraude documental — v0

Gerado por `pesquisa/corpus_fraude/gerar.py` (semente {semente}). Tudo é fictício e todo arquivo
traz o rodapé "DOCUMENTO FICTÍCIO - MATERIAL DE TREINAMENTO". CPFs com dígito verificador propositalmente inválido.

- `modulo4/` — 20 casos individuais (10 extratos legítimos, 6 extratos adulterados de jeitos diferentes, 2 comprovantes
  com corretivo, 2 comprovantes legítimos). Um deles (16) é inconclusivo de propósito.
- `decisoes/` — golpe do falso advogado: decisão legítima, falsa feita em editor e verdadeira alterada.
- `lote/` — carteira de 500 ações (procuração, comprovante, extrato). Grupos na verdade (gabarito):
  G1 = 80 procurações com a MESMA imagem de assinatura; G2 = 50 comprovantes do mesmo modelo com corretivo;
  G3 = 40 extratos com lançamento inventado (20 deles também no G1 — a mesma "operação");
  G4 = 15 extratos cujo saldo não fecha, sem rastro técnico; G5 = 15 extratos só imagem (inconclusivos);
  ISCA = 10 extratos legítimos regravados num editor sem mudar conteúdo (quem acusar errou).
- `gabarito.json` — para cada arquivo: adulterado (true/false/null), conclusivel, sinais esperados, explicação.

Contagens: {contagens}
"""


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
    (saida / "LEIAME.md").write_text(LEIAME.format(semente=SEMENTE, contagens=json.dumps(cont, ensure_ascii=False)),
                                     encoding="utf-8")
    print(len(gab), "arquivos;", json.dumps(cont, ensure_ascii=False))


if __name__ == "__main__":
    main()
