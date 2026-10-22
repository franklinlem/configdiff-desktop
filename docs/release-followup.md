# Continuidade após o aceite do pacote

Em 22/10/2026 Franklin informou que copiou/extraiu o RC1 em
/home/franklin/Documentos/ConfigDiff/, iniciou pelo Konsole e que tudo funcionou.
A cópia foi conferida somente para leitura: 419 hashes internos válidos. Não foi
substituída nem alterada. Isso acrescenta aceite manual do executável extraído ao
aceite anterior da interface executada pela .venv.

Na mesma etapa, Franklin confirmou explicitamente MIT para o código próprio.
LICENSE.proposed foi substituída por LICENSE efetiva, com metadados SPDX MIT no projeto.
As licenças de dependências e dos textos em third_party continuam sendo as dos autores.

## Fontes e atribuições preparadas no RC2

Foram obtidos arquivos oficiais de Qt Base, Qt Wayland, Qt SVG, Qt Image Formats e
PySide/Shiboken 6.12.0, ICU4C 73.2, PyYAML 6.0.3 e LibYAML 0.2.5. ICU 73.2 e LibYAML
0.2.5 foram também confirmados via APIs das bibliotecas instaladas no ambiente de build.
O manifesto third_party/upstream-sources.json registra URLs, versões e hashes.

Qt/PySide foram conferidos com os SHA-256 publicados pela Qt. ICU foi conferido com
SHA-512 do release oficial e teve SHA-256 fixado localmente. PyYAML usa hash do PyPI.
LibYAML veio do HTTPS oficial; seu hash foi fixado após a obtenção, sem alegar comparação
com um checksum separado do fornecedor. Os próximos downloads exigem o hash fixado.

O coletor reúne 99 registros qt_attribution.json e 245 arquivos de metadados, avisos e
licenças. Todas as referências LicenseFile desses registros foram encontradas nos
arquivos fonte. Alguns metadados upstream contêm novas linhas literais em strings;
somente o coletor de manutenção tolera isso. O parser JSON da aplicação continua restrito.

O conjunto é conservador: inclui registros de exemplos, testes e ferramentas upstream
que não necessariamente estão nos binários. Não implica que todas essas partes estejam
em uso ou que suas licenças se apliquem ao código próprio. O índice preserva QtParts,
QtUsage e a origem de cada registro para a revisão do artefato efetivamente distribuído.

O candidato leva os avisos, índice e manifesto. As oito fontes completas são fornecidas
no arquivo adjacente configdiff-0.1.0rc2-upstream-sources.tar, separado do aplicativo.
Os arquivos originais comprimidos e o manifesto estão dentro desse tar, sem recompilação
ou modificação. Ambos os artefatos possuem SHA-256 ao lado.

## Reproduzir

```sh
.venv/bin/python scripts/fetch_upstream_sources.py
.venv/bin/python scripts/collect_upstream_notices.py
```

A coleta não executa fontes nem extrai arquivos executáveis; copia somente arquivos
regulares selecionados e rejeita caminhos absolutos ou contendo segmentos .. .
Para um novo build, os textos/índice gerados e o manifesto precisam estar versionados.
O script de build exige a presença das fontes locais com os hashes esperados.

## Substituição de bibliotecas

O pacote onedir não impõe verificação de assinatura para impedir substituição das
bibliotecas compartilhadas. Para experimentar uma biblioteca Qt/PySide modificada,
reconstrua a mesma versão/ABI a partir das fontes e preserve nomes, dependências e
symlinks em _internal/PySide6/Qt/lib (e bindings/Shiboken quando necessário). O manifesto
de integridade acusará a mudança; o aplicativo não o usa como bloqueio de execução.
Alternativamente, reconstrua todo o aplicativo a partir do snapshot e scripts incluídos.
Não foi executada compilação de Qt/PySide modificados nesta etapa.

## Verificação do incremento

Ruff lint/formatação e mypy passaram; 229 testes passaram em 29,32 s. Os novos testes
rejeitam caminhos de atribuição que escapem do diretório e garantem que download com
hash divergente não seja publicado nem deixe arquivo .part. A suíte da aplicação
permanece com parsers restritivos, privacidade e encerramento preservados.

## Atualização da proveniência

O aceite do RC2 e a auditoria posterior estão em [provenance-audit.md](provenance-audit.md).
Ela verificou a identidade dos 179 binários de dependências e reuniu 193 arquivos
fonte das versões exatas de 57 pacotes Debian. Os dados abaixo preservam o registro
anterior à auditoria.

## Pendências registradas no preparo do RC2

- Conferência da configuração/patches exatos dos wheels Qt e sua correspondência com
  as fontes upstream coletadas; disponibilidade das fontes dos provedores Debian e
  condições aplicáveis ao conjunto realmente distribuído.
- Teste nativo Windows e lock transitivo; Ubuntu e acessibilidade detalhada continuam
  sem aceite específico. O aceite desktop desta etapa corresponde ao RC1 no Debian.
- Publicação de repositório/release não foi solicitada nem executada. Não houve push.

O RC2 é um candidato local com licença e atribuições mais completas, não uma declaração
automática de conformidade jurídica ou de suporte às plataformas ainda não testadas.


## Evidências finais do RC2

- Pacote extraído: licença MIT efetiva presente; LICENSE.proposed ausente.
- 668 arquivos regulares conferidos no manifesto interno.
- Smoke offline no Debian sem Python e smoke Wayland passaram a partir da cópia extraída.
- Índice embarcado confirma 99 registros, 245 arquivos e nenhuma referência LicenseFile pendente.
- Arquivo separado de fontes: oito conteúdos conferidos contra o manifesto, além do hash externo.
- Relatório local não versionado continua fora do snapshot de fontes do aplicativo.

Artefato Linux: dist/configdiff-0.1.0rc2-linux-x86_64.tar.gz (63452386 bytes).
SHA-256: 575dc22c2a62898b7dd985647bf6d9c7446f8411f44c5733208c2d166d1c930f.
Fontes: dist/configdiff-0.1.0rc2-upstream-sources.tar, com .tar.sha256 ao lado.
Esta seção registra verificações posteriores ao build; o candidato validado foi preservado.


## Atualização: repositório privado e CI

A publicação privada e o Actions foram autorizados em 22/10/2026. O histórico foi
enviado para franklinlem/configdiff-desktop. Windows e Ubuntu passaram em testes,
build e smoke; evidências e limites em [github-actions.md](github-actions.md).
Esta atualização substitui a pendência histórica de ausência de push e de testes
automatizados Windows/Ubuntu acima; o aceite visual Windows continua pendente.
