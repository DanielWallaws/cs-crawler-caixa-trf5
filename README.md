# CS-CROWLER-CAIXA-TRF5

Crawler em Python 3 para a consulta pública do TRF5, usando `requests`, `BeautifulSoup4` e saída em JSONL.

## Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure o `.env`:

```env
TRF5_BASE_URL=https://www5.trf5.jus.br
TRF5_REQUEST_TIMEOUT=30
TRF5_OUTPUT_PATH=data/processes.jsonl
TRF5_USER_AGENT=cs-crowler-caixa-trf5/1.0 (requests; +https://www5.trf5.jus.br/cp/)
```

Busca por número de processo:

```bash
python3 -m crawler.main --json process 0000881-39.2016.4.05.0000
```

Busca por CNPJ:

```bash
python3 -m crawler.main cnpj 34.020.354/0001-10 --limit 10
```

Busca por nome da parte:

```bash
python3 -m crawler.main party "CAIXA SEGURADORA S/A" --limit 10
```

Por padrão os dados são salvos em `data/processes.jsonl`. Para mudar o arquivo:

```bash
python3 -m crawler.main --output data/caixa.jsonl cnpj 34.020.354/0001-10
```

Para consultar sem salvar:

```bash
python3 -m crawler.main --skip-save --json process 0000881-39.2016.4.05.0000
```

## Estrutura

- `crawler/main.py`: CLI
- `crawler/client/trf5_client.py`: cliente HTTP
- `crawler/parsers/process_parser.py`: parser HTML
- `crawler/repositories/jsonl_repository.py`: persistência JSONL
