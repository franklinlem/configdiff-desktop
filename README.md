# ConfigDiff Desktop

Comparação local de configurações, planejada para JSON, YAML e .env, sem backend.
**0.0.1 — protótipo da fase 0; ainda não compara arquivos.**

## Executar no Debian 13

Python de referência: 3.13.5. Dependências isoladas no projeto:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-linux.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/configdiff
```

A janela inicia um trabalho sintético de 30 segundos. Cancele pelo botão ou feche
a janela; sem ação, o trabalho termina por timeout de 10 segundos. Não seleciona
nem lê configurações reais. Não há persistência ou acesso de rede no protótipo.

## Verificar

```sh
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
QT_QPA_PLATFORM=wayland .venv/bin/python -m configdiff.app --smoke-test
```

O último comando abre brevemente a janela na sessão gráfica. O modo smoke verifica
início e cancelamento, encerrando com código diferente de zero se o estado falhar.

## Empacotar

```sh
.venv/bin/python -m PyInstaller --noconfirm --clean --onedir --name ConfigDiff --paths src packaging/entrypoint.py
./dist/ConfigDiff/ConfigDiff --smoke-test
```

O pacote inclui Python; ainda depende de bibliotecas do sistema Linux e do servidor
gráfico. Em Windows, usar Python nativo, `requirements-windows.txt` e o mesmo comando
de build; executar `dist/ConfigDiff/ConfigDiff.exe --smoke-test`.

Consulte [evidências e próximos incrementos](docs/phase-0.md),
[arquitetura](docs/architecture.md), [política YAML experimental](docs/formats.md)
e [distribuição](docs/releasing.md). O planejamento original permanece preservado.
O repositório Git é local; publicação no GitHub não foi feita.
