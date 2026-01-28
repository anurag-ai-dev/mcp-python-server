help:
	@echo
	@echo "install                            -- install backend dependencies"
	@echo "lint                               -- lint backend"
	@echo "format                             -- format backend"
	@echo "mypy                               -- type check backend"
	@echo "dev                                -- start mcp server"


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

.PHONY: dev
dev:
	fastmcp run main.py --reload --transport http --port 8001 --log-level INFO

.PHONY: inspector
inspector:
	npx @modelcontextprotocol/inspector --transport http --url http://localhost:8001/mcp
