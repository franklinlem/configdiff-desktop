# Política YAML — experimento da fase 0

BaseLoader evita inferência automática de datas e booleanos legados. A conversão
explícita aceita true/false minúsculos, null/~ e vazio como null, inteiros decimais
sem zeros iniciais e sem sinal +, floats com parte decimal e expoente opcional.
Escalares com aspas ficam strings. Datas, yes/no/on/off, 012, 1e3 e 0x10 ficam strings.
Chaves escalares são sempre strings. Não se promete conformidade YAML 1.2 integral.

Rejeita duplicatas, tags explícitas (inclusive padrões), anchors, aliases, merge
keys, chaves complexas, múltiplos documentos e números .nan/.inf. Erros têm mensagem
fixa, sem reproduzir entrada ou exceção original. Limites experimentais: 5 MiB,
200 mil tokens, profundidade 64 e 50 mil nós; o contador da prova inclui a raiz,
mas não as chaves. Os contratos finais serão definidos na fase 1.

O experimento tem testes aceitos/rejeitados e limites; não está conectado à GUI.
JSON e .env ainda não foram implementados. A gramática prevista permanece no plano.
