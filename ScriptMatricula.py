#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from typing import List, Set, Tuple


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


def extrair_periodos_matriculados(texto: str) -> Tuple[List[str], int]:
    periodos: Set[str] = set()
    total_disciplinas = 0

    for linha in texto.splitlines():
        if "MATRICULADO" not in linha.upper():
            continue

        m = re.match(r"^\s*(\d{4}\.\d)\s+", linha)
        if m:
            periodos.add(m.group(1))
        total_disciplinas += 1

    return sorted(periodos), total_disciplinas


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica matrícula ativa com base na situação dos componentes curriculares."
    )
    parser.add_argument("pdf", help="Caminho do PDF do histórico acadêmico.")
    args = parser.parse_args()

    try:
        texto = pdf_para_texto(args.pdf)
        periodos, qtd_matriculado = extrair_periodos_matriculados(texto)
    except (RuntimeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    matriculado = qtd_matriculado > 0

    print("Verificação de matrícula")
    print(f"Aluno matriculado: {'SIM' if matriculado else 'NÃO'}")
    print(f"Componentes com situação MATRICULADO: {qtd_matriculado}")
    print(
        "Períodos com matrícula: "
        + (", ".join(periodos) if periodos else "nenhum encontrado")
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
