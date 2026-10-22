# Arquitetura da prova

A janela Qt usa QTimer de 25 ms para consultar um processo multiprocessing com
contexto spawn explícito. O filho só aguarda e retorna um código fixo por Pipe.
Nenhuma thread Qt faz parsing. Cancelar/fechar termina e aguarda o filho, com
fallback kill e esperas de 0,5 segundo por etapa. O timeout usa relógio monotônico.
O processo não é sandbox de sistema operacional.

O entrypoint chama freeze_support antes de importar Qt, necessário também no
pacote congelado. A prova YAML está isolada em prototypes/ e não faz parte da GUI.
Não é o parser definitivo: a árvore intermediária ainda é criada antes de medir
profundidade/nós; a fase 2 deverá aplicar limites prévios de profundidade e tokens
no worker, além dos limites canônicos finais.

Decisão inicial (ADR 0001): manter Python 3.13.5 e PySide6 Essentials 6.12.0,
Qt Widgets, PyYAML 6.0.3 e PyInstaller 6.22.3. Essentials evita módulos Qt sem uso.
Versões instaladas estão fixadas em requirements-linux.lock (snapshot pip,
sem hashes; não é lock multiplataforma). Compatibilidade Windows ainda pendente.
Referências oficiais consultadas em 22/10/2026:

- https://doc.qt.io/qtforpython-6/gettingstarted.html
- https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html
- https://pyyaml.org/wiki/PyYAMLDocumentation
