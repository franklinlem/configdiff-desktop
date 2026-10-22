# Segurança nesta etapa

Somente dados sintéticos. A interface não aceita arquivos, não grava preferências,
não exporta relatórios e não inicia conexões. A prova histórica YAML rejeita recursos proibidos
antes da composição e normaliza erros. O protótipo gráfico não compara dados reais.

Processo isolado permite cancelamento; não restringe permissões do usuário.
Não há promessa de apagar RAM, swap ou dumps. Testes de sentinelas, leitura limitada,
integridade e exportação sanitizada pertencem aos próximos incrementos.


Na fase 2, a CLI lê o arquivo indicado pelo usuário em processo isolado e imprime
somente metadados ou erro controlado. Conteúdo permanece transitório em memória e
IPC; não é persistido. Os testes usam apenas fixtures sintéticas. O domínio e parsers
não importam Qt. A GUI demonstrativa ainda não recebe arquivos. O mascaramento visual
e a exportação sanitizada serão implementados nas próximas fases.
