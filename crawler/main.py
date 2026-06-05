from __future__ import annotations

import argparse
import json
import sys

from crawler.client.trf5_client import TRF5Client
from crawler.parsers.process_parser import ProcessParser
from crawler.repositories.jsonl_repository import JsonlRepository
from crawler.settings import DEFAULT_JSONL_PATH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawler de consulta publica do TRF5.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_JSONL_PATH),
        help="Arquivo JSONL de saida. Padrao: %(default)s",
    )
    parser.add_argument(
        "--skip-save",
        action="store_true",
        help="Nao salva em JSONL.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime um array JSON no stdout.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    process_parser = subparsers.add_parser("process", help="Busca um processo por numero.")
    process_parser.add_argument("numero_processo")

    cnpj_parser = subparsers.add_parser("cnpj", help="Busca processos por CNPJ.")
    cnpj_parser.add_argument("cnpj")
    cnpj_parser.add_argument("--limit", type=int, default=None, help="Limita a quantidade de processos.")

    party_parser = subparsers.add_parser("party", help="Busca processos por nome da parte.")
    party_parser.add_argument("nome")
    party_parser.add_argument("--limit", type=int, default=None, help="Limita a quantidade de processos.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    client = TRF5Client(parser=ProcessParser())

    try:
        if args.command == "process":
            processes = [client.fetch_process(args.numero_processo)]
        elif args.command == "cnpj":
            processes = client.fetch_processes_by_cnpj(args.cnpj, limit=args.limit)
        else:
            processes = client.fetch_processes_by_party_name(args.nome, limit=args.limit)
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    if not args.skip_save:
        JsonlRepository(args.output).save_all(processes)

    if args.json:
        print(json.dumps(processes, ensure_ascii=False, indent=2))
    else:
        print(f"Processos encontrados: {len(processes)}")
        if not args.skip_save:
            print(f"JSONL: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
