import sys

from crawler import settings
from crawler.client.trf5_client import TRF5Client
from crawler.parsers.process_parser import ProcessParser
from crawler.repositories.jsonl_repository import JsonlRepository


def main(argv=None) -> int:
    """Run the configured crawler flow and persist the results."""

    args = sys.argv[1:] if argv is None else argv
    if args:
        print(
            "Erro: este crawler nao recebe argumentos. "
            "Execute: python3 -m crawler.main",
            file=sys.stderr,
        )
        return 2

    client = TRF5Client(parser=ProcessParser(), progress=_log)
    repository = JsonlRepository(settings.DEFAULT_JSONL_PATH)

    try:
        process_numbers = collect_configured_process_numbers(client)
        saved_count = fetch_and_save_processes(
            client,
            repository,
            process_numbers,
        )
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"Processos encontrados: {saved_count}")
    print(f"JSONL: {settings.DEFAULT_JSONL_PATH}")

    return 0


def collect_configured_process_numbers(client) -> list:
    """Collect and deduplicate configured process numbers."""

    process_numbers = list(settings.KNOWN_PROCESSES)
    _log(f"Processos conhecidos configurados: {len(process_numbers)}")

    for cnpj in settings.KNOWN_CNPJS:
        _log(f"Buscando processos por CNPJ: {cnpj}")
        process_numbers.extend(client.search_process_numbers_by_cnpj(cnpj))

    for party in settings.KNOWN_PARTIES:
        _log(f"Buscando processos por nome da parte: {party}")
        process_numbers.extend(
            client.search_process_numbers_by_party_name(party)
        )

    unique_numbers = _unique(process_numbers)
    _log(f"Processos consolidados sem duplicidade: {len(unique_numbers)}")
    return unique_numbers


def fetch_and_save_processes(client, repository, process_numbers) -> int:
    """Fetch process details and persist them in JSONL batches."""

    batch = []
    saved_count = 0
    total = len(process_numbers)

    for index, process_number in enumerate(process_numbers, start=1):
        _log(f"Consultando detalhes {index}/{total}: {process_number}")
        batch.append(client.fetch_process(process_number))

        if len(batch) >= settings.SAVE_BATCH_SIZE:
            repository.save_all(batch)
            saved_count += len(batch)
            _log(f"Lote salvo em {settings.DEFAULT_JSONL_PATH}")
            batch = []

    if batch:
        repository.save_all(batch)
        saved_count += len(batch)
        _log(f"Lote final salvo em {settings.DEFAULT_JSONL_PATH}")

    return saved_count


def _unique(values) -> list:
    """Return a list of unique values, preserving the original order."""

    seen = set()
    unique_values = []

    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)

    return unique_values


def _log(message):
    print(message, file=sys.stderr, flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
