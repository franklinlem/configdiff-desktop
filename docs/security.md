# Segurança nesta etapa

Somente dados sintéticos. A interface não aceita arquivos, não grava preferências,
não exporta relatórios e não inicia conexões. A prova YAML rejeita recursos perigosos
antes da composição e normaliza erros. Não usar o protótipo para dados reais.

Processo isolado permite cancelamento; não restringe permissões do usuário.
Não há promessa de apagar RAM, swap ou dumps. Testes de sentinelas, leitura limitada,
integridade e exportação sanitizada pertencem aos próximos incrementos.
