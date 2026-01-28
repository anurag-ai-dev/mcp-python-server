help:
	@echo
	@echo "install                            -- install backend dependencies"
	@echo "lint                               -- lint backend"
	@echo "format                             -- format backend"
	@echo "mypy                               -- type check backend"
	@echo "dev                                -- start mcp server"
	@echo "inspector                          -- start mcp inspector"


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
	uv run python main.py

.PHONY: inspector
inspector:
	npx @modelcontextprotocol/inspector \
		uv \
		--directory . \
		run main.py \
		args...