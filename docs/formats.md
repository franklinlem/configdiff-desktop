# Formatos suportados — fase 2

Entrada pública: `configdiff.parsers.parse_bytes(data, format, limits)` retorna uma
árvore canônica. Somente UTF-8 com BOM opcional. O limite de 5 MiB inclui o BOM.
A detecção por nome aceita .json, .yaml/.yml, .env, .env.* e *.env, sem distinguir
maiúsculas/minúsculas. Outros nomes exigem formato explícito; não se adivinha pelo
conteúdo nem se expande o caminho selecionado.

## JSON

Objetos, listas e raiz escalar. Rejeita duplicatas (inclusive chaves equivalentes
com escapes), NaN, Infinity, overflow não finito e sintaxe inválida. Ordem de objetos
não importa; strings mantêm Unicode e espaços, sem normalização. bool/int/float são
tipos distintos. Usa json da biblioteca padrão, com hooks restritivos e uma passagem
lexical de limites antes do decoder construir a árvore. Strings são reconhecidas
pelo próprio decoder JSON; colchetes dentro de strings não alteram a profundidade.

## YAML

Um documento, mapas com chaves escalares interpretadas como strings, sequências e
escalares. Sem conformidade completa com YAML 1.2. A política numérica é explícita:

| Sem aspas | Resultado |
|---|---|
| true / false | boolean |
| null / ~ / valor vazio | null |
| 0, 12, -12 | integer decimal |
| 1.5, -1.5e+2 | float finito |
| yes, no, on, off, TRUE, FALSE | string |
| 2026-10-22, 012, +12, 0x10, 1e3 | string |

Escalares entre aspas ou blocos `|`/`>` permanecem strings. Chaves escalares sempre
são strings: `true:` e `"true":` são duplicatas. Rejeita duplicatas, anchors, aliases,
merge key `<<`, chaves complexas, tags explícitas (inclusive tags padrão), múltiplos
documentos e .nan/.inf. Blocos de texto YAML podem conter novas linhas; a restrição
a uma linha aplica-se somente ao .env.

O parser faz scan limitado de tokens e interpreta eventos BaseLoader diretamente.
Não executa construtores de tags, não usa yaml.load e não compõe uma árvore YAML
intermediária. Conta nós e profundidade antes de construir cada nó canônico.
A antiga prova em prototypes/ é histórica e não é importada pela aplicação.

## .env

Formato restrito, sem alegar compatibilidade com todas as variantes dotenv:

- Linhas LF/CRLF; comentários de linha começam por `#` após espaços opcionais.
- Chaves seguem `[A-Za-z_][A-Za-z0-9_]*`; prefixo `export` seguido de espaço/tab é opcional.
- Espaços/tabs em torno da chave, do `=` e de valores sem aspas são removidos.
- Valor vazio é string vazia. Todos os valores permanecem strings, inclusive false/1.
- Comentário após valor sem aspas só começa com espaço/tab seguido de `#`.
- Aspas simples preservam o conteúdo literalmente. Aspas duplas aceitam somente
  `\"` e `\\`. Após fechar aspas, aceita espaços e comentário separado por espaço/tab.
- Não aceita duplicatas, multilinhas, continuação por barra final, aspas avulsas em
  valor sem aspas, controles ou escapes desconhecidos dentro de aspas duplas.
- `$VAR`, `${VAR}`, `~` e `$(command)` são texto literal. Não há source, expansão ou shell.

Aceitos:

```dotenv
export APP_ENV=development
EMPTY=
HASH=literal#hash
COMMENT=value # comentário
LITERAL='${HOME}'
QUOTED="aspas: \" e barra: \\"
```

Rejeitados:

```dotenv
DUP=1
DUP=2
1INVALID=value
UNKNOWN_ESCAPE="linha\n"
TRAILING="value"suffix
```

## Limites e erros

5 MiB, profundidade 64, 50 mil nós; JSON/YAML limitam também 200 mil tokens. Raiz tem
profundidade 0 e conta um nó. Cada entrada/elemento adiciona um nó; chaves não contam
separadamente. Estourar tokens retorna o código de limite estrutural NODE_LIMIT.
São limites cumulativos: o primeiro excedido interrompe o parsing. Inteiros também
estão sujeitos ao limite de conversão decimal do Python, com falha sanitizada.

O processo isolado aplica o orçamento de 10 segundos ao carregamento completo,
incluindo startup e IPC. Erros públicos mostram código, lado e posição quando
conhecida, sem reproduzir mensagens brutas ou conteúdo. Nem toda falha tem posição.
Funções de parsing isoladas não têm timeout próprio; usar LoadJob na aplicação.
