PNPM ?= corepack pnpm
PYTHON ?= python
POETRY ?= $(PYTHON) tools/poetryw.py

.PHONY: install install-root frontend-install mobile-install backend-install hooks-install lint test coverage format dupcheck docs-dev docs-build webui-up webui-down dive apifox-export

install: install-root frontend-install mobile-install backend-install hooks-install

install-root:
	npm install --workspaces=false --ignore-scripts

frontend-install:
	$(PNPM) --dir RagFrontend install --no-frozen-lockfile

mobile-install:
	$(PNPM) --dir RagMobile install --no-frozen-lockfile

backend-install:
	$(POETRY) --directory RagBackend install --with dev

hooks-install:
	$(PYTHON) tools/install_local_hooks.py

lint:
	$(PNPM) --dir RagFrontend lint
	$(PNPM) --dir RagFrontend typecheck
	$(PNPM) --dir RagMobile lint
	$(POETRY) --directory RagBackend run ruff check trace_logging.py audit exception tests/test_tooling_smoke.py
	$(POETRY) --directory RagBackend run black --check trace_logging.py audit exception tests/test_tooling_smoke.py
	$(POETRY) --directory RagBackend run mypy trace_logging.py audit exception tests/test_tooling_smoke.py


test:
	$(PNPM) --dir RagFrontend test -- --run
	$(POETRY) --directory RagBackend run pytest tests/test_tooling_smoke.py

coverage:
	$(PNPM) --dir RagFrontend test:coverage
	$(POETRY) --directory RagBackend run pytest tests/test_tooling_smoke.py --cov=trace_logging --cov=audit --cov=exception --cov-report=term-missing

format:
	npm run format

dupcheck:
	npm run dupcheck

docs-dev:
	npm run docs:dev

docs-build:
	npm run docs:build

apifox-export:
	npm run apifox:export

webui-up:
	docker compose -f docker-compose.tools.yml up -d open-webui

webui-down:
	docker compose -f docker-compose.tools.yml down

dive:
	docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock wagoodman/dive:latest $(IMAGE)

