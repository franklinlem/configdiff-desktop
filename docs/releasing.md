# Distribuição

Este pacote é somente uma prova local 0.0.2, não release MVP. Build nativo onedir;
usar tar.gz no Linux para preservar symlinks das bibliotecas Qt. Comando de build no
README. Gerar SHA-256 do arquivo compactado e guardar junto do artefato.

O workflow phase0.yml prepara build/testes em Ubuntu 24.04 e Windows. Ainda não foi
executado em serviço remoto. requirements-windows.txt fixa dependências diretas;
falta obter lock transitivo de um Windows real. Não anunciar essas plataformas como
validadas com base no YAML do workflow.

Antes de uma release: validar máquina limpa sem Python e offline, Qt/teclado/escala,
cancelamento e fechamento no pacote, inventário de bibliotecas e avisos/licenças
(inclusive Qt/PySide LGPL), disponibilização exigível de fontes e escolha da licença
do código próprio. A proposta MIT ainda não foi confirmada. Não publicar artefato
como versão final antes desses itens e do aceite RF01–RF13.
