# CS-CROWLER-CAIXA-TRF5

Crawler em Python 3 para a consulta pública do TRF5, usando `requests`,
`BeautifulSoup4` e persistência em JSONL.

## Arquitetura

O projeto mantém uma arquitetura simples, separando apenas responsabilidades
necessárias para o crawler:

- `crawler/main.py`: entrada da aplicação e comandos de CLI.
- `crawler/settings.py`: configurações e dados conhecidos do crawler.
- `crawler/client/trf5_client.py`: requisições HTTP ao TRF5.
- `crawler/parsers/process_parser.py`: extração de dados do HTML.
- `crawler/repositories/jsonl_repository.py`: persistência em JSONL.

Não há banco de dados, fila, scheduler ou monitoramento contínuo. A aplicação
consulta, consolida, persiste e encerra.

## Modelagem

A pasta `docs/` contém dois diagramas de apoio:

- `docs/Modelagem_Arquitetural.png`: visão dos componentes do crawler e suas
  dependências.
- `docs/Modelagem_ Solucao.png`: visão sequencial do fluxo de execução.

## Instalação

Execute os comandos a partir da pasta raiz do projeto:

```bash
cd cs-crowler-caixa-trf5
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configuração opcional via `.env`:

```env
TRF5_BASE_URL=https://cp.trf5.jus.br
TRF5_REQUEST_TIMEOUT=30
TRF5_SAVE_BATCH_SIZE=25
TRF5_OUTPUT_PATH=data/processes.jsonl
TRF5_USER_AGENT=cs-crowler-caixa-trf5/1.0
```

## Execução

O crawler possui uma única forma de execução:

```bash
cd cs-crowler-caixa-trf5
source .venv/bin/activate
python3 -m crawler.main
```

Essa execução roda o fluxo completo configurado:

1. Consulta os processos conhecidos em `settings.py`.
2. Busca processos pelos CNPJs configurados.
3. Busca processos pelos nomes de parte configurados.
4. Consolida os números de processo encontrados.
5. Remove duplicidades em memória.
6. Consulta os detalhes de cada processo consolidado.
7. Persiste os detalhes em JSONL por lotes.
8. Encerra a execução.

O crawler não aceita argumentos de linha de comando. Para alterar o destino do
JSONL, configure `TRF5_OUTPUT_PATH` no `.env`.

Durante a execução, o progresso é escrito no terminal. O arquivo JSONL é criado
após o primeiro lote de detalhes consultados, não durante a etapa inicial de
busca paginada.

Na busca por nome, o termo configurado é amplo (`CAIXA SEGURADORA`). O parser
usa a coluna `Nome` da tabela de resultados para manter somente linhas que
tenham `S/A`, evitando depender da busca direta por `CAIXA SEGURADORA S/A`.

Essa estratégia foi adotada porque a consulta direta pelo nome completo não
retorna todos os registros esperados. Ao pesquisar `CAIXA SEGURADORA SA`, sem
barra, a base retorna poucos resultados. Ao pesquisar `CAIXA SEGURADORA S/A`,
com barra, a consulta também não é confiável por causa do uso da barra na URL.
Por isso, o crawler primeiro busca por `CAIXA SEGURADORA` e depois confirma,
pela coluna `Nome` da própria tabela, se o registro pertence à seguradora
`S/A`.

## JSONL e deduplicação

JSONL foi escolhido porque é simples, legível e suficiente para o volume do
fluxo atual. Cada linha contém um processo em JSON, o que facilita inspeção,
versionamento simples e processamento posterior por scripts.

A deduplicação acontece em duas etapas:

- No fluxo automático, os números de processo são consolidados em memória antes
  da consulta detalhada.
- Ao salvar cada lote, o repositório carrega o JSONL existente, indexa por
  `numero_processo` e reescreve o arquivo com a versão mais recente de cada
  processo.

Essa abordagem é intencionalmente simples. A limitação é que o arquivo inteiro
é carregado e regravado a cada persistência. Para o volume atual isso é
adequado; para volumes muito maiores, outra estratégia de persistência poderia
ser avaliada futuramente.

## Possíveis melhorias futuras

- Testes automatizados com fixtures HTML reais e anonimizadas.
- Configuração externa para listas maiores de CNPJs, partes e processos.
- Persistência otimizada caso o volume cresça muito.
- Retentativas controladas para falhas temporárias de rede.

Essas melhorias não fazem parte do escopo atual para manter o crawler simples e
aderente ao escopo atual.
