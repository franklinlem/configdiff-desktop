# Fase 0 — evidências em 22/10/2026

Atualização após autorização de continuidade: desenvolvimento local Linux prossegue
na fase 1; Windows e aceite visual continuam pendentes para distribuição. Detalhes
em [phase-1.md](phase-1.md). O restante registra a evidência histórica da fase 0.

Status histórico: provas locais Linux executadas; marco M0 ainda pendente de Windows e aceite
visual. Conforme seção 12 do planejamento, a fase 1 depende desse marco. Não foi
implementada comparação de configurações nem declarada a versão MVP pronta.

## Ambiente observado

- Debian GNU/Linux 13.7, x86_64, sessão Wayland.
- Python 3.13.5; Qt/PySide Essentials 6.12.0; PyYAML 6.0.3;
  PyInstaller 6.22.3. Git 2.47.3.
- venv local, sem instalação global de dependências ou alteração de servidores.
- Nenhum repositório remoto criado; Git local inicializado no branch main.

## Verificações executadas

| Comando / experimento | Resultado |
|---|---|
| `ruff check .` e `ruff format --check .` | Passaram |
| `mypy` | Passou, 6 arquivos de src; protótipo YAML fora dessa checagem |
| `python -m pip check` | Dependências consistentes |
| `QT_QPA_PLATFORM=offscreen pytest -q` | 19 testes passaram em 5,35 s |
| `QT_QPA_PLATFORM=wayland python -m configdiff.app --smoke-test` | Código 0 |
| PyInstaller onedir | Build Linux concluído |
| Pacote `--smoke-test`, Wayland e offscreen | Ambos código 0; plugin offscreen emite aviso de size hints |

Os testes cobrem retorno do filho, cancelamento, timeout, falha abrupta, ausência
de filho vivo após encerramento, fechamento da janela e heartbeat Qt durante o
trabalho. YAML: semântica explícita, recursos proibidos, erro sem conteúdo e limites
de tamanho, nós e profundidade. A prova valida viabilidade, não todos os RNFs do MVP.

Os testes GUI automáticos não equivalem à avaliação visual/acessível por Franklin.
O pacote iniciou na máquina de desenvolvimento; falta máquina limpa sem Python,
ensaio offline isolado e medição de memória. Não foi executado teste Windows.

## Artefatos

- `dist/ConfigDiff/ConfigDiff`: executável Linux local.
- `dist/configdiff-phase0-linux-x86_64.tar.gz` e `dist/SHA256SUMS`.
- `requirements-linux.lock`: snapshot completo das dependências Python instaladas.
- `.github/workflows/phase0.yml`: matriz preparada, ainda sem execução remota.

Builds e venv ficam fora do Git. O pacote é experimental e não foi publicado.
As regras de distribuição e licenças ainda precisam ser concluídas antes de release.

## Próximos incrementos e critérios

1. Concluir M0: executar CI/build/smoke Windows nativos, obter lock Windows e realizar
   aceite visual do protótipo (iniciar/cancelar/timeout/fechar).
2. Fase 1: contratos canônicos e caminhos tipados, tipos de erro e limites definitivos,
   estrutura de testes por camada e lock reproduzível por plataforma.
3. Fase 2: leitura limitada e parsers completos no processo isolado; fixtures de
   fronteira e entradas hostis. A prova YAML não será adotada como parser sem essa etapa.
4. Fases 3–5: comparação, projeção sanitizada, interface de uso real e distribuição.

O plano original foi preservado; o status histórico no cabeçalho descreve o momento
do planejamento. Este arquivo e CHANGELOG registram o andamento da implementação.
