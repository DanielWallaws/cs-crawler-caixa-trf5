from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

NOT_FOUND_MESSAGE = "O processo é inexistente ou tramita em segredo de justiça."
PROCESS_NUMBER_PATTERN = re.compile(
    r"PROCESSO\s+N[º°o]\s*(?P<numero>[0-9.\-]+)?(?:\s*\((?P<legado>[0-9.\-]+)\))?",
    re.IGNORECASE | re.DOTALL,
)
AUTUACAO_PATTERN = re.compile(r"AUTUADO EM\s+(\d{2}/\d{2}/\d{4})")
TOTAL_PATTERN = re.compile(r"Total:\s*(\d+)")
MOVEMENT_PATTERN = re.compile(r"^Em\s+(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})\s*(.*)$", re.DOTALL)

class ProcessParser:
    def parse_process(self, html: str) -> dict[str, object]:
        if self.is_not_found(html):
            raise ValueError("Processo inexistente ou em segredo de justiça.")

        soup = BeautifulSoup(html, "html.parser")
        page_text = self._normalized_text(soup)

        numero_processo, numero_legado = self._extract_process_numbers(page_text)
        data_autuacao = self._extract_autuacao(page_text)
        relator, envolvidos = self._extract_participants(soup)
        movimentacoes = self._extract_movements(soup)

        numero_processo = numero_processo or numero_legado
        if not numero_processo:
            raise ValueError("Nao foi possivel identificar o numero do processo.")

        return {
            "numero_processo": numero_processo,
            "numero_legado": numero_legado or "",
            "data_autuacao": data_autuacao or "",
            "relator": relator or "",
            "envolvidos": envolvidos,
            "movimentacoes": movimentacoes,
        }

    def parse_search_results(self, html: str) -> tuple[int, list[str]]:
        if self.is_not_found(html):
            return 0, []

        soup = BeautifulSoup(html, "html.parser")
        page_text = self._normalized_text(soup)

        if self.is_process_detail(html):
            process = self.parse_process(html)
            return 1, [str(process["numero_processo"])]

        result_table = soup.find("table", class_="consulta_resultados")
        if result_table is None:
            raise ValueError("Tabela de resultados nao encontrada.")

        process_numbers: list[str] = []
        for anchor in result_table.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href.startswith("/processo/"):
                continue

            process_number = href.rsplit("/", 1)[-1].strip()
            if process_number and process_number not in process_numbers:
                process_numbers.append(process_number)

        total_match = TOTAL_PATTERN.search(page_text)
        total = int(total_match.group(1)) if total_match else len(process_numbers)

        return total, process_numbers

    def is_process_detail(self, html: str) -> bool:
        return "PROCESSO N" in html and "AUTUADO EM" in html

    def is_not_found(self, html: str) -> bool:
        return NOT_FOUND_MESSAGE in html

    def _extract_process_numbers(self, page_text: str) -> tuple[str | None, str | None]:
        match = PROCESS_NUMBER_PATTERN.search(page_text)
        if not match:
            return None, None

        numero_processo = self._clean_optional_text(match.group("numero"))
        numero_legado = self._clean_optional_text(match.group("legado"))
        return numero_processo, numero_legado

    def _extract_autuacao(self, page_text: str) -> str | None:
        match = AUTUACAO_PATTERN.search(page_text)
        if not match:
            return None
        return self._to_iso_date(match.group(1))

    def _extract_participants(self, soup: BeautifulSoup) -> tuple[str | None, list[dict[str, str]]]:
        participant_table = None
        for table in soup.find_all("table"):
            text = self._normalized_text(table)
            if "RELATOR" in text:
                participant_table = table
                break

        if participant_table is None:
            return None, []

        relator: str | None = None
        envolvidos: list[dict[str, str]] = []

        for row in participant_table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            papel = self._clean_label(cells[0].get_text(" ", strip=True))
            nome = self._clean_value(cells[1].get_text(" ", strip=True))
            if not papel or not nome:
                continue

            if papel.upper() == "RELATOR":
                relator = nome
                continue

            envolvidos.append({"papel": papel, "nome": nome})

        return relator, envolvidos

    def _extract_movements(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        movements: list[dict[str, str]] = []

        for table in soup.find_all("table"):
            text = self._normalized_text(table)
            match = MOVEMENT_PATTERN.match(text)
            if not match:
                continue

            movement_date = self._to_iso_datetime(match.group(1))
            movement_text = self._clean_value(match.group(2))
            if movement_text:
                movements.append({"data": movement_date, "texto": movement_text})

        return movements

    def _normalized_text(self, node: BeautifulSoup | Tag) -> str:
        parts = [" ".join(chunk.split()) for chunk in node.get_text("\n").splitlines()]
        return " ".join(part for part in parts if part).strip()

    def _clean_label(self, value: str | None) -> str:
        if value is None:
            return ""
        return value.strip().rstrip(":").strip()

    def _clean_value(self, value: str | None) -> str:
        if value is None:
            return ""
        cleaned = " ".join(value.split()).strip()
        if cleaned.startswith(":"):
            cleaned = cleaned[1:].strip()
        return cleaned

    def _clean_optional_text(self, value: str | None) -> str | None:
        cleaned = self._clean_value(value)
        return cleaned or None

    def _to_iso_date(self, value: str) -> str:
        day, month, year = value.split("/")
        return f"{year}-{month}-{day}"

    def _to_iso_datetime(self, value: str) -> str:
        date_part, time_part = value.split()
        day, month, year = date_part.split("/")
        return f"{year}-{month}-{day} {time_part}"
