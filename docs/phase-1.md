# Fase 1 — fundação do núcleo

Registro histórico; a fase 2 está documentada em [phase-2.md](phase-2.md).

Incremento 0.0.2, em 22/10/2026. A continuidade local Linux foi autorizada por
Franklin após o protótipo da fase 0. Windows, teste em máquina limpa e aceite visual
continuam pendentes para distribuição; não impedem os incrementos locais.

## Entregue

- Árvore canônica imutável, tipos escalares explícitos e conversão sem coerções.
- Caminhos por segmentos Key/Index, apresentação sem colisão e controles escapados.
- Limites compartilhados: 5 MiB, profundidade 64, 50 mil nós, 200 mil tokens e 10 s.
  A raiz conta um nó e tem profundidade zero; cada entrada de mapa/elemento de lista
  adiciona um nó; chaves não contam separadamente. Parsers aplicarão esses limites.
- Códigos de erro públicos sem conteúdo, com lado e linha/coluna opcionais.
- Contratos de diferenças/resultados e DTO sanitizado sem referências a valores.
- Lock Linux com versões exatas e hashes SHA-256; backend de build fixado.
- Testes de domínio em tests/unit, regressão de processo real em tests/integration
  e tipagem estrita dos módulos de domínio. Testes anteriores do protótipo mantidos.

## Correção do Ctrl+C

A saída enviada por Franklin era KeyboardInterrupt decorrente da interrupção no
terminal. O handler padrão podia lançar a exceção enquanto Qt executava um slot.
Agora SIGINT marca a intenção de saída, e o loop Qt fecha a janela, cancela o filho
e retorna código 130. Fechar normalmente continua retornando código 0.

A regressão executa um aplicativo real em subprocesso, envia SIGINT com a janela
ociosa e ao grupo de processos com trabalho ativo, e verifica código 130, ausência
de traceback e remoção do processo de trabalho. O cleanup também roda em aboutToQuit
para cobrir saídas iniciadas por QApplication.quit.

## Evidências executadas no Debian 13

| Verificação | Resultado |
|---|---|
| Ruff lint e formatação | Passaram |
| mypy, incluindo domínio estrito | Passou em 12 arquivos de src |
| pytest headless | 52 testes passaram em 8,47 s |
| pip --dry-run --ignore-installed --require-hashes | Resolveu o lock sem erro; hashes dos artefatos verificados |
| Smoke da fonte em Wayland | Código 0 |
| Build PyInstaller limpo | Concluído |
| Smoke do pacote em Wayland | Código 0 |
| SIGINT com worker no pacote Linux | Código 130, sem traceback e sem subprocessos remanescentes |

O lock foi validado para Linux/Python 3.13.5. O ensaio de hashes usa dry-run com
ignore-installed; não representa reinstalação em máquina limpa. Dependências
Windows continuam no arquivo de versões diretas, sem lock transitivo validado.

Artefatos locais: dist/ConfigDiff/ConfigDiff e arquivo compactado da fase 1 com
checksum. Builds e ambiente virtual ficam fora do Git. Não houve publicação remota.

## Limites e próximo incremento

A interface permanece demonstrativa. Não há leitura, comparação de configurações,
revelação de valores ou exportação. Os contratos de resultado não são um comparador
pronto. Sanitização de Markdown e execução dos parsers isolados virão nas fases 2/3.

Próximo incremento: leitura limitada de arquivos regulares e parsers JSON, YAML e
.env, com erros seguros, fixtures sintéticas e rejeição de entradas hostis.
