# ConfigDiff Desktop

Comparação local de configurações JSON, YAML e .env, sem backend.
**0.0.5 — fase 4: interface gráfica funcional e ferramentas de terminal.**

## Executar no Debian 13

Python de referência: 3.13.5. Dependências isoladas no projeto:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-linux.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/configdiff
```

Selecione os arquivos A e B e clique Comparar. Para experimentar, use
`tests/fixtures/example.json` e `tests/fixtures/example-b.json`. Os valores ficam
ocultos; selecione uma célula Valor A/B e use Revelar célula para uma prévia de até
15 segundos. Busca e filtros consideram caminhos/categorias. Exportação Markdown
omite todos os valores e exige um arquivo novo. Limpar descarta os dados da sessão.

Ctrl+C no terminal encerra a aplicação e o trabalho ativo, com código de saída 130.
[Guia da interface, atalhos e privacidade](docs/phase-4.md).

## Validar arquivos no terminal

```sh
.venv/bin/configdiff-inspect tests/fixtures/example.json
.venv/bin/configdiff-inspect tests/fixtures/example.yaml
.venv/bin/configdiff-inspect tests/fixtures/example.env.txt --format env
```

Executa leitura e parsing em processo isolado; mostra somente formato, tipo da raiz,
número de nós e tamanho. Não imprime chaves/valores. Regras em [formats.md](docs/formats.md).

## Comparar e exportar

```sh
.venv/bin/configdiff-compare tests/fixtures/example.json tests/fixtures/example-b.json
.venv/bin/configdiff-compare tests/fixtures/example.json tests/fixtures/example-b.json --query PASSWORD --category value_changed --output relatorio-password.md
```

Sem --output, mostra Markdown sanitizado no terminal. Relatórios contêm caminhos de
chaves, categorias e tipos; valores são sempre omitidos. --query busca só caminhos;
--category pode ser repetido. Destinos existentes são recusados: escolha um nome novo.
[Detalhes e evidências da fase 3](docs/phase-3.md). A GUI usa o mesmo núcleo de comparação.

## Verificar

```sh
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
QT_QPA_PLATFORM=wayland .venv/bin/python -m configdiff.app --smoke-test
```

O último comando testa a janela na sessão gráfica com dados sintéticos. O modo smoke
verifica comparação, mascaramento, exportação e cancelamento; retorna erro se falhar.

## Empacotar

```sh
.venv/bin/python -m PyInstaller --noconfirm --clean --onedir --name ConfigDiff --paths src packaging/entrypoint.py
./dist/ConfigDiff/ConfigDiff --smoke-test
```

O pacote inclui Python; ainda depende de bibliotecas do sistema Linux e do servidor
gráfico. Em Windows, usar Python nativo, `requirements-windows.txt` e o mesmo comando
de build; executar `dist/ConfigDiff/ConfigDiff.exe --smoke-test`.

Consulte [evidências da fase 0](docs/phase-0.md), [fase 1](docs/phase-1.md), [fase 2](docs/phase-2.md), [fase 3](docs/phase-3.md), [fase 4](docs/phase-4.md),
[arquitetura](docs/architecture.md), [formatos suportados](docs/formats.md)
e [distribuição](docs/releasing.md). O planejamento original permanece preservado.
O repositório Git é local; publicação no GitHub não foi feita.
