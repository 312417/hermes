---
name: curated-news
description: "Curadoria de notícias especializadas em 9 frentes (Gospel BR/Intl, Igreja Perseguida, Futebol BR/Intl, Mercado Financeiro BR/Intl, Tecnologia e IA)"
version: 1.0.0
author: user
tags: [News, RSS, Curated, Gospel, Missões, Futebol, Economia, Tecnologia]
---

# Curated News Skill

Esta skill permite coletar notícias atualizadas das fontes mais confiáveis mapeadas em 9 categorias.

## Categorias disponíveis no `feeds.json`:
- `gospel_br`: Notícias do mundo cristão e evangélico brasileiro (Gospel Prime, Guiame, Gospel Mais, CPAD).
- `missoes_perseguida`: Relatórios e notícias de missões e da igreja perseguida no mundo (Portas Abertas, ICC, Voice of the Martyrs).
- `gospel_intl`: Notícias do cristianismo internacional (Christianity Today, Christian Post).
- `futebol_br`: Futebol nacional (GE Globo, UOL Esporte).
- `futebol_intl`: Futebol internacional (BBC Sport).
- `tecnologia`: Notícias de tecnologia (TechCrunch, The Verge, Ars Technica).
- `ia`: Notícias oficiais de inteligência artificial (OpenAI, Anthropic).
- `mercado_financeiro_br`: Economia e finanças brasileiras (InfoMoney, Valor Econômico).
- `mercado_financeiro_intl`: Mercados e finanças globais (Reuters).

## Como executar:
Execute o script em Python passando o nome da categoria desejada:

```bash
python3 /root/.hermes/skills/curated-news/fetch_news.py <categoria>
```

Exemplos:
- `python3 /root/.hermes/skills/curated-news/fetch_news.py gospel_br`
- `python3 /root/.hermes/skills/curated-news/fetch_news.py missoes_perseguida`
- `python3 /root/.hermes/skills/curated-news/fetch_news.py tecnologia`

## Diretrizes de Resposta para o Telegram:
- Apresente um resumo em tópicos (bullet points) claros e objetivos.
- Inclua o nome do veículo entre colchetes (ex: `[Portas Abertas]`).
- Se a notícia original for em inglês (como em `missoes_perseguida`), traduza o resumo para o português brasileiro.
- Coloque o link original da matéria para quem quiser ler na íntegra.
