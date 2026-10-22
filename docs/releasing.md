# Build e distribuição — 0.1.0rc1 local

O candidato está preparado para avaliação local. Publicação final depende das
pendências de phase-5.md e THIRD_PARTY_NOTICES.md. Windows/Ubuntu não são anunciados
como validados. Referência de build: Debian 13 x86_64, Python 3.13.5.

## Construir

```sh
.venv/bin/python -m pip install --require-hashes -r requirements-linux.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/ruff check .
.venv/bin/mypy
QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
.venv/bin/python scripts/build_candidate.py
```

Arquivos novos necessários à distribuição devem estar no índice Git antes do build:
fontes, documentação e exemplos são limitados à lista de arquivos versionados. O
script não inclui relatórios locais não versionados e não publica nada. O bundle em
dist/ConfigDiff é reconstruído pelo PyInstaller; preserve arquivos próprios fora dele.

Gerados: dist/ConfigDiff, dist/configdiff-VERSAO-linux-x86_64.tar.gz e arquivo .sha256.
O bundle inclui source/configdiff-source.tar.gz, build-info.json, bundle-inventory.json,
files.sha256, docs, examples e licenses. O inventário distingue provedores Debian quando
identificáveis e marca terceiros Qt incorporados ainda sem atribuição completa.

O código-fonte empacotado é o estado de trabalho dos arquivos versionados; build-info
registra commit e se havia mudanças versionadas. O snapshot de fontes e hashes é a
evidência exata de entrada. O processo é repetível com versões fixadas, mas timestamps,
compilação nativa e bibliotecas de sistema impedem prometer binários idênticos byte a byte.

## Verificar e executar

A partir de dist, verifique o hash e extraia em uma pasta nova:

```sh
sha256sum -c configdiff-0.1.0rc1-linux-x86_64.tar.gz.sha256
tar -xzf configdiff-0.1.0rc1-linux-x86_64.tar.gz -C /caminho/para/pasta-nova
cd /caminho/para/pasta-nova/ConfigDiff
sha256sum -c files.sha256
./ConfigDiff
```

Preserve os symlinks e mantenha _internal junto do executável. Não instalar Python no
destino. No Debian 13, requer libgl1/libegl1 e fontes/configuração Fontconfig do sistema,
além de sessão gráfica para uso normal. Sem dependência de rede em tempo de execução.
Sem assinatura de binário ou atualizador automático. Para reverter, feche o programa e
use o diretório do candidato anterior; não há migração de dados de usuário.

## Smoke offline sem Python

```sh
docker build -f packaging/Dockerfile.smoke -t configdiff-smoke:debian13 .
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,mode=1777 --user 1000:1000 --mount type=bind,src="$PWD/dist/ConfigDiff",dst=/app,readonly configdiff-smoke:debian13
```

A construção da imagem usa rede para instalar somente bibliotecas gráficas/fontes;
o ensaio roda sem rede, verifica que python3 não existe e testa comparação, mascaramento,
exportação e cancelamento no executável congelado. Não equivale a teste manual de desktop.
A base é fixada por digest; versões apt ainda seguem o repositório Debian no momento do
build. Recriar a imagem pode atualizar esses pacotes; registrar sua ID nas evidências.

## Windows e CI

Workflow phase0.yml prepara qualidade e candidatos em runners nativos Linux/Windows.
Ainda não foi executado remotamente. Windows usa requirements-windows.txt, sem lock
transitivo validado, e gera ZIP. Build Linux não é cross-compilation para Windows.
Uma versão pública deve usar tag após checks e aceite; o workflow não publica releases.
