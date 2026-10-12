[English](README.md) · [简体中文](README_zh.md) · [日本語](README_ja.md) · [Español](README_es.md) · [Français](README_fr.md) · [Deutsch](README_de.md) · [Português (Brasil)](README_pt-BR.md)

# SRE — Software Resynthesis Engine

[![Tests](https://github.com/lovejzzz/SRE/actions/workflows/test.yml/badge.svg)](https://github.com/lovejzzz/SRE/actions/workflows/test.yml)

**Diga qual software deseja reconstruir, em qual plataforma e o que deve melhorar.**

SRE é uma skill para agentes que pesquisam software existente e criam um sucessor: preservar comportamentos, adaptar a outra plataforma e adicionar ou aprimorar funções. A proposta abrange jogos, aplicativos de desktop, ferramentas CLI, web e dispositivos móveis. A viabilidade depende das evidências acessíveis, das dependências e da plataforma de destino.

**v0.2: uma skill com ferramentas executáveis de pesquisa e validação.** O agente hospedeiro pesquisa e programa. Não há garantia de reconstrução completa de qualquer software com um clique.

## Instalação

É necessário um hospedeiro com suporte a skills locais e **Python 3.10+**, sem dependências Python de terceiros. REA é opcional e não é instalado automaticamente.

```bash
git clone https://github.com/lovejzzz/SRE.git
python3 SRE/scripts/install.py
```

O instalador usa `$CODEX_HOME/skills` ou `~/.codex/skills` e recusa sobrescrever uma instalação existente. Use `--skills-dir /path/to/skills` para outro diretório. Preserve alterações locais ao atualizar e recarregue a skill no hospedeiro.

> Use $software-resynthesis para pesquisar este aplicativo de desktop e reconstruí-lo como aplicativo web offline. Preserve o fluxo de documentos, adicione operações em lote e valide contra o original. Entregue um primeiro marco testado sem perder o escopo completo solicitado.

## Capacidades implementadas

- Inventários de funções a partir de várias fontes, mapeamentos, dependências, detecção de omissões e referências versionadas.
- Hipóteses concorrentes, previsões, priorização de experimentos que distinguem hipóteses e detecção de contradições.
- Execução explícita de adaptadores com diretório próprio, contrato de reinicialização/ação/observação/finalização, hashes, logs e limite de tempo.
- Erros de imagens normalizadas, preservação semântica ao salvar e reabrir arquivos, rastros de interação e orçamentos de desempenho por dispositivo e carga.
- Aceitação que exige evidências de comportamento e auditoria da pesquisa. Registros desatualizados e questões bloqueantes impedem a aprovação.

REA pode fornecer análise; SRE conecta a pesquisa às especificações, à implementação e à aceitação. Não inclui um cliente REA nem afirma superioridade medida em relação ao REA.

## Exemplo executável

```bash
cd SRE
python3 -m unittest discover -s tests -v
python3 examples/posix-path/run.py --workspace work/posix-run-1
```

O exemplo executa de fato `posixpath.normpath` do Python e uma implementação JavaScript independente com **417 entradas**. Resolve uma pergunta por observações e detecta um defeito intencional. Exige Node.js 18+ e um diretório de saída novo. Não é uma avaliação independente de reconstrução autônoma de aplicativos completos.

## Comandos e limites

`sre.py`: `init`, `fingerprint`, `seal`, `audit`, `plan`, `run-adapter`, `compare`, `domain-check`, `check`. Consulte `--help`. As saídas não são sobrescritas. Códigos: 0 sucesso, 1 comparação/aceitação/execução reprovada, 2 erro de entrada ou execução. Espaços v0.1 precisam de registros reais de descoberta e uma referência fixada para passar em `check`.

SRE não prova que todas as funções foram descobertas nem autentica experimentos. Um marco não significa o produto completo. Não há rastreador universal, agendador permanente ou adaptadores de execução para PZ/Photoshop. O agente coleta fontes e cria hipóteses. Adaptadores usam as permissões do hospedeiro e não são uma sandbox. Validadores recebem JSON normalizado; análise PSD, decodificação de imagens, operação de GUI e medição de dispositivos exigem adaptadores específicos. Implementações inacessíveis de servidor não podem ser recuperadas, e qualquer carga não é garantida em qualquer plataforma.

Avaliações independentes de agentes ainda não foram realizadas. Mantenha amostras privadas, credenciais e dados pessoais fora do repositório público; respeite as licenças do código reutilizado.

[Pesquisa](skills/software-resynthesis/references/research-protocol.md) · [Adaptadores](skills/software-resynthesis/references/adapters.md) · [Validação por domínio](skills/software-resynthesis/references/domain-validation.md) · [Avaliação](evals/behavioral.md)

Contribuições com falhas reproduzíveis e dados sensíveis removidos, incluindo versões, entradas, comportamento esperado/real e evidências, além de melhorias de tradução, são bem-vindas. Os protocolos técnicos detalhados estão atualmente em inglês.
