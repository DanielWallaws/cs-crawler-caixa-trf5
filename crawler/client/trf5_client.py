from urllib.parse import quote

import requests

from crawler import settings


class TRF5Client:
    """Request search and detail pages from the TRF5 consultation system."""

    def __init__(
        self,
        parser,
        base_url=settings.BASE_URL,
        timeout=settings.REQUEST_TIMEOUT,
        session=None,
        progress=None,
    ):
        self.parser = parser
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.progress = progress
        self.session.headers.update({"User-Agent": settings.USER_AGENT})

    def fetch_process(self, process_number) -> dict:
        """Fetch and parse one process detail page."""

        html = self._get(f"/processo/{process_number}")
        return self.parser.parse_process(html)

    def search_process_numbers_by_cnpj(self, cnpj, limit=None) -> list:
        """Search active process numbers by CNPJ."""

        normalized_cnpj = self._normalize_digits(cnpj)
        return self._search_paginated(
            path_template="/processo/cpf/porData/ativos/{term}/{page}",
            term=normalized_cnpj,
            limit=limit,
            progress_label=f"CNPJ {cnpj}",
        )

    def search_process_numbers_by_party_name(
        self,
        party_name,
        limit=None,
    ) -> list:
        """Search active process numbers by party name and S/A row filter."""

        encoded_name = quote(party_name.strip(), safe="")
        return self._search_paginated(
            path_template=(
                "/processo/nomeparte/porProcesso/ativos/exata/{term}/{page}"
            ),
            term=encoded_name,
            limit=limit,
            name_filter=settings.PARTY_NAME_REQUIRED_TEXT,
            progress_label=f"parte {party_name}",
        )

    def fetch_processes_by_cnpj(self, cnpj, limit=None) -> list:
        """Search by CNPJ and fetch details for each result."""

        return self._fetch_processes(
            self.search_process_numbers_by_cnpj(cnpj, limit)
        )

    def fetch_processes_by_party_name(self, party_name, limit=None) -> list:
        """Search by party name and fetch details for each filtered result."""

        process_numbers = self.search_process_numbers_by_party_name(
            party_name,
            limit,
        )
        return self._fetch_processes(process_numbers)

    def _search_paginated(
        self,
        path_template,
        term,
        limit=None,
        name_filter=None,
        progress_label=None,
    ) -> list:
        """Walk paginated search pages and collect process numbers."""
        collected = []
        seen = set()
        total = None
        scanned = 0
        page = 0

        while True:
            html = self._get(path_template.format(term=term, page=page))
            page_total, process_numbers, page_size = (
                self.parser.parse_search_results(
                    html,
                    name_filter=name_filter,
                )
            )

            if total is None:
                total = page_total

            if not process_numbers and not page_size:
                break

            scanned += page_size
            reached_limit = False
            for process_number in process_numbers:
                if process_number in seen:
                    continue
                seen.add(process_number)
                collected.append(process_number)
                if limit is not None and len(collected) >= limit:
                    reached_limit = True
                    break

            self._log_search_page(
                progress_label,
                page,
                total,
                page_size,
                len(process_numbers),
                len(collected),
            )
            if reached_limit:
                return collected

            if total is not None and scanned >= total:
                break

            page += 1

        return collected

    def _fetch_processes(self, process_numbers) -> list:
        return [self.fetch_process(number) for number in process_numbers]

    def _get(self, path) -> str:
        response = self.session.get(
            f"{self.base_url}{path}",
            timeout=self.timeout,
        )
        response.raise_for_status()
        response.encoding = "iso-8859-1"
        return response.text

    def _normalize_digits(self, value) -> str:
        digits = "".join(char for char in value if char.isdigit())
        if not digits:
            raise ValueError("O valor informado nao contem digitos.")
        return digits

    def _log_search_page(
        self,
        progress_label,
        page,
        total,
        page_size,
        selected_count,
        collected_count,
    ):
        if self.progress is None or progress_label is None:
            return

        message = (
            f"Busca {progress_label}: página {page + 1}, "
            f"{page_size} linhas, {selected_count} selecionados, "
            f"{collected_count} únicos"
        )
        if total is not None:
            message = f"{message}, total {total}"
        self.progress(message)
