# Fase 5 — candidato local de distribuição

Versão 0.1.0rc1, em 22/10/2026. O aceite funcional geral da interface Linux foi dado
por Franklin; detalhes e limites em acceptance.md. Não é uma release pública final.

## Preparação entregue

- Build nativo por scripts/build_candidate.py, documentação e exemplos sintéticos.
- Inventário de binários/provedores, versões e metadados de build, sem caminhos locais
  do ambiente usados como campos de proveniência.
- Textos de licença disponíveis dos pacotes, copyrights Debian e avisos de terceiros.
- Arquivo fonte somente com arquivos Git versionados; relatório local não versionado
  de Franklin preservado e excluído de fontes, exemplos e documentação empacotados.
- Hashes SHA-256 de arquivos regulares e do arquivo de distribuição.
- Imagem de teste Debian com digest-base fixado, sem Python, e execução sem rede.
- Workflow nativo Linux/Windows preparado para gerar candidatos; sem publicação automática.
- Proposta MIT concreta em LICENSE.proposed, sem assumir confirmação da licença final.

O primeiro teste no Debian mínimo revelou ausência de libGL.so.1. O ambiente documentado
foi ajustado para instalar libgl1/libegl1, fontes e configuração Fontconfig, preservando
a distinção entre runtime portátil e dependências de sistema. A imagem de teste não
instala Python, roda usuário sem privilégios, filesystem somente leitura, /tmp em tmpfs,
sem capabilities e com rede desabilitada. O bundle é montado somente para leitura.

## Evidências finais

| Verificação | Resultado |
|---|---|
| Ruff lint/formatação e mypy | Passaram |
| pytest headless completo | 227 testes passaram em 30,93 s |
| Build nativo do candidato | Concluído |
| Inventário de binários | 180 entradas; 79 provedores Debian identificados |
| SHA-256 do arquivo compactado | Conferiu antes de extrair |
| Manifesto do pacote extraído | 419 arquivos regulares verificados |
| Smoke da cópia extraída no desktop Wayland | Passou |
| Smoke da cópia extraída no Debian isolado | Passou sem Python, sem rede, bundle somente leitura e usuário 1000 |
| Exclusão do relatório local | Conferida em fontes, docs e exemplos do pacote |

Artefato: dist/configdiff-0.1.0rc1-linux-x86_64.tar.gz, 61968269 bytes (~59,1 MiB),
com .tar.gz.sha256 ao lado. SHA-256:

```text
2a5d5a9954aea09fa991012e7502d19fa3c97e177dee0a11ee3e715ad7ecc10d
```

O conteúdo e o snapshot de fontes do candidato foram preservados após a validação;
este registro final é evidência posterior ao build, no repositório de trabalho.
Os hashes internos cobrem arquivos regulares; o hash do arquivo compactado cobre
também a estrutura e symlinks. O inventário não é um SBOM SPDX certificado.

Imagem de teste: sha256:be0afa621728cc24a51da180184739173ac866a5872b149fc34530fea1d49fd6.
Base fixada: debian:13-slim@sha256:62bd423aeee912639ca8ee681c2b762cb3e25137e0a92b20be455898a9f034ad.
Pacotes gráficos instalados: libgl1/libegl1 1.7.0-1+b2, fontconfig-config 2.15.0-2.3,
fonts-dejavu-core 2.37-8. A presença de python3 é explicitamente rejeitada pelo ensaio.
O teste isolado é headless; não substitui aceite desktop em outro sistema.

## Pendências reais de release

1. Confirmar a licença final do código próprio antes de publicação.
2. Completar atribuições/fontes correspondentes dos terceiros incorporados nos wheels
   Qt/ICU/plugins e validar as condições aplicáveis de distribuição/substituição LGPL.
   Os textos e links reunidos não são uma certificação de conformidade completa.
3. Executar a matriz Windows nativa, obter lock transitivo e fazer aceite desktop;
   Ubuntu 24.04 ainda não validado nesta execução.
4. Concluir ensaios manuais específicos de acessibilidade/escalas/tempo de revelação.

Código, candidato e evidências ficam locais. Nenhum servidor existente foi alterado,
nenhuma imagem/container de aplicação do usuário foi removida, nenhuma release/tag ou
repositório remoto foi publicado. A imagem de smoke é nova e específica deste projeto;
containers de teste são descartados com --rm.
