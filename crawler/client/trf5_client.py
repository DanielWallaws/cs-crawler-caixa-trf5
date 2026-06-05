from __future__ import annotations

from urllib.parse import quote

import requests

from crawler.parsers.process_parser import ProcessParser
from crawler import settings


class TRF5Client:
    def __init__(
        self,
        parser: ProcessParser,
        base_url: str = settings.BASE_URL,
        timeout: int = settings.REQUEST_TIMEOUT,
        session: requests.Session | None = None,
    ) -> None:
        self.parser = parser
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": settings.USER_AGENT})

    def fetch_process(self, process_number: str) -> dict[str, object]:
        html = self._get(f"/processo/{process_number}")
        return self.parser.parse_process(html)

    def search_process_numbers_by_cnpj(self, cnpj: str, limit: int | None = None) -> list[str]:
        normalized_cnpj = self._normalize_digits(cnpj)
        return self._search_paginated(
            path_template="/processo/cpf/porData/ativos/{term}/{page}",
            term=normalized_cnpj,
            limit=limit,
        )

    def search_process_numbers_by_party_name(
        self,
        party_name: str,
        limit: int | None = None,
    ) -> list[str]:
        encoded_name = quote(party_name.strip(), safe="/")
        return self._search_paginated(
            path_template="/processo/nomeparte/porData/ativos/{term}/{page}",
            term=encoded_name,
            limit=limit,
        )

    def fetch_processes_by_cnpj(self, cnpj: str, limit: int | None = None) -> list[dict[str, object]]:
        return [self.fetch_process(number) for number in self.search_process_numbers_by_cnpj(cnpj, limit)]

    def fetch_processes_by_party_name(self, party_name: str, limit: int | None = None) -> list[dict[str, object]]:
        return [
            self.fetch_process(number)
            for number in self.search_process_numbers_by_party_name(party_name, limit)
        ]

    def _search_paginated(
        self,
        path_template: str,
        term: str,
        limit: int | None = None,
    ) -> list[str]:
        collected: list[str] = []
        seen: set[str] = set()
        total: int | None = None
        page = 0

        while True:
            html = self._get(path_template.format(term=term, page=page))
            page_total, process_numbers = self.parser.parse_search_results(html)

            if total is None:
                total = page_total

            if not process_numbers:
                break

            for process_number in process_numbers:
                if process_number in seen:
                    continue
                seen.add(process_number)
                collected.append(process_number)
                if limit is not None and len(collected) >= limit:
                    return collected

            if total is not None and len(collected) >= total:
                break

            page += 1

        return collected

    def _get(self, path: str) -> str:
        response = self.session.get(
            f"{self.base_url}{path}", timeout=self.timeout)
        response.raise_for_status()
        response.encoding = "iso-8859-1"
        return response.text

    def _normalize_digits(self, value: str) -> str:
        digits = "".join(char for char in value if char.isdigit())
        if not digits:
            raise ValueError("O valor informado nao contem digitos.")
        return digits
