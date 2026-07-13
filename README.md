# REI'SPETOS OS — MVP Publicável

MVP full stack pronto para GitHub, Render e Vercel.

## Incluído
- Login Admin e Caixa
- Dashboard
- Produtos e estoque
- Mesas, comandas e pagamentos
- Produção Bar/Churrasqueira/Cozinha
- Clientes, reservas, despesas e auditoria
- FastAPI + PostgreSQL + React

## Logins
- admin / 1234
- caixa / 0000

## Local
1. Instale e abra o Docker Desktop.
2. Execute `docker compose up --build`.
3. Abra `http://localhost:3000`.

## Render
Backend: raiz `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
Variáveis: `DATABASE_URL`, `SECRET_KEY`, `FRONTEND_URL`.

## Vercel
Raiz `frontend`, framework Vite, build `npm run build`, saída `dist`.
Variável: `VITE_API_URL=https://SEU-BACKEND.onrender.com`.

As integrações reais de iFood e impressoras exigem credenciais/equipamentos externos.

## Versão 1.3 — Mesas e Comandas Individuais

- Mapa com 20 mesas e 4 bistrôs.
- Abertura de mesa pelo painel.
- Várias comandas por mesa, uma para cada cliente.
- Lançamento rápido de produtos por comanda.
- Observação e quantidade por item.
- Cancelamento com devolução automática ao estoque.
- Fechamento individual por Pix, dinheiro, débito, crédito ou vale.
- Fechamento automático da mesa quando a última comanda é paga.
- Compatibilidade com dados da versão 1.1.
