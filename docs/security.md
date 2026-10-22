# Segurança — estado da fase 3

O fluxo de terminal lê somente os dois arquivos indicados, em processo isolado,
sem backend, telemetria, histórico, preferências ou acesso de rede iniciado pelo app.
A GUI continua demonstrativa. Fixtures e benchmarks usam dados sintéticos.

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
os valores são omitidos da saída independentemente desse indicador. O mascaramento e
revelação temporária na GUI serão implementados na fase 4.
