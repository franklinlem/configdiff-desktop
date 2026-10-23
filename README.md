# ConfigDiff Desktop

Comparação local de configurações JSON, YAML e .env, sem backend.
**0.1.0rc2 — candidatos Linux e Windows validados no CI; release final pendente.**

[Execução e pacotes no GitHub Actions](https://github.com/franklinlem/configdiff-desktop/actions/runs/39871502594)
(repositório privado). [Resultados e limites da validação](docs/github-actions.md).

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

## Pacote Linux sem Python

```sh
.venv/bin/python scripts/fetch_upstream_sources.py
.venv/bin/python scripts/build_candidate.py
./dist/ConfigDiff/ConfigDiff
```

O candidato inclui documentação, exemplos, código versionado, inventário, textos de
licença disponíveis e checksums. Validação offline em contêiner sem Python e detalhes
em [distribuição](docs/releasing.md) e [fase 5](docs/phase-5.md). O aceite funcional
Linux e Windows 11 Enterprise em VM estão em [acceptance.md](docs/acceptance.md).
A correspondência completa de fontes/atribuições Qt segue pendente antes da release final.

Consulte [evidências da fase 0](docs/phase-0.md), [fase 1](docs/phase-1.md), [fase 2](docs/phase-2.md), [fase 3](docs/phase-3.md), [fase 4](docs/phase-4.md), [fase 5](docs/phase-5.md),
[arquitetura](docs/architecture.md), [formatos suportados](docs/formats.md)
e [distribuição](docs/releasing.md). O planejamento original permanece preservado.
O [repositório GitHub](https://github.com/franklinlem/configdiff-desktop) é privado;
a matriz CI Linux/Windows passou. Não foi criada release pública.

Código próprio sob [MIT](LICENSE), confirmada por Franklin. O pacote RC1 extraído foi
aceito no desktop; o RC2 acrescenta fontes e atribuições. Veja [continuidade](docs/release-followup.md).

A proveniência do RC2 foi auditada sem alterar o aplicativo aceito: 179 arquivos de
dependências conferidos e fontes exatas de 57 pacotes Debian reunidas. Consulte
[auditoria e pacote auxiliar](docs/provenance-audit.md). O pacote Windows também foi aceito manualmente em VM Windows 11 Enterprise.
