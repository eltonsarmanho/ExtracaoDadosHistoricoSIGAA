#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from typing import Dict


COLUNAS = ["obrigatorias", "optativos", "extensao", "complementares", "total"]


def pdf_para_texto(caminho_pdf: str) -> str:
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", caminho_pdf, "-"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise RuntimeError("Comando 'pdftotext' não encontrado no sistema.")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Falha ao converter PDF em texto: {exc.stderr.strip()}")
    return proc.stdout


def extrair_linha_valores(texto: str, rotulo: str) -> Dict[str, int]:
    match = re.search(rf"^\s*{rotulo}\s+(.*)$", texto, flags=re.MULTILINE | re.IGNORECASE)
    if not match:
        raise ValueError(f"Linha '{rotulo}' não encontrada na seção de carga horária.")

    numeros = [int(n) for n in re.findall(r"(\d+)\s*h", match.group(1), flags=re.IGNORECASE)]
    if len(numeros) < 5:
        raise ValueError(f"Linha '{rotulo}' com formato inesperado: {match.group(0)}")

    return dict(zip(COLUNAS, numeros[:5]))


def extrair_carga_horaria(texto: str) -> Dict[str, Dict[str, int]]:
    if "Carga Horária Integralizada/Pendente" not in texto:
        raise ValueError("Seção 'Carga Horária Integralizada/Pendente' não encontrada no PDF.")

    return {
        "exigido": extrair_linha_valores(texto, "Exigido"),
        "integralizado": extrair_linha_valores(texto, "Integralizado"),
        "pendente": extrair_linha_valores(texto, "Pendente"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extrai Carga Horária Integralizada/Pendente de um histórico PDF."
    )
    parser.add_argument("pdf", help="Caminho do PDF do histórico acadêmico.")
    args = parser.parse_args()

    try:
        texto = pdf_para_texto(args.pdf)
        carga = extrair_carga_horaria(texto)
    except (RuntimeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    exigido_total = carga["exigido"]["total"]
    integralizado_total = carga["integralizado"]["total"]
    pendente_total = carga["pendente"]["total"]
    carga_completa = pendente_total == 0 and integralizado_total >= exigido_total

    print("Carga Horária Integralizada/Pendente")
    print(f"Exigido (total): {exigido_total}h")
    print(f"Integralizado (total): {integralizado_total}h")
    print(f"Pendente (total): {pendente_total}h")
    print(f"Carga horária completa: {'SIM' if carga_completa else 'NÃO'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
