"""Corpus fictício de fraude documental v1 — teste ÀS CEGAS do periciar-lote (ver pre-registro-v1.md).

Mesmas garantias do v0 (tudo fictício, rodapé de treinamento, CPF com dígito inválido, determinístico), com
fraudes que a ferramenta congelada não foi feita para pegar e legítimos que podem enganar.

Uso: python3 -I gerar_v1.py <pasta_saida>
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar import (P_BANCO, P_EDITOR_ONLINE, P_EDITOR_TEXTO, P_ENERGIA, Pdf, assinatura, info,  # noqa: E402
                   itens_comprovante, itens_extrato, itens_procuracao, lancamentos_extrato, pessoa)

SEMENTE = 20261117
P_OTIMIZADOR = "OtimizadorPDF 4.0"


def imagem_padrao(semente: int, w=120, h=40) -> tuple[int, int, bytes]:
    """Logotipo/papel timbrado fictício: faixas e blocos determinados pela semente."""
    r = random.Random(semente)
    px = bytearray([255] * (w * h))
    for _ in range(6):
        x0, y0 = r.randint(0, w - 20), r.randint(0, h - 8)
        tom = r.randint(20, 160)
        for y in range(y0, min(h, y0 + r.randint(3, 10))):
            for x in range(x0, min(w, x0 + r.randint(10, 40))):
                px[y * w + x] = tom
    return w, h, bytes(px)


def assinatura_recodificada(base: tuple[int, int, bytes], r: random.Random) -> tuple[int, int, bytes]:
    """A mesma assinatura 'recortada e salva de novo': desloca 0–1 px, muda levemente o tom e acrescenta ruído.
    A olho é igual; os bytes nunca são."""
    w, h, px = base
    dx, dy = r.choice((-1, 0, 1)), r.choice((-1, 0, 1))
    novo = bytearray([255] * (w * h))
    for y in range(h):
        for x in range(w):
            sx, sy = x - dx, y - dy
            v = px[sy * w + sx] if 0 <= sx < w and 0 <= sy < h else 255
            if v < 128:
                v = max(0, min(255, v + r.randint(-12, 12)))
            elif r.random() < 0.01:
                v = 240
            novo[y * w + x] = v
    return w, h, bytes(novo)


def emissao(r: random.Random, dia_max=5) -> str:
    return f"2026-04-{r.randint(1, dia_max):02d} {r.randint(6, 9):02d}:{r.randint(0, 59):02d}"


def gerar(saida: Path) -> list[dict]:
    r = random.Random(SEMENTE)
    gab = []
    lote = saida / "lote"
    logo_banco, logo_energia = imagem_padrao(1), imagem_padrao(2)
    escritorios = [{"nome": f"Escritorio Ficticio {k + 1:02d}", "timbre": imagem_padrao(100 + k)} for k in range(40)]
    fraude_esc = {"nome": "Escritorio Ficticio Modelo", "timbre": imagem_padrao(999)}
    assin_mestra = assinatura(777_001)

    ids = list(range(1, 501))
    emb = r.sample(ids, len(ids))
    h1 = set(emb[:60])
    h2 = set(emb[60:80]) | set(emb[:20])          # 20 em comum com H1
    h3 = set(emb[80:110])
    h4 = set(emb[110:130])
    h5 = set(emb[130:145])
    isca = set(emb[145:160])
    # clientes legítimos espalhados pelos 40 escritórios, com tamanhos desiguais (alguns com muitos clientes)
    pesos = [r.choice((1, 1, 2, 3, 5)) for _ in escritorios]

    def reg(a, i, grupos, tipo, adulterado, sinais, explicacao, conclusivel=True):
        gab.append({"arquivo": str(a.relative_to(saida)), "acao": i, "grupos": grupos, "tipo": tipo,
                    "adulterado": adulterado, "conclusivel": conclusivel, "sinais": sinais, "explicacao": explicacao})

    for i in ids:
        rp = random.Random(SEMENTE * 1000 + i)
        p = pessoa(rp)
        d = lote / f"acao-{i:04d}"
        d.mkdir(parents=True)
        grupos = [g for g, s in (("H1", h1), ("H2", h2), ("H3", h3), ("H4", h4), ("H5", h5), ("ISCA", isca)) if i in s]

        # procuração (papel timbrado do escritório + assinatura do cliente)
        a = d / "procuracao.pdf"
        if i in h1:
            esc = fraude_esc
            imgs = {"Tim": esc["timbre"], "Ass": assinatura_recodificada(assin_mestra, rp)}
        else:
            esc = rp.choices(escritorios, weights=pesos)[0]
            imgs = {"Tim": esc["timbre"], "Ass": assinatura(SEMENTE + i)}
        itens = [("I", "Tim", 40, 790, 120, 40)] + [x if x[0] != "T" or x[5] < 790 else (x[0], x[1], x[2], x[3], x[4], 770)
                                                     for x in itens_procuracao(p, esc["nome"], "Ass")]
        Pdf(a, imgs).salvar(itens, info(P_EDITOR_TEXTO, f"2026-04-{rp.randint(1, 28):02d} {rp.randint(8, 18):02d}:{rp.randint(0, 59):02d}",
                                        autor=esc["nome"].lower().replace(" ", "-")))
        if i in h1:
            reg(a, i, grupos, "procuracao", True, ["assinatura_igual_a_olho_bytes_diferentes"],
                "A mesma assinatura, recortada e salva de novo, em 60 procurações de pessoas diferentes.")
        else:
            reg(a, i, grupos, "procuracao", False, [],
                "Legítima. O papel timbrado do escritório se repete em todos os clientes dele (não é fraude).")

        # comprovante (com logotipo da companhia)
        a = d / "comprovante.pdf"
        valor = rp.randint(8_000, 40_000)
        logo = [("I", "Logo", 440, 780, 120, 40)]
        if i in h3:
            itens = logo + itens_comprovante(p, valor, fonte_end="F2")
            Pdf(a, {"Logo": logo_energia}).salvar(itens, {})
            reg(a, i, grupos, "comprovante", True, ["metadados_apagados", "fonte_fora_do_padrao"],
                "Endereço trocado e arquivo regerado com os metadados apagados (antiperícia simples).")
        else:
            Pdf(a, {"Logo": logo_energia}).salvar(logo + itens_comprovante(p, valor), info(P_ENERGIA, emissao(rp)))
            reg(a, i, grupos, "comprovante", False, [], "Legítimo, emitido pelo sistema da companhia.")

        # extrato (com logotipo do banco)
        a = d / "extrato.pdf"
        sa, lanc = lancamentos_extrato(rp)
        logo = [("I", "Logo", 440, 790, 120, 40)]
        emit = emissao(rp)
        imgs = {"Logo": logo_banco}
        if i in h2:
            linha = (f"{rp.randint(10, 28):02d}/03/2026", "DEB SEGURO PRESTAMISTA NAO CONTRATADO", -rp.choice([9_990, 14_990]))
            falso = sorted(lanc + [linha], key=lambda x: x[0])
            Pdf(a, imgs).salvar(logo + itens_extrato(p, sa, falso), info(P_EDITOR_ONLINE, emit, emit))
            reg(a, i, grupos, "extrato", True, ["produtor_fora_do_padrao", "sem_versao_anterior"],
                "Refeito inteiro num editor com um lançamento inventado: não há versão do banco dentro do arquivo.")
        elif i in h4:
            novo = [(dt, h, v * 2 if h.startswith("TARIFA") else v) for dt, h, v in lanc]
            Pdf(a, imgs).salvar(logo + itens_extrato(p, sa, lanc), info(P_BANCO, emit)).atualizar(
                logo + itens_extrato(p, sa, novo), info(P_BANCO, emit, f"2026-04-{rp.randint(10, 28):02d} 20:{rp.randint(10, 59)}"))
            reg(a, i, grupos, "extrato", True, ["versao_anterior", "saldo_fecha_mesmo_assim"],
                "Tarifa dobrada numa segunda gravação, mesma fonte e produtor, saldo recalculado: só a versão anterior denuncia.")
        elif i in h5:
            Pdf(a, imgs).salvar(logo + itens_extrato(p, sa, lanc), info(P_BANCO, f"2026-02-{rp.randint(18, 22):02d} 10:00"))
            reg(a, i, grupos, "extrato", True, ["anacronismo_sutil"],
                "Arquivo criado em fevereiro mostrando movimentos de março inteiro (até 31/03): impossível.")
        elif i in isca:
            Pdf(a, imgs).salvar(logo + itens_extrato(p, sa, lanc), info(P_OTIMIZADOR, emit, "2026-04-25 13:00"))
            reg(a, i, grupos, "extrato", False, ["produtor_fora_do_padrao"],
                "ISCA: regravado inteiro por um otimizador, sem mudar conteúdo. Edição não é fraude.")
        else:
            Pdf(a, imgs).salvar(logo + itens_extrato(p, sa, lanc), info(P_BANCO, emit))
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
        k = f"{g['tipo']}:{'adulterado' if g['adulterado'] else 'legitimo'}"
        cont[k] = cont.get(k, 0) + 1
    print(len(gab), "arquivos;", json.dumps(cont, ensure_ascii=False))


if __name__ == "__main__":
    main()
