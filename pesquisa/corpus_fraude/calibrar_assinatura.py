"""Calibra DIST_PERCEPTUAL do periciar-lote num conjunto SEPARADO (semente própria), nunca no v0/v1.

Mede a distância do mapa de tinta entre: (a) cópias recodificadas da MESMA assinatura; (b) assinaturas DIFERENTES.
O limiar bom fica entre o maior (a) e o menor (b). Uso: python3 calibrar_assinatura.py
"""

import random
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parents[1]))
from gerar import assinatura  # noqa: E402
from gerar_v1 import assinatura_recodificada  # noqa: E402
from periciar_lote import _hash_perceptual, _semelhanca  # noqa: E402


class _S:
    def __init__(self, w, h):
        self.attrs = {"Width": w, "Height": h}


def mapa(img):
    w, h, px = img
    return _hash_perceptual(_S(w, h), px)


def main():
    r = random.Random(5_550_001)
    bases = [assinatura(9_000_000 + k) for k in range(200)]
    mesma = [_semelhanca(mapa(b), mapa(assinatura_recodificada(b, r))) for b in bases for _ in range(5)]
    diferentes = [_semelhanca(mapa(a), mapa(b)) for i, a in enumerate(bases) for b in bases[i + 1:i + 6]]
    print(f"mesma assinatura recodificada: mín {min(mesma):.3f}, média {sum(mesma) / len(mesma):.3f} ({len(mesma)} pares)")
    print(f"assinaturas diferentes:        máx {max(diferentes):.3f}, média {sum(diferentes) / len(diferentes):.3f} ({len(diferentes)} pares)")
    for lim in (0.6, 0.7, 0.75, 0.8, 0.85, 0.9):
        fn = sum(s < lim for s in mesma) / len(mesma)
        fp = sum(s >= lim for s in diferentes) / len(diferentes)
        print(f"  limiar {lim:.2f}: perde {fn:.1%} das cópias, confunde {fp:.2%} das diferentes")
    calibrar_v2()


def calibrar_v2():
    """Assinaturas no estilo do v2 (Pillow), sementes 9_500_000+k, nunca as do corpus: (a) a MESMA digitalização
    recortada e recomprimida em JPEG; (b) a mesma pessoa assinando de novo (legítimo); (c) pessoas diferentes."""
    import io
    from gerar_v2 import assinatura_v2
    from PIL import Image

    def m_jpeg(img, q):
        b = io.BytesIO()
        img.save(b, format="JPEG", quality=q)
        d = Image.open(io.BytesIO(b.getvalue())).convert("L")
        return mapa((d.width, d.height, d.tobytes()))

    r = random.Random(5_550_002)
    copia, de_novo, diferentes = [], [], []
    bases = []
    for k in range(150):
        s = 9_500_000 + k
        dig = assinatura_v2(s, ruido=random.Random(s + 1), fundo=246)
        bases.append(m_jpeg(dig, 85))
        for _ in range(3):
            c = dig.crop((r.randint(0, 2), r.randint(0, 2), dig.width - r.randint(0, 2), dig.height - r.randint(0, 2)))
            copia.append(_semelhanca(bases[-1], m_jpeg(c, r.randint(60, 92))))
        ref = assinatura_v2(s)
        for j in range(3):
            de_novo.append(_semelhanca(mapa((ref.width, ref.height, ref.tobytes())),
                                       mapa((lambda i: (i.width, i.height, i.tobytes()))(
                                           assinatura_v2(s, jitter=random.Random(s * 10 + j))))))
    for i, a in enumerate(bases):
        diferentes += [_semelhanca(a, b) for b in bases[i + 1:i + 6]]
    print("\nestilo v2 + JPEG:")
    for nome, xs in (("cópia recomprimida", copia), ("mesma pessoa de novo", de_novo), ("pessoas diferentes", diferentes)):
        print(f"  {nome:22} mín {min(xs):.3f}  média {sum(xs) / len(xs):.3f}  máx {max(xs):.3f}  ({len(xs)} pares)")
    for lim in (0.7, 0.75, 0.8, 0.85, 0.9):
        print(f"  limiar {lim:.2f}: perde {sum(s < lim for s in copia) / len(copia):.1%} das cópias, "
              f"junta {sum(s >= lim for s in de_novo) / len(de_novo):.1%} das 'de novo', "
              f"confunde {sum(s >= lim for s in diferentes) / len(diferentes):.2%} das diferentes")


if __name__ == "__main__":
    main()
