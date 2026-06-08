import re

from bs4 import BeautifulSoup, Tag

NOT_FOUND_MESSAGE = "O processo é inexistente ou tramita em segredo de justiça."
DATE_PATTERN = re.compile(r"\d{2}/\d{2}/\d{4}")
PROCESS_LINK_PREFIX = "/processo/"


class ProcessParser:
    """Extract process data from TRF5 HTML pages."""

    def parse_process(self, html) -> dict:
        """Parse a process detail page into the JSONL record format."""

        soup = BeautifulSoup(html, "html.parser")
        if self.is_not_found(soup):
            raise ValueError("Processo inexistente ou em segredo de justiça.")

        heading = self._find_process_heading(soup)
        numero_processo, numero_legado = self._extract_process_numbers(
            heading
        )
        data_autuacao = self._extract_autuacao(soup)
        relator, envolvidos = self._extract_participants(soup)
        movimentacoes = self._extract_movements(soup)

        numero_processo = numero_processo or numero_legado
        if not numero_processo:
            raise ValueError(
                "Nao foi possivel identificar o numero do processo."
            )

        return {
            "numero_processo": numero_processo,
            "numero_legado": numero_legado or "",
            "data_autuacao": data_autuacao or "",
            "relator": relator or "",
            "envolvidos": envolvidos,
            "movimentacoes": movimentacoes,
        }

    def parse_search_results(self, html, name_filter=None) -> tuple:
        """Parse a search page and return total, numbers and page size."""

        soup = BeautifulSoup(html, "html.parser")
        if self.is_not_found(soup):
            return 0, [], 0

        if self.is_process_detail(soup):
            process = self.parse_process(html)
            return 1, [str(process["numero_processo"])], 1

        result_table = soup.find("table", class_="consulta_resultados")
        if result_table is None:
            raise ValueError("Tabela de resultados nao encontrada.")

        process_numbers, page_size = self._extract_result_links(
            result_table,
            name_filter,
        )
        return self._extract_total(soup), process_numbers, page_size

    def is_process_detail(self, soup) -> bool:
        """Check whether the parsed HTML is a process detail page."""

        return bool(self._find_process_heading(soup))

    def is_not_found(self, soup) -> bool:
        """Check whether the parsed HTML reports a missing process."""

        page_text = self._normalized_text(soup)
        return NOT_FOUND_MESSAGE in page_text

    def _find_process_heading(self, soup) -> str:
        for paragraph in soup.find_all("p"):
            text = self._normalized_text(paragraph)
            if text.startswith("PROCESSO"):
                return text
        return ""

    def _extract_process_numbers(self, heading) -> tuple:
        if not heading:
            return None, None

        content = heading
        for marker in ("Nº", "N°", "No", "N"):
            if marker in content:
                content = content.split(marker, 1)[1]
                break

        content = self._clean_value(content)
        if not content:
            return None, None

        if "(" not in content or ")" not in content:
            return content, None

        process_number, legacy = content.split("(", 1)
        legacy = legacy.split(")", 1)[0]
        process_number = self._clean_optional_text(process_number)
        legacy = self._clean_optional_text(legacy)
        return process_number, legacy

    def _extract_autuacao(self, soup) -> str:
        for table in soup.find_all("table"):
            for cell in table.find_all("td"):
                text = self._normalized_text(cell)
                if not text.startswith("AUTUADO EM"):
                    continue

                match = DATE_PATTERN.search(text)
                if match:
                    return self._to_iso_date(match.group(0))
        return ""

    def _extract_participants(self, soup) -> tuple:
        participant_table = self._find_participant_table(soup)
        if participant_table is None:
            return None, []

        relator = None
        envolvidos = []

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

    def _extract_movements(self, soup) -> list:
        movements = []

        for anchor in soup.find_all("a", attrs={"name": True}):
            if not anchor["name"].startswith("mov_"):
                continue

            table = anchor.find_parent("table")
            movement_date = self._extract_movement_date(anchor)
            movement_text = self._extract_movement_text(table)
            if movement_date and movement_text:
                movements.append(
                    {"data": movement_date, "texto": movement_text}
                )

        return movements

    def _extract_result_links(self, result_table, name_filter=None) -> tuple:
        process_numbers = []
        page_size = 0
        name_index = self._find_column_index(result_table, "Nome")

        for row in self._result_rows(result_table):
            anchor = self._find_process_anchor(row)
            if anchor is None:
                continue

            page_size += 1
            if name_filter and not self._row_matches_name(
                row,
                name_index,
                name_filter,
            ):
                continue

            process_number = self._normalized_text(anchor)
            if process_number and process_number not in process_numbers:
                process_numbers.append(process_number)

        return process_numbers, page_size

    def _extract_total(self, soup) -> int:
        for table in soup.find_all("table", class_="consulta_paginas"):
            total = self._extract_total_from_text(self._normalized_text(table))
            if total is not None:
                return total

        result_table = soup.find("table", class_="consulta_resultados")
        if result_table is None:
            return 0
        _, page_size = self._extract_result_links(result_table)
        return page_size

    def _extract_total_from_text(self, text) -> int | None:
        marker = "Total:"
        if marker not in text:
            return None

        value = text.split(marker, 1)[1].strip().split(" ", 1)[0]
        return int(value) if value.isdigit() else None

    def _find_column_index(self, table, column_name) -> int | None:
        headers = [
            self._normalized_text(header)
            for header in table.find_all("th")
        ]

        for index, header in enumerate(headers):
            if header == column_name:
                return index
        return None

    def _result_rows(self, table) -> list:
        body = table.find("tbody")
        if body is None:
            return table.find_all("tr")
        return body.find_all("tr", recursive=False)

    def _find_process_anchor(self, row) -> Tag | None:
        for anchor in row.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href.startswith(PROCESS_LINK_PREFIX):
                continue
            if href.startswith("/processo/rss/"):
                continue
            return anchor
        return None

    def _row_matches_name(self, row, name_index, name_filter) -> bool:
        if name_index is None:
            return True

        cells = row.find_all("td", recursive=False)
        if name_index >= len(cells):
            return False

        name = self._normalized_text(cells[name_index]).upper()
        return name_filter.upper() in name

    def _find_participant_table(self, soup) -> Tag | None:
        for table in soup.find_all("table"):
            labels = [
                self._clean_label(cell.get_text(" ", strip=True)).upper()
                for cell in table.find_all("td")
            ]
            if "RELATOR" in labels:
                return table
        return None

    def _extract_movement_date(self, anchor) -> str:
        text = self._normalized_text(anchor)
        if not text.startswith("Em "):
            return ""

        value = text.removeprefix("Em ").strip()
        return self._to_iso_datetime(value)

    def _extract_movement_text(self, table) -> str:
        if table is None:
            return ""

        descriptions = []
        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if not cells:
                continue
            text = self._clean_value(cells[-1].get_text(" ", strip=True))
            if text:
                descriptions.append(text)

        return self._clean_value(" ".join(descriptions))

    def _normalized_text(self, node) -> str:
        parts = [
            " ".join(chunk.split())
            for chunk in node.get_text("\n").splitlines()
        ]
        return " ".join(part for part in parts if part).strip()

    def _clean_label(self, value) -> str:
        if value is None:
            return ""
        return value.strip().rstrip(":").strip()

    def _clean_value(self, value) -> str:
        if value is None:
            return ""

        cleaned = " ".join(value.split()).strip()
        if cleaned.startswith(":"):
            cleaned = cleaned[1:].strip()
        return cleaned

    def _clean_optional_text(self, value) -> str | None:
        cleaned = self._clean_value(value)
        return cleaned or None

    def _to_iso_date(self, value) -> str:
        day, month, year = value.split("/")
        return f"{year}-{month}-{day}"

    def _to_iso_datetime(self, value) -> str:
        date_part, time_part = value.split()
        day, month, year = date_part.split("/")
        return f"{year}-{month}-{day} {time_part}"
