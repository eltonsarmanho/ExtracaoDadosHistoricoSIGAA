#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import BinaryIO, Union


PdfInput = Union[str, os.PathLike, bytes, bytearray, BinaryIO]


class StatusAlunoExtractor:
    @staticmethod
    def _pdf_to_text(pdf_input: PdfInput) -> str:
        if isinstance(pdf_input, (str, os.PathLike)):
            return StatusAlunoExtractor._run_pdftotext(Path(pdf_input))

        if isinstance(pdf_input, (bytes, bytearray)):
            return StatusAlunoExtractor._run_pdftotext_bytes(bytes(pdf_input))

        if hasattr(pdf_input, "read"):
            raw = pdf_input.read()
            if not isinstance(raw, (bytes, bytearray)):
                raise ValueError("Arquivo de upload inválido: esperado conteúdo binário PDF.")
            return StatusAlunoExtractor._run_pdftotext_bytes(bytes(raw))

        raise TypeError(
            "Tipo de entrada inválido. Use caminho (str/path), bytes ou arquivo de upload (file-like)."
        )

    @staticmethod
    def _run_pdftotext(pdf_path: Path) -> str:
        try:
            proc = subprocess.run(
                ["pdftotext", "-layout", str(pdf_path), "-"],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("Comando 'pdftotext' não encontrado no sistema.") from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            raise RuntimeError(f"Falha ao converter PDF em texto: {stderr}") from exc
        return proc.stdout

    @staticmethod
    def _run_pdftotext_bytes(pdf_bytes: bytes) -> str:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            return StatusAlunoExtractor._run_pdftotext(Path(tmp.name))

    @staticmethod
    def aluno_integralizou(pdf_input: PdfInput) -> bool:
        texto = StatusAlunoExtractor._pdf_to_text(pdf_input)

        # Captura a linha "Pendente ... Total", pegando o último número (total).
        match = re.search(
            r"^\s*Pendente\s+.*?(\d+)\s*h\s*$",
            texto,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        if not match:
            raise ValueError("Linha 'Pendente' não encontrada na seção de carga horária.")

        pendente_total = int(match.group(1))
        return pendente_total == 0

    @staticmethod
    def aluno_matriculado(pdf_input: PdfInput) -> bool:
        texto = StatusAlunoExtractor._pdf_to_text(pdf_input)
        return "MATRICULADO" in texto.upper()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida status do aluno (integralização e matrícula) a partir de PDF."
    )
    parser.add_argument("pdf", help="Caminho do PDF do histórico acadêmico.")
    args = parser.parse_args()

    integralizou = StatusAlunoExtractor.aluno_integralizou(args.pdf)
    matriculado = StatusAlunoExtractor.aluno_matriculado(args.pdf)
    # Com upload (frontend/backend):

    # StatusAlunoExtractor.aluno_integralizou(file.read())
    # StatusAlunoExtractor.aluno_matriculado(file) (objeto com .read())


    print(f"Integralizou: {integralizou}")
    print(f"Matriculado: {matriculado}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
