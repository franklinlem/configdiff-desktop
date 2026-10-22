# Fase 2 — leitura e parsers

Incremento 0.0.3, em 22/10/2026, validado localmente no Debian 13/Python 3.13.5.

## Entregue

- Captura somente leitura de arquivos regulares, tamanho limitado e verificação de
  metadados do objeto aberto; symlinks regulares aceitos.
- Parsers JSON, YAML e .env com contratos canônicos e regras documentadas em formats.md.
- Rejeição de duplicatas, UTF-8 inválido, recursos YAML proibidos e .env ambíguo.
- LoadJob isolado com cancelamento, timeout e canal de erros sem conteúdo bruto.
- Recebimento do IPC em thread, evitando bloquear a GUI com mensagens grandes.
- `configdiff-inspect`: ferramenta de terminal com saída somente de metadados.
- Fixtures sintéticas e benchmark reproduzível. Nenhuma dependência nova de runtime.

## Evidências executadas

| Verificação | Resultado |
|---|---|
| Ruff lint/formatação | Passaram |
| mypy | Passou em 20 arquivos de src; domínio estrito |
| pytest headless completo | 155 testes passaram em 15,04 s |
| CLI com fixtures JSON/YAML/.env | Três códigos 0; 5 nós cada; sem chaves/valores na saída |
| JSON de 1 MiB/10 mil nós em LoadJob | 0,646 s incluindo spawn/leitura/parsing/IPC/cleanup |
| Pico RSS de filho no benchmark Linux | 31372 KiB (~30,6 MiB) |

A suíte cobre fronteiras de tamanho/nós/profundidade/tokens, YAML profundo (2 mil
níveis, rejeitado), preservação do hash das origens, crescimento durante leitura,
FIFO/dispositivo, erro de permissão simulado, symlink, processo morto, cancelamento,
timeout, mensagem IPC superior ao buffer e saída CLI sem sentinelas. Os testes GUI
e SIGINT anteriores continuam passando. Windows ainda não foi executado.

Reproduzir a medição: `.venv/bin/python scripts/benchmark_loading.py`. A fixture é
gerada com dados sintéticos em diretório temporário removido ao final. Medição única
nesta máquina; não é benchmark de comparação, garantia de desempenho nem teto de
memória para todas as entradas. O processo não impõe limite de RAM do sistema.

## Executar

```sh
.venv/bin/configdiff-inspect tests/fixtures/example.json
.venv/bin/configdiff-inspect tests/fixtures/example.yaml
.venv/bin/configdiff-inspect tests/fixtures/example.env.txt --format env
```

Retornos: 0 válido; 1 arquivo/parsing/trabalho falhou; 2 formato não identificado ou
uso inválido; 130 interrupção pelo terminal. Não imprime chaves, valores ou caminho
nas mensagens de validação. Use --format para nomes sem extensão reconhecida.

## Próximo incremento

Fase 3: comparador estrutural, categorias de diferenças, filtros e projeção para
relatório Markdown sanitizado, com testes de simetria/privacidade/integridade.
A GUI ainda é demonstrativa e não abre arquivos. Esta etapa não implementa comparação,
revelação ou exportação. Pacotes GUI existentes em dist continuam sendo da fase 1;
a CLI desta fase está instalada na .venv. Distribuição final e Windows permanecem pendentes.
