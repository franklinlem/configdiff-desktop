# Fase 3 — comparação e privacidade

Incremento 0.0.4, em 22/10/2026, validado localmente no Debian 13/Python 3.13.5.

## Entregue

- Comparador estrutural com ausente em A/B, tipo alterado, valor alterado e igual.
- Tipos escalares distintos, igualdade exata de floats finitos, strings sem normalização,
  mapas sem ordem e listas por posição. Ausência difere de null e string vazia.
- Um ramo ausente ou com tipo alterado gera somente a entrada na raiz desse ramo.
  Ramos compartilhados não vazios são percorridos; folhas e contêineres vazios iguais
  geram entradas Igual. Contadores usam exatamente essas unidades.
- Busca textual no caminho exibido e filtro combinável de categorias, sem buscar valores.
- Projeção de uma visão filtrada em DTO sem valores e exportador Markdown separado.
- Indicador auxiliar de nomes potencialmente sensíveis; mascaramento independe dele.
- ComparisonJob: duas leituras, parsing e comparação no mesmo processo, com orçamento
  total de 10 s incluindo startup/IPC; nenhum resultado parcial se A ou B falhar.
- Exportação exclusiva para arquivo novo, recusando equivalência com entradas e qualquer
  destino existente. Não há sobrescrita, nem mesmo de relatório anterior.
- CLI configdiff-compare; pares fictícios nos três formatos e benchmark reproduzível.

## Evidências executadas

| Verificação | Resultado |
|---|---|
| Ruff lint e formatação | Passaram |
| mypy | Passou em 28 arquivos de src; domínio estrito |
| pytest headless completo | 206 testes passaram em 19,48 s |
| CLI instalada, par JSON fictício | 5 diferenças, sem valores na saída |
| Benchmark, dois JSON de 1 MiB/10 mil nós cada | 1,002 s incluindo spawn/leitura/parsing/comparação/IPC/cleanup |
| Pico RSS de filho no benchmark Linux | 51088 KiB (~49,9 MiB) |

Testes novos cobrem todas as categorias, parada por raiz de ramo, simetria A/B,
identidade em árvores sintéticas geradas com semente fixa, ordem de mapas, posição de
listas, caminhos ambíguos, tipos e igualdade sem tolerância, contagem e filtros.

Sentinelas em valores diferentes, iguais e em subárvores não aparecem nos relatórios.
Caminhos com links, HTML, imagens, pipes, backticks e controles permanecem em um único
code span literal; controles/bidi são escapados. Exportador rejeita resultado rico.

Testes reais de arquivos verificam hashes preservados, destinos existentes intactos,
origem por caminho, symlink e hard link, caminho da origem removida e uma corrida que
cria hard link antes do open exclusivo. CLI verifica exportação filtrada e erros sem
sentinelas. Timeout/cancelamento/falha de processo não retornam resultado parcial.

O benchmark é uma medição única nesta máquina, não garantia geral nem teto de RAM.
Reproduzir: `.venv/bin/python scripts/benchmark_comparison.py`. Usa apenas dados
sintéticos em diretório temporário removido ao final. Não mede GUI ou exportação.

## Usar

```sh
.venv/bin/configdiff-compare tests/fixtures/example.json tests/fixtures/example-b.json
.venv/bin/configdiff-compare tests/fixtures/example.yaml tests/fixtures/example-b.yaml --query FEATURE
.venv/bin/configdiff-compare tests/fixtures/example.env.txt tests/fixtures/example-b.env.txt --format env
```

Para exportar, escolha um nome que ainda não existe:

```sh
.venv/bin/configdiff-compare tests/fixtures/example.json tests/fixtures/example-b.json --query PASSWORD --category value_changed --output relatorio-password.md
```

Sem --output, imprime o Markdown sanitizado no terminal. Os nomes de chaves continuam
visíveis. --query pesquisa o caminho ASCII escapado exibido, sem distinguir caixa;
não pesquisa valores. --category pode ser repetido e substitui o padrão de somente
diferenças. Para incluir iguais, especifique as categorias desejadas explicitamente.
Contagem do relatório corresponde somente à visão exportada.

Retornos: 0 comparação/exportação concluída, mesmo havendo diferenças; 1 erro; 2 uso ou
formato não identificado; 130 interrupção. Sem --format, ambos os formatos precisam
ser reconhecidos e iguais. --format declara o formato dos dois arquivos.

## Limites e próximo incremento

GUI ainda demonstrativa; não há revelação visual, preferências ou fluxo gráfico de
comparação. Próximo incremento, fase 4: seletores, tabela Qt, filtros, contadores,
revelação temporária, atalhos e exportação da visão atual. Comparação Windows,
validação em máquina limpa e distribuição final continuam pendentes. Nenhum pacote
GUI novo foi gerado nesta etapa; artefatos anteriores em dist são históricos.

Arquivos criados no POSIX usam permissão máxima 0600. ACLs e políticas Windows dependem
do sistema. Uma falha durante a escrita pode deixar relatório parcial, ainda sem
valores. Não remover arquivos automaticamente após erro evita apagar um destino que
outro processo tenha substituído. Há proteção contra sobrescrita das origens, sem
promessa de segurança contra outro processo malicioso com as mesmas permissões.
