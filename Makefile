PY ?= python
PIP := $(PY) -m pip
PORT ?= 8000

.PHONY: help install dev test lint check demo up down logs deploy-vercel

help: ## Mostra os comandos disponíveis
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | sed 's/:.*## /:/'

install: ## Instala dependências de desenvolvimento
	$(PIP) install -r requirements-dev.txt

dev: ## Sobe a API com recarregamento automático
	$(PY) -m uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)

demo: ## Sobe a API em modo offline (dados sintéticos)
	VTS_DEMO=1 $(PY) -m uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)

test: ## Executa a suíte de testes
	$(PY) -m pytest

lint: ## Verifica estilo com Ruff
	$(PY) -m ruff check .

check: lint test ## Roda lint e testes

up: ## Sobe o Docker Compose em segundo plano
	docker compose up -d --build

down: ## Desliga os containers
	docker compose down

logs: ## Acompanha os logs da API
	docker compose logs -f api

deploy-vercel: ## Publica na Vercel (requer CLI autenticada)
	vercel --prod
