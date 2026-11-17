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


if __name__ == "__main__":
    main()
