# ConfigDiff Desktop — Planejamento completo

**Autor:** Franklin Martins  
**Data:** 22/10/2026  
**Status:** planejamento para implementação; nenhum aplicativo ou repositório foi criado nesta etapa.  
**Release inicial:** v0.1.0 — MVP local para Linux e Windows.

## 1. Recomendação e resultado esperado

Desenvolver um aplicativo desktop que compare configurações JSON, YAML e .env sem enviar arquivos à internet. Ele deve mostrar chaves ausentes, valores diferentes e mudanças de tipo, mantendo valores ocultos por padrão e permitindo exportar um relatório sanitizado.

O primeiro uso será comparar configurações fictícias representativas dos ambientes de desenvolvimento, homologação e produção dos projetos de Franklin. Configurações reais só serão usadas localmente após validar o mascaramento. O programa não acessará VPS, Docker ou Coolify, nem precisará de SSH.

A escolha atende a um problema recorrente de administração de aplicações, produz um projeto de portfólio independente e permite validar o produto sem aumentar a carga da VPS Contabo. ReleaseLedger e BackupProof são alternativas futuras, com maior dependência de infraestrutura e integrações.

### Objetivos verificáveis

- Abrir dois arquivos, comparar e identificar diferenças em até três ações principais: selecionar A, selecionar B e comparar.
- Detectar corretamente todos os casos da suíte de referência aprovada.
- Não incluir valores das configurações em exportações, logs ou preferências do MVP.
- Funcionar sem conexão, sem conta e sem serviço de backend.
- Manter os arquivos de origem sem alteração, comprovada por hashes antes/depois nos testes.
- Distribuir pacotes testados em Linux e Windows, com limitações documentadas.

### Requisitos e hipóteses

**Confirmado pelo pedido:** escolher um projeto da seleção e planejar antes de desenvolver.

**Decisões propostas neste plano:** ConfigDiff Desktop, interface em português do Brasil, Python e Qt, funcionamento local, MVP sem edição de arquivos, prioridade de validação no Debian/KDE de Franklin e suporte adicional ao Windows.

**Hipóteses de estimativa:** desenvolvimento individual assistido por IA; 10–15 horas semanais; acesso posterior a uma máquina ou VM Windows para teste manual; arquivos de texto pequenos ou médios. As decisões técnicas poderão ser ajustadas após os protótipos, sem ampliar silenciosamente o escopo.

## 2. Escopo por versão

| Recurso | v0.1.0 MVP | Próxima versão |
|---|---|---|
| JSON, YAML, .env | Sim | Melhorias de compatibilidade |
| Comparação estrutural de dois arquivos do mesmo formato | Sim | Comparação entre formatos por regra explícita |
| Filtros, busca por caminho, contadores | Sim | Perfis de comparação |
| Valores ocultos e revelação temporária na tela | Sim | Regras personalizadas de sensibilidade |
| Exportação Markdown sanitizada | Sim | JSON sanitizado |
| Tema claro/escuro e atalhos | Sim | Internacionalização |
| TOML e INI | Não | v0.2 |
| Comparação entre três ou mais ambientes | Não | v0.3 |
| Comparação textual | Não | Somente após política de proteção própria |
| Edição, merge e sincronização | Não | Exigem novo planejamento |

Também ficam fora: login, banco remoto, IA, telemetria, acesso SSH, execução de comandos, importação de URLs, leitura automática de diretórios, atualização automática, SaaS, pagamentos e plugins executáveis.

## 3. Fluxos de utilização

### Comparação normal

1. O usuário seleciona A e B por diálogo nativo; cada lado permite escolher explicitamente o formato.
2. A aplicação mostra apenas nome do arquivo, formato e tamanho. Caminho completo fica em detalhe acessível sob demanda.
3. Ao comparar, lê uma captura de cada arquivo com limites de recursos e valida a sintaxe.
4. Se um lado falhar, não apresenta comparação parcial como resultado válido.
5. Exibe contadores e tabela: caminho, categoria, tipo A, tipo B e valores ocultos.
6. O usuário filtra por categoria e pesquisa caminhos. A busca não varre valores.
7. Pode revelar uma célula temporariamente ou exportar um relatório sem valores.

### Erros e estados

Estados da interface: vazio, arquivos selecionados, processando, concluído, cancelado e erro. Cancelamento descarta resultados incompletos. Nova comparação oculta qualquer revelação anterior. Erros apontam lado, categoria e linha/coluna quando disponíveis, sem reproduzir o conteúdo da linha ou a mensagem bruta do parser.

Arquivo alterado durante a leitura: invalidar a tentativa quando a verificação de metadados detectar alteração; permitir repetir. A comparação usa as capturas lidas, sem prometer detectar todas as modificações concorrentes possíveis.

### Exemplo público

A: APP_ENV=development, DB_PASSWORD=segredo-a. B: APP_ENV=production, DB_PASSWORD=segredo-b.

A interface informa duas diferenças. Os valores ficam ocultos até revelação individual; DB_PASSWORD recebe indicador de potencial segredo. O relatório contém os caminhos e a classificação das diferenças, sem os quatro valores. Todos os exemplos distribuídos serão sintéticos.

## 4. Requisitos funcionais e critérios de aceite

| ID | Requisito | Aceite |
|---|---|---|
| RF01 | Selecionar arquivos locais regulares | Validar acesso, tipo e tamanho; rejeitar diretórios e dispositivos |
| RF02 | Detectar formato e permitir seleção manual | Extensões conhecidas preenchem o formato; ambiguidade exige escolha |
| RF03 | Interpretar JSON | Rejeitar sintaxe inválida, duplicatas e números não finitos |
| RF04 | Interpretar YAML seguro | Rejeitar tags arbitrárias, duplicatas, aliases e múltiplos documentos |
| RF05 | Interpretar .env documentado | Aceitar o subconjunto definido na seção 7; rejeitar entradas ambíguas |
| RF06 | Comparar estruturas | Identificar ausente em A/B, tipo alterado, valor alterado e igual |
| RF07 | Ocultar valores | Nenhum valor visível ao concluir a comparação |
| RF08 | Revelação temporária | Revelar só a célula solicitada; ocultar ao perder foco, trocar arquivo ou após 15 segundos |
| RF09 | Buscar e filtrar | Pesquisa por caminho e filtros combináveis, com contagem coerente |
| RF10 | Exportar Markdown | Exportar a visão filtrada, sem valores, trechos brutos ou caminhos locais absolutos |
| RF11 | Preferências mínimas | Salvar tema, tamanho de janela e formato preferido; nunca conteúdo ou nomes dos arquivos |
| RF12 | Cancelar e limpar | Encerrar trabalho com limite de espera e remover referências ao resultado anterior |
| RF13 | Utilização acessível | Operações principais por teclado, foco visível e status também por texto |

## 5. Requisitos não funcionais

- **Privacidade:** nenhum tráfego de rede iniciado pela aplicação; bibliotecas não podem habilitar telemetria. Sem histórico de arquivos, caches de conteúdo ou relatórios automáticos.
- **Integridade:** abrir origem somente para leitura; exportação nunca pode sobrescrever A ou B, inclusive por caminho equivalente, symlink ou hard link detectável.
- **Responsividade:** parsing e comparação fora da thread da interface; tabela com modelo Qt, sem criar um widget por célula.
- **Metas iniciais de recursos:** máximo de 5 MiB por arquivo, profundidade 64 e 50 mil nós por documento; leitura também limitada, mesmo se o arquivo crescer. Listas contam seus elementos e mapeamentos contam suas entradas.
- **Orçamento por execução:** 10 segundos como limite inicial de trabalho; cancelar e terminar o processo isolado se excedido. Validar esse valor no protótipo.
- **Desempenho alvo:** até 2 segundos para o par de fixtures de 1 MiB/10 mil nós no notebook Debian de referência, sem incluir seleção ou gravação; meta a medir, não garantia antecipada.
- **Compatibilidade proposta:** Debian 13 KDE como alvo primário e Ubuntu 24.04 como alvo Linux adicional; Windows 11 x64 como alvo secundário. Builds não testados não serão anunciados como suportados.
- **Manutenção:** tipagem no núcleo, lint, testes determinísticos, dependências fixadas em lockfile e documentação das escolhas.

## 6. Tecnologia e alternativas

| Decisão | Escolha | Justificativa / alternativa |
|---|---|---|
| Runtime | Python 3.12 ou superior, versão exata fixada no bootstrap | Bibliotecas maduras; validar combinação Python/Qt no Debian e Windows |
| GUI | PySide6, Qt Widgets | Adequado a tabelas e diálogos nativos; QML adicionaria complexidade visual desnecessária |
| JSON | json da biblioteca padrão, com hooks restritivos | Não precisa de dependência adicional |
| YAML | PyYAML com SafeLoader adaptado e validações adicionais | safe_load isolado não resolve duplicatas nem todos os limites de recursos |
| .env | Parser pequeno com gramática restrita e testes | Não depender de expansão de variáveis ou execução de shell |
| Preferências | QSettings | Dispensa SQLite para poucas opções não sensíveis |
| Qualidade | pytest, pytest-qt, Ruff e verificação de tipos | Testes de domínio separados dos testes Qt |
| Empacotamento | PyInstaller em modo diretório | Facilita diagnóstico e distribuição das bibliotecas; build por sistema operacional |
| Repositório proposto | franklinlem/configdiff-desktop | Ainda não criado; verificar disponibilidade ao implementar |
| Licença proposta | MIT para código próprio | Inventariar e cumprir licenças de dependências e bibliotecas distribuídas |

Uma interface web local facilitaria prototipagem visual, mas acrescentaria navegador e dificuldades de integração com arquivos. Electron/Tauri são viáveis, porém não oferecem vantagem suficiente para este MVP. Não usar SQLite até existir necessidade real de dados estruturados persistentes.

Versões exatas de PySide6, PyYAML, PyInstaller e ferramentas serão verificadas e fixadas ao iniciar o projeto, considerando compatibilidade e avisos oficiais. Não usar tags latest nos processos de release.

## 7. Contrato de parsing e comparação

### Modelo canônico

Cada documento contém nós de mapeamento, sequência ou escalar. Escalares têm tipo explícito: null, boolean, integer, float ou string. Não usar apenas igualdade Python: true e 1 devem ser classificados como tipos diferentes. Comparar floats finitos exatamente, sem tolerância implícita.

Caminhos internos serão tuplas de segmentos tipados, evitando colisão entre a chave literal a.b e a estrutura a → b, ou entre chave "0" e índice 0. A apresentação usa caminho escapado e indicação de índices; o formato deve ser testado com caracteres especiais. Mapeamentos ignoram ordem e preservam distinção de maiúsculas/minúsculas. Listas são comparadas por posição, sem detecção de movimentação no MVP.

Uma ausência é diferente de null e de string vazia. Se o tipo de um nó mudar, emitir uma diferença naquele caminho e não multiplicar diferenças de seus descendentes. Nós presentes somente em um lado também produzem uma diferença na raiz ausente. Filtros e contadores seguem essa mesma unidade de diferença.

### JSON

UTF-8 com BOM opcional; rejeitar codificação inválida. Rejeitar chaves duplicadas, NaN e Infinity. Aceitar raiz escalar, lista ou objeto. Ordem dos objetos não altera resultado. Strings Unicode são comparadas sem normalização automática; espaços dentro dos valores são significativos.

### YAML

Suportar um documento com chaves string, listas e escalares do subconjunto documentado. Rejeitar aliases, anchors, merge keys, chaves complexas, tags customizadas e múltiplos documentos. Desabilitar inferência automática de datas e regras surpreendentes de booleanos; documentar true/false e política numérica explicitamente com fixtures. Não prometer compatibilidade completa com YAML 1.2. Verificar tamanho e tokens antes de construir a árvore; limites finais de nós e profundidade continuam obrigatórios.

### .env

UTF-8 com BOM opcional; linhas vazias e comentários iniciados por # são aceitos. Chaves seguem [A-Za-z_][A-Za-z0-9_]*. Aceitar prefixo export, valor vazio e valores de uma linha, com aspas simples ou duplas. Comentário após valor sem aspas só começa com espaço seguido de #. Em aspas duplas, admitir somente escapes documentados para aspas e barra invertida. Rejeitar duplicatas, multilinhas, escapes desconhecidos e linhas sem =.

Valores permanecem strings: false não vira booleano. Não expandir $VAR, ${VAR}, ~ ou substituição de comandos. Esses trechos são dados literais, nunca comandos. Não executar source. O README terá exemplos aceitos e rejeitados; o programa não afirmará suportar todas as variantes de dotenv.

### Resultados

DiffEntry: caminho tipado, categoria, tipos A/B e referências transitórias para valores. ComparisonResult: formatos, contadores, duração e diferenças. Relatórios recebem exclusivamente um SanitizedReportDTO, sem valores ou objetos originais. Não serializar DiffEntry diretamente.

## 8. Arquitetura e estrutura

Fluxo: interface → serviço de comparação → processo de trabalho isolado → leitura limitada → parser → árvore canônica → comparador → resultado → modelo Qt. Exportação parte de uma projeção sanitizada separada.

O processo isolado permite finalizar entradas excessivas sem travar a GUI. Ele não constitui sandbox de segurança do sistema operacional. A comunicação deve transportar somente estruturas controladas e não carregar serializações fornecidas pelo usuário. Não criar arquivos temporários com conteúdo. Cancelamento, processo travado e encerramento da janela terão testes próprios, especialmente no Windows.

Estrutura proposta:

- src/configdiff/domain/: tipos, caminhos e algoritmo de comparação.
- src/configdiff/parsers/: json_parser, yaml_parser e env_parser.
- src/configdiff/services/: leitura, coordenação, sanitização e exportação.
- src/configdiff/workers/: processo de trabalho e protocolo de mensagens.
- src/configdiff/ui/: janela, modelos de tabela, diálogos e temas.
- src/configdiff/settings/: preferências e versão de esquema.
- tests/unit/, tests/integration/, tests/gui/ e tests/fixtures/.
- docs/: arquitetura, formatos suportados, segurança e distribuição.
- packaging/: especificações PyInstaller e scripts de release.
- .github/workflows/: qualidade e builds.

O núcleo não importa Qt. Parsers não conhecem interface ou relatório. A interface não implementa regras de comparação. Injeção das funções de leitura e relógio permitirá testar erros e temporização sem depender de arquivos reais de produção.

## 9. Proteção de informações

Ocultar todos os valores por padrão evita depender da capacidade de reconhecer nomes secretos. Um classificador adicional marca nomes como password, token, secret, api_key e private_key, sem alegar detecção completa. A política de exportação do MVP exclui todos os valores, inclusive os revelados na tela.

- Não exibir editor de texto bruto no MVP.
- Não oferecer cópia de valores; apenas caminhos, sob ação explícita.
- Logs registram códigos de erro e durações, sem nomes de arquivos, caminhos, chaves ou valores.
- Escapar Markdown e caracteres de controle/bidirecionais nos caminhos exportados; não criar links ativos a partir de entradas.
- Preferências gravadas de forma segura, com validação e retorno aos padrões em caso de corrupção.
- O relatório avisa que nomes de chaves podem revelar informações e permite omitir entradas pelos filtros.
- Sem promise de apagamento seguro da RAM: strings Python, swap, dumps do sistema e capturas de tela estão fora dessa garantia. Limpar referências reduz retenção, mas não assegura zeragem.
- Seleção de symlink de entrada pode ser aceita após resolver para arquivo regular; capturar metadados do arquivo aberto. Exportações exigem proteção contra equivalência com entradas.
- Não operar com privilégios administrativos. Documentar que arquivos legíveis pelo usuário continuam sujeitos às permissões do sistema.

## 10. Interface e acessibilidade

Janela inicial com dois seletores, seletor de formato e botão Comparar. Resultado em tabela central; filtros e contadores acima, status e progresso abaixo. Colunas redimensionáveis e painel de detalhes recolhível. Mensagens em português direto.

Atalhos propostos: Ctrl+O para A, Ctrl+Shift+O para B, Ctrl+Enter para comparar, Ctrl+F para busca, Ctrl+E para exportar e Esc para cancelar ou ocultar valores revelados, conforme estado. Documentar conflitos com atalhos do sistema e testar navegação somente por teclado.

Tema segue o sistema inicialmente, com opção claro/escuro. Não usar somente cor para status: apresentar texto e ícone. Nome acessível nos botões, ordem de foco lógica e suporte a fontes ampliadas. Testar notebook em 1366×768 e escala de 125–200%, sem botões essenciais inacessíveis.

## 11. Estratégia de testes

| Camada | Casos essenciais | Evidência |
|---|---|---|
| Parsers | Duplicatas, UTF-8/BOM, vazio, sintaxe, limites, YAML hostil e .env ambíguo | Fixtures sintéticas e erros estáveis sem conteúdo |
| Comparador | null/ausente, bool/int, listas, raiz escalar, chaves escapadas | Resultados esperados por caminho e categoria |
| Propriedades | Comparar A com A; inverter A/B; mudar ordem de objetos | Sem diferenças no primeiro caso e simetria documentada |
| Privacidade | Segredos sentinela em valores, erros e exportações | Nenhum sentinela em relatório, logs ou preferências |
| Arquivos | Permissão negada, arquivo removido, crescimento e saída equivalente | Erro controlado e hashes de origem preservados |
| Trabalho isolado | Cancelar, timeout, fechar janela e falha do processo | GUI utilizável e sem processo órfão |
| GUI | Selecionar, comparar, filtrar, revelar/ocultar, exportar | pytest-qt e roteiro manual |
| Pacotes | Iniciar sem Python instalado e sem internet | Smoke test em cada sistema alvo |

Testes adversariais verificarão que nomes de chaves e erros de parser não injetam conteúdo em diálogos ou Markdown. Testar mascaramento também após ordenação, troca de arquivo, filtros e cancelamento. Testes automatizados usam dados fictícios; nunca subir .env real como fixture.

Cobertura é auxiliar, sem meta global artificial: todos os ramos de segurança, categorias de diferença e contratos de parsing devem ter testes. Benchmark terá máquina e fixture registrados. Monitorar consumo de memória no protótipo para validar limites em vez de assumir que SafeLoader basta.

## 12. Plano de execução e estimativas

Franklin será responsável pelo aceite funcional e teste no ambiente pessoal; o desenvolvimento assistido cobrirá código, documentação e automação. Cada fase só avança após seu critério de aceite.

| Fase | Entradas / dependências | Entrega e aceite | Esforço |
|---|---|---|---|
| 0 — Provas de viabilidade | Este plano | Janela Qt e pacote mínimo em Linux/Windows; processo cancelável; validar política YAML | 6–9 h |
| 1 — Fundação | Fase 0 | Estrutura, lockfile, lint, testes e contratos canônicos executáveis | 4–6 h |
| 2 — Parsers | Fase 1 | Três parsers e suíte de entradas aceitas/rejeitadas; limites aplicados | 9–13 h |
| 3 — Comparação e privacidade | Fase 2 | Diferenças corretas, sanitização e relatório sem sentinelas | 7–10 h |
| 4 — Interface | Fase 3 | Fluxo completo, acessibilidade, filtros e revelação temporária | 9–13 h |
| 5 — Distribuição e validação | Fase 4 | Pacotes, CI, documentação e roteiro de aceite executado | 8–12 h |
| Reserva | Problemas de compatibilidade | Correções sem ampliar escopo | 6–10 h |

**Total:** 49–73 horas. A 10–15 horas semanais, reservar aproximadamente 4–8 semanas corridas. Uma execução concentrada pode ser mais rápida; não tratar a estimativa original de 2–4 semanas como compromisso. Não inclui tempo de publicação em lojas ou comercialização.

**Caminho crítico:** compatibilidade Qt/empacotamento → contratos de parsing → comparação e sanitização → GUI → validação dos pacotes. Não investir em acabamento visual antes das provas de viabilidade.

**Marcos:** M0 viabilidade; M1 núcleo correto; M2 fluxo completo; M3 candidato de release; M4 v0.1.0 validada.

## 13. Riscos e contingências

| Risco | Probabilidade / impacto | Sinal de alerta | Mitigação e contingência |
|---|---|---|---|
| Vazamento no relatório | Média / alto | Sentinela aparece em saída | DTO sem valores; bloquear release e corrigir antes de distribuir |
| YAML excessivo | Média / alto | Consumo ou tempo acima do limite | Restrições prévias e processo terminável; reduzir subconjunto suportado |
| Semântica ambígua de .env | Alta / médio | Arquivo popular não é aceito | Gramática explícita; rejeitar com orientação; ampliar só com testes |
| Qt incompatível no Linux | Média / alto | Falta de plugin ou falha Wayland | Teste inicial no Debian/KDE; fixar combinação e documentar dependências |
| Pacote Windows problemático | Média / médio | Não inicia ou antivírus bloqueia | Build nativo e teste limpo; marcar Windows experimental até validação |
| Falta de ambiente Windows | Média / médio | Apenas CI disponível | Entregar Linux primeiro, sem declarar Windows validado |
| Crescimento de escopo | Alta / médio | Pedido de merge, SSH ou múltiplos ambientes | Backlog separado; manter critérios da v0.1 |
| Licenças incompletas no pacote | Média / alto | Avisos ou fontes exigidos ausentes | Inventário e revisão das condições oficiais antes do release |

## 14. CI/CD, distribuição e operação

Em pull requests: lint, tipos, testes do núcleo e testes Qt headless onde suportados. Matriz inicial com Linux e Windows e versões Python escolhidas na fase 0. Build de release em runners nativos; não prometer cross-compilation. Release por tag após checks e aceite manual.

Produzir pacote Linux em diretório compactado e pacote Windows portátil em ZIP, com README, versões e avisos de terceiros. Instalador Windows e AppImage são melhorias posteriores, condicionadas aos testes; não são necessários para chamar o MVP de funcional. Gerar SHA-256 dos artefatos e inventário de dependências. Assinatura de binários não está orçada.

Sem deploy na Contabo ou Hostinger para o aplicativo. Uma landing page poderá ser criada depois, sem conter arquivos de usuários. Não serão alterados domínios, contas ou servidores na implementação inicial.

Custo inicial de infraestrutura: nenhum servidor adicional. Custos possíveis: tempo de desenvolvimento, eventual runner/armazenamento além das franquias e assinatura de binários, se adotada. Não assumir que serviços externos permanecerão gratuitos.

## 15. Documentação e entrega final

- Código organizado, testes e exemplos totalmente sintéticos.
- README com instalação, utilização e limitações.
- docs/formats.md com gramática e diferenças semânticas.
- docs/security.md com fluxo dos dados e limites do mascaramento.
- docs/architecture.md com contratos e responsabilidades.
- docs/releasing.md com builds reproduzíveis e aceite por plataforma.
- CHANGELOG, licença do código próprio e avisos das dependências.
- Pacotes validados e checksums; lista explícita de sistemas realmente testados.

## 16. Definição de pronto

A v0.1.0 está pronta quando RF01–RF13 passam; fixtures de referência produzem as diferenças esperadas; entradas hostis terminam dentro dos limites; origem permanece intacta; relatórios/logs/preferências não contêm valores sentinela; interface funciona por teclado; pacote inicia offline no sistema declarado; documentação e inventário de licenças acompanham a entrega. Falha de privacidade ou corrupção de origem bloqueia a versão.

Aceite pessoal: comparar três pares fictícios inspirados em WebhookLab, CertGuard e uma aplicação genérica, localizar uma chave ausente, uma alteração de tipo e uma mudança de segredo, exportar o relatório e conferir que ele contém apenas metadados permitidos. Não incluir dados policiais ou credenciais reais nesse roteiro.

## 17. Decisões pendentes e próximos três passos

As propostas permitem começar sem perguntas adicionais. Permanecem para confirmação ao longo da execução: licença final do código próprio, disponibilidade do ambiente Windows e eventual preferência por nome comercial. Nenhuma impede a prova de viabilidade local.

1. Criar a pasta/repositório de trabalho e registrar este plano como documentação do projeto, sem publicar automaticamente um repositório remoto.
2. Executar a fase 0: validar Qt no Debian/KDE, empacotamento mínimo e processo cancelável.
3. Fixar versões compatíveis e implementar contratos, fixtures e núcleo de parsing antes da interface completa.

Este documento encerra a etapa solicitada de planejamento. Desenvolvimento, publicação e testes reais do aplicativo ainda não foram executados.

## 18. Referências técnicas oficiais

Consultadas em 22/10/2026; versões exatas devem ser verificadas novamente no bootstrap.

- Qt for Python: https://doc.qt.io/qtforpython-6/
- Licenciamento Qt for Python: https://doc.qt.io/qtforpython-6/commercial/index.html
- PyYAML, SafeLoader e avisos sobre carregamento inseguro: https://pyyaml.org/wiki/PyYAMLDocumentation

As escolhas de escopo, limites e estimativas são decisões deste plano, não garantias fornecidas pelas bibliotecas.
