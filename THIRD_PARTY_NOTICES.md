# Dependências e avisos — candidato local

ConfigDiff usa Qt for Python/PySide6 Essentials e Shiboken6 6.12.0, Qt 6.12.0 e
PyYAML 6.0.3. Python e bibliotecas nativas também acompanham o executável congelado.
Os direitos dessas dependências pertencem a seus autores. O inventário do build
registra versões, arquivos binários, hashes e provedores Debian quando identificados.
Não representa certificação SPDX nem análise automática de conformidade.

| Componente | Informação de licença do fornecedor | Fonte oficial |
|---|---|---|
| PySide6 Essentials / Shiboken6 | LGPL-3.0-only ou alternativas GPL/comercial; há partes com outras licenças | https://code.qt.io/cgit/pyside/pyside-setup.git/?h=v6.12.0 |
| Qt | LGPL-3.0 para módulos elegíveis; condições e terceiros variam por módulo | https://code.qt.io/cgit/qt/ e https://download.qt.io/official_releases/qt/6.12/6.12.0/submodules/ |
| Python | PSF e avisos de componentes incluídos | https://www.python.org/downloads/release/python-3135/ |
| PyYAML | MIT; extensão libyaml tem seus próprios avisos incluídos na distribuição fonte | https://pypi.org/project/PyYAML/6.0.3/ |
| PyInstaller (ferramenta/bootloader) | GPL-2.0-or-later com exceção de distribuição; alguns arquivos Apache-2.0 | https://pyinstaller.org/en/stable/license.html |
| Bibliotecas Debian copiadas | Ver copyright de cada pacote em licenses/debian | https://sources.debian.org/ |

O pacote copia os textos disponíveis nos metadados dos pacotes selecionados, a licença
Python instalada, textos comuns GNU e os arquivos copyright dos provedores Debian
identificados. O texto BSD de Qt for Python em third_party/licenses foi obtido do
tag oficial v6.12.0. Isso ainda não cobre automaticamente todas as atribuições e
fontes dos terceiros incorporados nas bibliotecas Qt/ICU/plugins de seus wheels.

Antes de publicação: conferir cada módulo/plugin e componente incorporado no
inventário, reunir seus avisos específicos, disponibilizar as fontes correspondentes
conforme as licenças aplicáveis e validar o procedimento de substituição/relink das
bibliotecas LGPL. O modo onedir mantém bibliotecas em arquivos separados; isso, sozinho,
não certifica cumprimento de todas as condições. Não impor restrições incompatíveis
à modificação dessas bibliotecas ou depuração das modificações.

O código próprio tem proposta MIT em LICENSE.proposed; a licença final ainda não foi
confirmada. O candidato é preparado para avaliação local e não é publicado pelo script.
Referências oficiais consultadas em 22/10/2026:

- https://doc.qt.io/qtforpython-6/licenses.html
- https://doc.qt.io/qt-6/lgpl.html
- https://pyinstaller.org/en/stable/license.html
