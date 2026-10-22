# Segurança — estado da fase 4

O fluxo de terminal lê somente os dois arquivos indicados, em processo isolado,
sem backend, telemetria, histórico ou acesso de rede iniciado pelo app.
A GUI utiliza o mesmo núcleo. Fixtures e benchmarks usam dados sintéticos.

Capturas limitadas e somente leitura preservam o conteúdo das origens; hashes são
verificados nos testes. O sistema pode atualizar atime ao ler. O processo isolado
permite timeout/cancelamento, mas não restringe permissões do usuário nem limita RAM
pelo sistema operacional. O protocolo privado aceita somente tipos internos; não
carrega serializações fornecidas nos arquivos de configuração.

Erros públicos têm somente código, lado e posição. Mensagens brutas de parser,
conteúdo e nomes/caminhos dos arquivos não entram nas mensagens de validação. Valores
ficam transitórios em memória e IPC. Não há promessa de apagar strings Python, RAM,
swap ou dumps. Encerramento/cancelamento remove referências mantidas pelo coordenador.

Relatórios recebem somente SanitizedReportDTO: caminho estrutural, categoria e tipos.
Não recebem árvores, valores ou metadados dos nomes dos arquivos. Exportam exatamente
a visão filtrada. Os nomes de chaves podem conter informação sensível; o aviso no
relatório orienta revisão. A busca só considera caminhos, nunca valores.

Caminhos são ASCII escapado e code spans com delimitador maior que qualquer sequência
de backticks contida neles. Isso impede que dados virem HTML, links, imagens ou
estrutura Markdown nos renderizadores CommonMark. Não usar conteúdo exportado como
HTML bruto nem interpretá-lo como outro formato. Testes adversariais cobrem controles,
bidi e sintaxe Markdown/HTML nas chaves.

A exportação recusa a origem por caminho/identidade e qualquer destino existente.
open exclusivo impede truncamento inclusive numa corrida que introduza symlink/hard
link. Não substitui relatórios anteriores. Novos arquivos POSIX usam modo máximo 0600;
Windows segue ACLs locais. Uma falha pode deixar relatório parcial sanitizado, com
mensagem de erro controlada. Não é defesa contra processos hostis com as mesmas
permissões do usuário nem garante persistência após falha de energia.

O indicador password/token/secret/api_key/private_key é auxiliar e incompleto. Todos
os valores são omitidos dos relatórios independentemente desse indicador. A GUI mascara
todos os valores, limita a revelação a uma célula por até 15 s e oculta
ao perder foco ou mudar o contexto. A prévia de string tem até 512 caracteres; não
revela subárvores de contêineres. Cópia de valores, tooltips de conteúdo e edição não
são oferecidos. Preferências contêm apenas esquema, tema, dimensões e formato.

A apresentação usa texto simples: nomes de arquivos e erros não viram rich text.
Limpar/fechar libera referências do resultado mantidas pela janela e cancela trabalho.
A revelação não altera o DTO de exportação. Não há promessa de apagar dados de captura
de tela, clipboard de caminhos, RAM ou histórico mantido pelo sistema operacional.
