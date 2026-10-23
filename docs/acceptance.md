# Aceite e rastreabilidade

Em 22/10/2026 Franklin informou “tudo esta funcionando” após executar a interface
0.0.5 no notebook Linux. Registrado como aceite funcional geral da interface, sem
inferir que todos os ensaios específicos abaixo foram realizados manualmente.

| Requisito | Evidência automatizada | Situação |
|---|---|---|
| RF01 arquivo local regular/limites | test_files, test_loading, test_window | Passou no Linux |
| RF02 formato/manual/ambiguidade | test_files, test_window | Passou no Linux |
| RF03 JSON restritivo | test_parsers | Passou |
| RF04 YAML restritivo | test_parsers | Passou |
| RF05 .env literal | test_parsers | Passou |
| RF06 categorias estruturais | test_comparison, test_comparing | Passou |
| RF07 ocultação inicial | test_window, smoke do pacote | Passou |
| RF08 uma célula/ocultação/timer | test_window | Passou; timer acelerado no teste de expiração, configuração padrão 15000 ms verificada |
| RF09 filtros/busca/contadores | test_comparison, test_window | Passou |
| RF10 relatório/visão/proteção de origens | test_reports, test_exporting, test_comparing, test_window | Passou |
| RF11 preferências mínimas/corrupção | test_preferences, test_window | Passou |
| RF12 cancelamento/limpar/fechar/timeout | test_loading, test_comparing, test_window, test_interrupt | Passou no Linux |
| RF13 teclado/acessibilidade | test_window, smoke 200% | Atalhos/foco/rolagem testados; leitor de tela e ensaio visual detalhado pendentes |

Testes estão em tests/unit, tests/integration e tests/gui. Somente fixtures sintéticas.
A captura em docs/images/interface.png mostra o resultado com valores ocultos.

Em seguida, Franklin validou o pacote RC1 copiado e extraído em
/home/franklin/Documentos/ConfigDiff/, executando-o pelo Konsole com sucesso.
Os 419 hashes dessa cópia foram conferidos sem alterar arquivos. Detalhes da
continuidade, MIT e fontes em [release-followup.md](release-followup.md).

## Roteiro manual complementar

- Abrir os três pares example/example-b: JSON, YAML e env.txt (formato env explícito).
- Encontrar chave ausente, alteração de tipo (JSON/YAML) e diferença de DB_PASSWORD.
- Revelar uma célula, esperar 15 s reais, repetir e trocar foco; confirmar ocultação.
- Filtrar PASSWORD, exportar para arquivo novo e confirmar ausência dos valores.
- Repetir somente por teclado; conferir escalas 125%/200% e leitor de tela disponível.
- Testar pacote extraído no desktop, sem .venv; verificar hashes antes de executar.

O teste de contêiner offline sem Python cobre inicialização e fluxo automático do
pacote; não substitui o roteiro no desktop. O aceite Windows posterior está registrado abaixo; Ubuntu continua sem aceite desktop manual.


Em 22/10/2026 Franklin também aceitou o RC2 extraído em
dist/teste/ConfigDiff. A cópia teve seus 668 hashes conferidos somente para leitura.
A auditoria complementar de pacotes/fontes está em provenance-audit.md.


## Aceite manual — Windows 11 Enterprise em VM

Em 22/10/2026 Franklin informou que instalou uma VM com ISO do Windows 11
Enterprise, copiou o ZIP, extraiu e executou o aplicativo com sucesso. O ambiente
mostrado é QEMU/KVM. Registro do usuário: “a aplicação esta funcionando”.

A [captura fornecida](images/windows-11-enterprise.png) mostra a interface no Windows,
os exemplos JSON A/B carregados, cinco diferenças (duas de valor, uma de tipo e
uma ausência de cada lado), tema escuro e uma célula de APP_ENV revelada. Os demais
valores permanecem ocultos, incluindo DB_PASSWORD. O caminho visível identifica
`configdiff-0.1.0rc2-windows-AMD64`; o hash do ZIP usado não foi informado.

Registrado como aceite funcional geral do pacote portátil na VM Windows 11
Enterprise. Não implica execução manual de todos os itens do roteiro: exportação,
tempo real de ocultação, troca de foco, escalas e leitor de tela não foram confirmados
individualmente. A edição/build exata do Windows e teste em hardware físico não
foram informados. Evidências automatizadas complementares em [github-actions.md](github-actions.md).
