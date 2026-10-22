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
Versões instaladas estão fixadas em requirements-linux.lock (versões fixas com hashes SHA-256 do PyPI;
não é lock multiplataforma). Compatibilidade Windows ainda pendente.
Referências oficiais consultadas em 22/10/2026:

- https://doc.qt.io/qtforpython-6/gettingstarted.html
- https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html
- https://pyyaml.org/wiki/PyYAMLDocumentation


## Fundação do domínio — fase 1

`domain/nodes.py` contém Scalar, Mapping e Sequence imutáveis. O tipo escalar faz
parte da igualdade: boolean, integer e float são distintos. Mapeamentos canônicos
são ordenados por chave; listas mantêm posição; strings não são normalizadas.
`canonicalize` aceita somente tipos built-in, limita a profundidade e conta raiz
mais cada entrada de mapa/elemento de sequência recursivamente. Chaves não contam
como nós separados. Ausência é `None` na referência do resultado; null é Scalar(None).
Construtores não aceitam NaN/Infinity, duplicatas ou estrutura canônica mutável.

`domain/paths.py` usa Key e Index em tuplas. A apresentação começa em `$` e usa
colchetes com strings JSON para chaves: `$["a.b"]` difere de `$["a"]["b"]`.
Unicode é escapado em ASCII na apresentação, inclusive controles bidirecionais.
Escapar caminhos para Markdown será responsabilidade do exportador na fase 3.

`domain/results.py` separa DiffEntry/ComparisonResult (valores transitórios, ocultos
no repr) de SanitizedEntry/SanitizedReportDTO (somente caminho, categoria e tipos).
Não usar asdict nos resultados ricos para exportação. Contadores derivam das
entradas; o algoritmo de comparação será implementado na fase 3.

Erros públicos têm códigos enumerados, lado e posição opcionais. Não carregam
mensagens de bibliotecas, nomes de arquivo ou conteúdo. Exceções não serão o
protocolo do worker; serão projetadas em metadados controlados na integração.

ADR 0002: Ctrl+C marca uma flag em handler SIGINT; QTimer a consulta a cada 50 ms,
fecha a janela e encerra Qt com código 130. aboutToQuit e finally limpam trabalho
ativo. O filho ignora SIGINT e seu encerramento é coordenado pelo pai. Isso evita
KeyboardInterrupt surgir dentro de um slot Qt. Referências consultadas:

- https://docs.python.org/3.13/library/signal.html
- https://doc.qt.io/qtforpython-6/PySide6/QtCore/QCoreApplication.html

## Leitura e parsing isolados — fase 2

`services/files.py` abre somente para leitura, confirma arquivo regular com fstat,
limita a leitura inclusive se crescer e compara tamanho/mtime/ctime/inode antes e
depois. Symlink de entrada para arquivo regular é permitido. A captura usa o objeto
aberto; não promete detectar toda troca concorrente do caminho nem alterações que
preservem os metadados observados. Capturas não imprimem bytes em repr.

`workers/loading.py` implementa LoadJob com contexto spawn e timeout monotônico.
Recebe só Loaded (Node + identidade) ou Failure (código/lado/posição), nunca exceções
com mensagens de bibliotecas. O IPC é privado entre processos criados pela aplicação;
serializações fornecidas pelo usuário não são carregadas. Não há arquivos temporários
com conteúdo. Ctrl+C no filho é ignorado; cancelamento/kill é coordenado pelo pai.

ADR 0003: o Pipe é recebido por uma thread dedicada do pai, com fila consultável sem
bloqueio. Poll de pipe seguido de recv na GUI poderia bloquear em uma mensagem parcial
maior que seu buffer. Apenas parsing e leitura rodam no processo; a thread faz IPC.
Cancelamento termina o filho, aguarda por tempo limitado e descarta resposta tardia.
Não equivale a isolamento de permissões nem a promessa de zeragem da RAM.

ADR 0004: a versão definitiva de YAML interpreta eventos BaseLoader, em vez de adaptar
os construtores do SafeLoader sugerido originalmente. A política escalar é preservada,
e a contagem de profundidade/nós acontece antes de alocar cada nó. Rejeição de tokens
proibidos precede a construção. Referências oficiais consultadas nesta etapa:

- https://docs.python.org/3.13/library/json.html
- https://docs.python.org/3.13/library/os.html#os.open
- https://pyyaml.org/wiki/PyYAMLDocumentation

## Comparação e relatório — fase 3

`domain/comparison.py` percorre pares de nós, ordena a união de chaves e compara
listas por posição. Ausência e mudança de tipo emitem uma única entrada sem descer
no ramo. Nós compartilhados não vazios são percorridos; folhas e contêineres vazios
iguais geram Igual. O núcleo continua sem Qt.

`workers/base.py` concentra spawn, timeout, recepção em thread e encerramento; LoadJob
mantém a API anterior. ComparisonJob executa leitura/parsing de A e B e comparação no
mesmo processo. Erros são Failure, com lado A/B somente quando atribuíveis a uma
entrada. Timeout e falha geral não inventam lado. Compared mantém resultado e
referências de origem para proteção de escrita, sem expô-los em repr.

`services/reports.py` filtra somente caminhos/categorias e projeta entradas em DTO
sanitizado. O renderizador exige esse DTO, não ComparisonResult. Caminhos entram como
code spans com delimitador calculado; não há interpolação de conteúdo em markup ativo.
O aviso esclarece que nomes de chaves podem ser sensíveis.

ADR 0005: exportar somente para destino novo com O_CREAT|O_EXCL, sem truncamento,
substituição ou temporário. Simplicidade e integridade das origens prevalecem sobre
sobrescrever um relatório existente. SourceRef registra caminho absoluto/resolvido e
identidade capturada; eles não são serializados no relatório. Erros de escrita podem
deixar arquivo parcial sanitizado; o aplicativo não remove automaticamente esse nome.
Referências oficiais consultadas:

- https://docs.python.org/3.13/library/os.html#os.O_EXCL
- https://spec.commonmark.org/0.31.2/#code-spans


## Interface e preferências — fase 4

MainWindow coordena estados empty/selected/processing/done/cancelled/error. Nova
comparação ou troca de arquivo/formato invalida o resultado antes de iniciar trabalho.
ComparisonJob é consultado por QTimer; erros não mantêm resultados anteriores.
Exportação projeta exatamente as entradas ordenadas/filtradas do modelo em DTO sanitizado.

DiffTableModel usa QAbstractTableModel, sem widgets por célula. Exibe texto simples,
mascara todas as células de valores e fornece dados somente para apresentação/acessibilidade.
A revelação guarda apenas um par linha/coluna e um prazo monotônico, com QTimer de 15 s.
Troca de foco, modelo, seleção, filtros ou ordem revoga a revelação. Não ordena valores;
Ctrl+C da tabela é interceptado. Prévia escalar é limitada; contêineres não expõem filhos.

QSettings guarda somente esquema/tema/dimensões/formato, valida campos ao ler e grava
com sync atômico. A UI recebe PreferenceStore por injeção para testes sem tocar em
preferências pessoais. Estilos claro/escuro são locais à janela; tema do sistema não
substitui a paleta nativa. QScrollArea permite alcançar controles em área pequena.

O app agora cria MainWindow. ProbeWindow foi isolada para os testes históricos. O
smoke usa um diretório temporário somente de dados sintéticos e preferências isoladas,
com comparação, relatório sanitizado e cancelamento real, inclusive no executável.

A regressão SIGINT exige bloqueio POSIX durante spawn: proteger só a função do worker
não cobria imports do bootstrap. A máscara é restaurada no pai em finally; o filho
herda SIGINT bloqueado. SIGTERM/kill continuam disponíveis para cancelamento.
Referências Qt consultadas:

- https://doc.qt.io/qtforpython-6/PySide6/QtCore/QAbstractTableModel.html
- https://doc.qt.io/qtforpython-6/PySide6/QtCore/QSettings.html
