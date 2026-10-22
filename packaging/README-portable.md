# ConfigDiff Desktop — candidato Linux local

Execute `./ConfigDiff` nesta pasta. Não é necessário instalar Python.
Referência validada: Debian 13 x86_64, com bibliotecas do sistema para OpenGL
(`libgl1`, `libegl1`) e fontes. Para usar a janela, é necessária sessão gráfica.
Outras distribuições e Windows ainda não estão validados.

Selecione A e B, confirme o formato e clique Comparar. Use examples/example.json e
examples/example-b.json para experimentar. Valores ficam ocultos; selecione uma
célula Valor A/B e use Revelar célula para prévia de até 15 segundos. Esc oculta
ou cancela. Relatórios Markdown nunca incluem valores e exigem nome de arquivo novo.

A pasta docs contém formatos, privacidade, atalhos e limitações. build-info.json
registra ambiente/versões e files.sha256 permite verificar os arquivos regulares.
bundle-inventory.json inventaria binários e proveniência; THIRD_PARTY_NOTICES.md
explica licenças e as pendências para publicação. source contém o código versionado
usado neste build, sem arquivos locais não versionados.

Este é um candidato local, não uma release pública aprovada. O código próprio usa MIT. A correspondência completa de fontes/atribuições Qt
permanece para revisão.
O pacote não é assinado. Não excluir ou mover isoladamente _internal.

O RC2 acrescenta avisos/índice upstream. Fontes de dependências acompanham em arquivo
separado configdiff-0.1.0rc2-upstream-sources.tar; preserve-o para avaliação da distribuição.
MIT aplica-se ao código próprio; os componentes de terceiros mantêm suas licenças.
