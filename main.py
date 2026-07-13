# REI'SPETOS OS v1.7 — Produção em Tempo Real

## Novidades
- cronômetro em tempo real por pedido;
- alerta visual quando o preparo passa de 15 minutos;
- filtros por Bar, Churrasqueira, Cozinha e Fritadeira;
- fila de impressão por setor;
- impressão de todos os pedidos pendentes do setor;
- reimpressão individual;
- registro de quais pedidos já foram enviados à impressão;
- painel de status Aguardando → Em preparo → Pronto → Entregue.

## Limitação importante
Navegadores exigem confirmação na caixa de impressão. Impressão silenciosa automática depende de um conector local para a impressora e será configurada numa etapa específica.

## Arquivos deste patch
- backend/app/models.py
- backend/app/main.py
- frontend/src/main.jsx
- frontend/src/styles.css

Não envie package.json, package-lock.json, Dockerfile ou arquivos fora desses caminhos.
