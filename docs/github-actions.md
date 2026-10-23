# Validação pelo GitHub Actions

Em 22/10/2026, Franklin autorizou criar o repositório privado, enviar o histórico
local e executar o Actions. Remoto: https://github.com/franklinlem/configdiff-desktop.
A visibilidade PRIVATE foi conferida via API após a criação. O relatório local
não versionado não foi enviado. Nenhuma release pública foi criada.

## Pipeline

O workflow `.github/workflows/phase0.yml` executa em push, pull request ou acionamento
manual. A matriz usa Ubuntu 24.04 e windows-latest, Python 3.13.5, Qt offscreen e
UTF-8 explícito. Cada plataforma roda lint, formatação, mypy, pytest, download de
fontes com hashes, PyInstaller, smoke do executável e upload dos candidatos.
Falhas de uma plataforma não cancelam a outra; cada job tem limite de 25 minutos.
Os candidatos ficam nos artefatos candidate-Linux e candidate-Windows na página
da execução. Exigem acesso ao repositório privado e estão sujeitos à retenção do
GitHub; não substituem uma release permanente.

## Correções encontradas no primeiro uso remoto

- Ubuntu: instalar libegl1, libgl1 e configuração/fontes antes dos testes Qt.
- Windows: delimitar explicitamente o bloco POSIX de máscaras de sinais, para
  conferir os tipos de cada plataforma.
- Windows: espera limitada por dados no pipe e evento de parada para encerrar o
  leitor quando o processo é interrompido durante spawn; detectar saída anormal
  do processo sem esperar que o prazo expire. Os testes existentes de cancelamento,
  timeout e crash expuseram o problema. Regressão local: 232 testes passaram em
  29,82 s; lint, formatação e mypy passaram.

Referência da API de pipe: [documentação Python 3.13](https://docs.python.org/3.13/library/multiprocessing.html#connection-objects).
O recv permanece na thread para não bloquear a interface durante mensagens grandes.

## Execução validada

[Execução 39871502594](https://github.com/franklinlem/configdiff-desktop/actions/runs/39871502594),
commit `7b0c46e`, concluída com sucesso em ambas as plataformas em 22/10/2026.

| Runner | Testes | Build e smoke | Artefato |
| --- | --- | --- | --- |
| Ubuntu 24.04 | 232 passaram em 10,14 s | passaram | candidate-Linux (12466467285) |
| Windows | 225 passaram, 7 POSIX ignorados, em 11,26 s | passaram | candidate-Windows (12467165939) |

Lint, formatação e mypy também passaram nos dois runners. O candidato Windows é
`configdiff-0.1.0rc2-windows-AMD64.zip`; o Linux é
`configdiff-0.1.0rc2-linux-x86_64.tar.gz`. Os uploads incluem checksums e o arquivo
adjacente com fontes upstream. Não foi criada release pública.

## Aceite manual posterior

Franklin executou o ZIP extraído em uma VM QEMU/KVM com Windows 11 Enterprise e
confirmou o funcionamento. A comparação JSON está visível na captura fornecida.
Registro e limites do aceite em [acceptance.md](acceptance.md#aceite-manual--windows-11-enterprise-em-vm).

## Limites

A execução automatizada sem tela não representa aceite visual, leitor de tela ou
instalação em uma máquina Windows de usuário. Os testes POSIX não se aplicam ao
Windows. O lock transitivo Windows ainda precisa ser preparado. A auditoria Debian
em provenance-audit.md é específica do pacote local anterior; não certifica os novos
binários Ubuntu/Windows. Pacotes com o mesmo número de versão devem ser identificados
pela execução, commit e checksums. Os artefatos locais já aceitos foram preservados.
