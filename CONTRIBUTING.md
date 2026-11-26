# Como contribuir

Obrigado por querer melhorar o VariantScope! Este projeto lida com informações de saúde,
então mudanças devem ser cuidadosas e rastreáveis.

## Começando

```bash
git clone https://github.com/JNeves07/VariantScope.git
cd VariantScope
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
make install
make test
```

## Antes de abrir um pull request

1. `make check` — Ruff e pytest precisam passar.
2. Se mexeu no front-end, rode `node --check frontend/app.js`.
3. Se adicionou uma fonte de dados, inclua fixtures em `tests/` e documente o schema da API.
4. Nunca faça logging da consulta do usuário (rsID, gene, condição) nem gravando em claro no cache.
5. Atualize o README quando mudar comportamento visível ou variáveis de ambiente.

## Convenções

- Backend em `app/`, com rotas finas em `app/routers/` e regras de negócio nos módulos de domínio.
- Front-end estático em `frontend/` (HTML/CSS/JS sem framework).
- Mensagens de erro voltadas ao usuário devem ser claras e em inglês na API; a interface faz a tradução.
- Aviso legal é obrigatório em qualquer resposta de brief.

## Reportando problemas

Abra uma issue com: consulta usada (sem dados pessoais), resposta esperada, resposta obtida,
modo (`VTS_DEMO` ligado ou não), versão e plataforma. Anexe o JSON de `/api/health` se possível.
