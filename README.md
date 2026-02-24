# ImoDashboard

Dashboard simples em Flask que agrega anúncios de imobiliário (arrendamento e venda) em Portugal continental, calcula €/m² e permite ordenar/filtrar os resultados.

## Funcionalidades
- **Agregação Multi-fonte**: Procura em vários portais imobiliários em simultâneo.
- **Arrendar ou Comprar**: Suporte para pesquisa de imóveis para arrendamento ou venda.
- **RAG & Contexto**: Integração com modelo RAG (mcp) para entender o contexto das regras de scraping definidas em YAML.
- **Filtros Avançados**: Filtra por preço, área, tipologia e €/m².
- **Favoritos e Rejeitados**: Marca anúncios como "gosto" ou "ignorar" para futuro sistema de recomendação.
- **Gráficos e Estatísticas**: Visualização rápida da distribuição de preços e áreas.

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
- Escolhe o distrito, tipo de negócio (Arrendar/Comprar), tipologia, número de páginas por fonte e as fontes (checkboxes).
- Define filtros de preço/área e a ordenação desejada.
- Clica em "Atualizar" para carregar os dados.
- Resumo e gráficos rápidos ajudam a perceber a distribuição por fonte e a mediana atual de €/m².
- Usa os ícones de coração ou lixo para treinar o teu futuro sistema de recomendação pessoal.

## Notas técnicas
- Scrapers implementados em `scrapers/` com uma base comum (`BaseScraper`).
- O serviço agregador em `services/aggregator.py` faz cache leve (10 min), deduplica por URL e ordena/aplica filtros.
- O frontend usa Bootstrap e Chart.js; JavaScript modularizado em `static/js/`.
- Respeito por "polite sleep" entre páginas para reduzir carga nos sites.

## Estrutura do Projeto
- `app.py`: Servidor Flask e API.
- `scrapers/`: Lógica de extração de dados para cada site.
- `services/aggregator.py`: Orquestração de scrapers e processamento de dados.
- `templates/` & `static/`: Interface de utilizador.
- `marks.json`: Persistência local das tuas preferências.

## Estrutura de templates e assets (refactor)
- A página principal é `templates/dashboard.html` que estende `templates/_layout.html`.
- Componentes Jinja em `templates/parts/`:
  - `_controls.html`, `_sources.html`, `_filters.html`, `_charts.html`, `_table_controls.html`, `_table.html`.
- CSS personalizado em `static/css/app.css`.
- JavaScript foi modularizado (ES Modules) sob `static/js/`:
  - `apiClient.js` (Facade), `eventBus.js` (Observer), `marksRepository.js` (Repository), `utils/format.js`, renderizadores em `render/` (`table.js`, `charts.js`, `summary.js`) e `main.js` (bootstrap).

