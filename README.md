# ImoDashboard

Dashboard simples em Flask que agrega anúncios de arrendamento T2 em Portugal continental, calcula €/m² e permite ordenar/filtrar os resultados.

## Fontes suportadas
- Idealista (`idealista`)
- Imovirtual (`imovirtual`)
- SUPERCASA (`supercasa`)
- CASA SAPO (`casasapo`)
- RE/MAX (`remax`)
- OLX (`olx`)

## Como correr
1. Criar virtualenv e instalar dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Correr a app:
   ```bash
   python app.py
   ```
   - Variáveis opcionais: `HOST` e `PORT` (por omissão `127.0.0.1:5000`).

3. Abrir no browser: http://127.0.0.1:5000/

## Utilização
- Escolhe o distrito, número de páginas por fonte e as fontes (checkboxes).
- Define filtros de preço/área e a ordenação desejada.
- Clica em "Atualizar" para carregar os dados.
- Resumo e gráficos rápidos ajudam a perceber a distribuição por fonte e a mediana atual de €/m².

## Notas técnicas
- Scrapers implementados em `scrapers/` com uma base comum (`BaseScraper`).
- O serviço agregador em `services/aggregator.py` faz cache leve (10 min), deduplica por URL e ordena/aplica filtros.
- O frontend usa Bootstrap e Chart.js; cabeçalho da tabela "sticky" e badges coloridas por fonte.
- Respeito por "polite sleep" entre páginas para reduzir carga nos sites.
