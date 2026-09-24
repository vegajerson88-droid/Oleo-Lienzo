"""Aritmética monetaria del proyecto.

El dinero se calcula siempre con `Decimal` y se redondea a dos decimales con
ROUND_HALF_UP. Usar `float` acumularía errores de coma flotante que acabarían
descuadrando facturas.
"""
from decimal import ROUND_HALF_UP, Decimal

CENTAVOS = Decimal("0.01")
CERO = Decimal("0.00")


def a_decimal(valor) -> Decimal:
    """Convierte cualquier número a Decimal con dos decimales exactos."""
    if isinstance(valor, Decimal):
        bruto = valor
    else:
        # str() evita heredar el error binario de un float como 0.1.
        bruto = Decimal(str(valor if valor is not None else 0))
    return bruto.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def calcular_linea(precio_unitario, cantidad: int, descuento=0) -> Decimal:
    """Subtotal de una línea: precio x cantidad - descuento (nunca negativo)."""
    bruto = a_decimal(precio_unitario) * Decimal(cantidad)
    neto = bruto - a_decimal(descuento)
    return a_decimal(max(neto, CERO))


def calcular_totales(subtotales: list, descuento_global, iva_tasa: Decimal) -> dict:
    """Desglose económico de una venta.

    Devuelve subtotal, descuento aplicado, impuestos y total. El descuento
    global nunca puede superar el subtotal, y el IVA se calcula sobre la base
    ya descontada, que es como lo exige la normativa colombiana.
    """
    subtotal = a_decimal(sum((a_decimal(s) for s in subtotales), CERO))
    descuento = min(a_decimal(descuento_global), subtotal)
    base_gravable = a_decimal(subtotal - descuento)
    impuestos = a_decimal(base_gravable * iva_tasa)
    total = a_decimal(base_gravable + impuestos)
    return {
        "subtotal": subtotal,
        "descuento": descuento,
        "base_gravable": base_gravable,
        "impuestos": impuestos,
        "total": total,
    }


def formato_cop(valor) -> str:
    """Formatea un importe como moneda colombiana: $ 1.250.000,00"""
    d = a_decimal(valor)
    entero, _, decimales = f"{d:.2f}".partition(".")
    negativo = entero.startswith("-")
    entero = entero.lstrip("-")
    # Separador de miles con punto, decimal con coma (convención es-CO).
    grupos = []
    while len(entero) > 3:
        grupos.insert(0, entero[-3:])
        entero = entero[:-3]
    grupos.insert(0, entero)
    return f"{'-' if negativo else ''}$ {'.'.join(grupos)},{decimales}"
