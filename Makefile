help:
	@echo
	@echo "install                            -- install backend dependencies"
	@echo "lint                               -- lint backend"
	@echo "format                             -- format backend"
	@echo "mypy                               -- type check backend"
	@echo "mcp                                -- start mcp server"
	@echo "inspect                            -- start mcp inspector"


.PHONY: install
install:
	uv sync --frozen

.PHONY: lint
lint:
	uv run ruff check .

.PHONY: mypy
mypy:
	uv run mypy .

.PHONY: format
format:
	uv run ruff check --fix .
	uv run ruff format .

.PHONY: mcp
mcp:
	uvicorn main:app --reload --host localhost --port 8001 --log-level info

.PHONY: inspect
inspect:
	npx @modelcontextprotocol/inspector --transport http --url http://localhost:8001/mcp

