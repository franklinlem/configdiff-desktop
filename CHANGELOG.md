# Changelog

## 0.0.5 — 2026-10-22

- Interface real: seleção de arquivos/formatos, comparação, busca, filtros e contadores.
- Tabela Qt com valores ocultos e revelação individual temporária, sem cópia de valores.
- Exportação da visão atual, temas, atalhos, rolagem e preferências mínimas.
- Smoke gráfico com comparação/exportação/cancelamento, inclusive no pacote Linux.
- Corrida de SIGINT no bootstrap do filho corrigida no transporte POSIX.

## 0.0.4 — 2026-10-22

- Comparador estrutural com cinco categorias, caminhos tipados e contagem coerente.
- Busca por caminho, filtros combináveis e projeção de relatório sem valores.
- Exportação Markdown literal, somente para arquivo novo, com proteção das origens.
- ComparisonJob isolado; transporte compartilhado com LoadJob.
- CLI configdiff-compare, pares sintéticos e benchmark de dois arquivos de 1 MiB.
- 206 testes; interface gráfica de uso real ainda pendente.

## 0.0.3 — 2026-10-22

- Leitura limitada e somente leitura de arquivos regulares, com verificação de metadados.
- Parsers JSON, YAML por eventos e .env literal, com regras e limites documentados.
- LoadJob em processo spawn com timeout/cancelamento e recepção IPC em thread.
- CLI configdiff-inspect com metadados, fixtures sintéticas e benchmark reproduzível.
- 155 testes; comparação e GUI de uso real ainda pendentes.

## 0.0.2 — 2026-10-22

- Ctrl+C encerra a GUI e o processo filho sem traceback; regressão POSIX real.
- Contratos canônicos imutáveis, caminhos tipados, erros seguros e limites definidos.
- Tipos de resultados e DTO de relatório sem valores; testes do domínio.
- Lock Linux com hashes SHA-256 e tipagem estrita do domínio.
- Continuidade local Linux autorizada; Windows permanece pendente.

## 0.0.1 — 2026-10-22

- Prova Qt Widgets, processo spawn cancelável, timeout e encerramento.
- Experimento restritivo de YAML e testes de regras/limites.
- Bootstrap Python, versões fixadas, build PyInstaller e CI proposto Linux/Windows.
- MVP ainda não implementado; validação Windows e aceite visual pendentes.
