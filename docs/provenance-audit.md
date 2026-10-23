# Auditoria de proveniência do RC2 Linux

Em 22/10/2026 Franklin confirmou que extraiu e executou o RC2 em
dist/teste/ConfigDiff, com funcionamento correto. Foram conferidos os 668 hashes
dessa cópia sem modificar seus arquivos. O aplicativo e os arquivos RC2 distribuídos
continuam com os hashes já aceitos; este incremento acrescenta evidências e fontes.

## Identidade dos binários

A auditoria separa:

- 74 bibliotecas/extensões dos wheels PySide6 Essentials/Shiboken6 6.12.0 e PyYAML 6.0.3.
- 105 bibliotecas/extensões de 79 pacotes binários Debian, associados a 57 pacotes-fonte.
- Um executável gerado pelo PyInstaller, vinculado ao inventário e snapshot do projeto.

Os 179 arquivos de dependências conferem em SHA-256 com o material usado no build.
Os 74 arquivos de wheels também conferem byte a byte com os wheels publicados,
baixados do PyPI e verificados contra seu SHA-256 oficial. Para os 105 arquivos Debian,
o conteúdo original confere com os registros MD5 locais do dpkg e, em SHA-256, com o
bundle. Nenhuma divergência foi encontrada. O MD5 aqui é o registro do instalador,
não uma nova assinatura criptográfica nem comparação com um .deb baixado nesta etapa.

O relatório third_party/binary-provenance.json vincula a auditoria ao inventário,
ao snapshot de fontes do projeto e ao executável gerado. Não contém caminhos absolutos
dos arquivos originais do ambiente de build. Os wheels selecionados, URLs e hashes
ficam em third_party/published-wheels.json; suas cópias locais são cache de auditoria
em dist/provenance-wheels, sem entrar no pacote auxiliar de fontes.

## Fontes Debian exatas

Foram encontradas no índice APT local as versões exatas dos 57 pacotes-fonte; nenhuma
foi substituída por uma versão mais nova ou próxima. Após deduplicação de registros,
são 193 arquivos únicos (~337,1 MiB): descritores .dsc, originais upstream, patches e
instruções Debian, além de assinaturas disponibilizadas nos respectivos registros.
Todos foram baixados e conferidos pelo SHA-256 do índice APT de origem. O índice local
é o administrado pelo APT da máquina de build; esta etapa não importa novas chaves
nem revalida assinaturas OpenPGP dos .dsc individualmente.

third_party/debian-sources.json preserva pacote, versão, arquivos, tamanhos, URLs e
hashes. Repositórios usados: deb.debian.org/debian e security.debian.org/debian-security.
Esses arquivos são complementares às oito fontes Qt/PySide/ICU/PyYAML/LibYAML já reunidas.

## Artefatos complementares

- configdiff-0.1.0rc2-linux-x86_64.tar.gz: aplicativo Linux aprovado, inalterado.
- configdiff-0.1.0rc2-upstream-sources.tar: oito fontes upstream já verificadas.
- configdiff-0.1.0rc2-debian-sources-and-provenance.tar: 193 arquivos fonte Debian,
  relatórios de proveniência, manifests, documentação, MIT e scripts de auditoria.

Cada arquivo possui .sha256 ao lado. Os dois arquivos de fontes devem acompanhar o
aplicativo ao preparar a distribuição completa. Não é necessário extraí-los para
executar a interface. Os arquivos fonte são distribuídos em sua forma original;
nenhum script desses projetos é executado durante download, conferência ou empacotamento.

## Reproduzir a auditoria

No checkout do projeto, com o mesmo build/ConfigDiff/COLLECT-00.toc, ambiente de build
e dist/ConfigDiff do RC2:

```sh
.venv/bin/python scripts/audit_provenance.py
.venv/bin/python scripts/package_provenance.py
```

A auditoria usa rede apenas nas ferramentas de manutenção, para fontes e wheels;
o aplicativo permanece sem esse fluxo. Arquivos já válidos em cache são reutilizados.
Alteração no ambiente pode mudar os candidatos ou versões disponíveis no índice APT;
os manifests versionados preservam a evidência desta execução. A auditoria falha se
não encontrar a versão fonte exata ou detectar diferença de conteúdo.

O pacote auxiliar não inclui os caminhos originais privados do COLLECT-00.toc. Os
scripts nele são referência para repetir a auditoria no checkout/build, não uma
promessa de reprodução com qualquer instalação Debian. Para reconstruir a aplicação
usando seu snapshot sem .git, inicialize um repositório Git local e versione o snapshot
antes de seguir docs/releasing.md. Isso atende à seleção explícita de arquivos do
script de build, sem incluir relatórios pessoais não versionados.

## Alcance e validação ainda pendente

A rastreabilidade foi concluída no nível de arquivos binários, pacotes e versões
fonte disponíveis. Não houve recompilação independente de Qt/PySide/Debian para obter
binários idênticos, reconstrução completa da toolchain upstream ou assinatura do
relatório. Igualdade dos arquivos publicados não equivale a prova de build reproduzível
nem a certificação jurídica. As instruções e patches Debian estão nas respectivas
fontes; configurações dos wheels continuam sendo as do fornecedor.

Na etapa original desta auditoria, Windows e publicação remota ainda estavam pendentes.
Posteriormente, o repositório privado foi criado e a matriz Ubuntu/Windows passou
([CI](github-actions.md)); Franklin também aceitou o pacote na VM Windows 11 Enterprise
([aceite](acceptance.md)). Acessibilidade detalhada e aceite desktop Ubuntu permanecem
pendentes. Nenhuma release pública foi criada. Esta auditoria de proveniência continua
restrita ao pacote Debian analisado.

Referências oficiais consultadas:

- https://manpages.debian.org/trixie/dpkg-dev/dsc.5.en.html
- https://packaging.python.org/en/latest/specifications/recording-installed-packages/


## Resultados finais do incremento

Ruff lint/formatação e mypy passaram; os seis testes focados de empacotamento passaram
em 0,42 s. Eles cobrem exclusão de arquivos não versionados, caminhos fora da raiz,
versão fonte exata, hash divergente e rejeição de fontes modificadas. O código da
aplicação não foi alterado; a suíte completa anterior tinha 229 testes aprovados.

O pacote auxiliar foi reaberto e teve os 193 arquivos fonte internos conferidos,
além do hash externo. Tamanho: 353976320 bytes. SHA-256:

```text
a56e7f56650c461d752e8df956d1a269d8fb7f647eb029c66cacbcacc76b5ceb
```

O pacote validado preserva a documentação do momento do empacotamento; esta seção
registra verificações posteriores no checkout. O RC2 aprovado mantém seu hash anterior.
