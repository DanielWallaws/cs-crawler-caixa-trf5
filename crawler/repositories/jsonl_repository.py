import json
from pathlib import Path


class JsonlRepository:
    """Persist processes in a JSONL file."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_all(self, processes):
        """Save processes to JSONL, replacing duplicated process numbers."""

        existing = self._load_index()

        for process in processes:
            process_number = str(process["numero_processo"])
            existing[process_number] = process

        with self.path.open("w", encoding="utf-8") as handler:
            for process in existing.values():
                handler.write(json.dumps(process, ensure_ascii=False) + "\n")

    def _load_index(self):
        if not self.path.exists():
            return {}

        indexed = {}
        with self.path.open(encoding="utf-8") as handler:
            for line in handler:
                line = line.strip()
                if not line:
                    continue
                process = json.loads(line)
                indexed[str(process["numero_processo"])] = process
        return indexed
