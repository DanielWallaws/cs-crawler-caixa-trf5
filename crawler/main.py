import sys

from crawler import settings
from crawler.client.trf5_client import TRF5Client
from crawler.parsers.process_parser import ProcessParser
from crawler.repositories.jsonl_repository import JsonlRepository


def main(argv=None) -> int:
    """Run the assessment crawler."""

    args = sys.argv[1:] if argv is None else argv
    if args:
        print(
            "Erro: este crawler nao recebe argumentos. "
            "Execute: python3 -m crawler.main",
            file=sys.stderr,
        )
        return 2

    client = TRF5Client(parser=ProcessParser())

    try:
        processes = fetch_assessment_processes(client)
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    JsonlRepository(settings.DEFAULT_JSONL_PATH).save_all(processes)
    print(f"Processos encontrados: {len(processes)}")
    print(f"JSONL: {settings.DEFAULT_JSONL_PATH}")

    return 0


def fetch_assessment_processes(client) -> list:
    """Fetch and consolidate the assessment process set."""

    process_numbers = list(settings.KNOWN_PROCESSES)

    for cnpj in settings.KNOWN_CNPJS:
        process_numbers.extend(client.search_process_numbers_by_cnpj(cnpj))

    for party in settings.KNOWN_PARTIES:
        process_numbers.extend(
            client.search_process_numbers_by_party_name(party)
        )

    return [
        client.fetch_process(process_number)
        for process_number in _unique(process_numbers)
    ]


def _unique(values):
    """Return a list of unique values, preserving the original order."""

    seen = set()
    unique_values = []

    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)

    return unique_values


if __name__ == "__main__":
    raise SystemExit(main())
