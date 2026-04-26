# =============================================================================
# NetworkMemories — Demon's Souls Server — Makefile
# =============================================================================

DC = docker compose -f docker-compose.yml

.PHONY: help init build run run-daemon stop down logs backup restore \
        disable-systemd-resolved enable-systemd-resolved shell-server

help: ## Show all available commands
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS=":.*##"}; {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'

init: ## First-time setup
	@if [ ! -f .env ]; then cp .env.example .env; \
	  echo "✅ .env created — edit it before continuing!"; \
	else echo "⚠️  .env already exists, skipping."; fi
	@mkdir -p db backups
	@echo "✅ Init done. Edit .env then run: make build"

build: ## Build all containers
	$(DC) build

run: ## Start all services (foreground)
	$(DC) up

run-daemon: ## Start all services (background)
	$(DC) up -d

stop: ## Stop services (keep data)
	$(DC) stop

down: ## Remove containers (keep volumes)
	$(DC) down

down-volumes: ## ⚠️  Remove containers AND volumes (data loss!)
	$(DC) down -v

logs: ## Follow all logs
	$(DC) logs -f

logs-server: ## Follow DeSSE server logs only
	$(DC) logs -f desse-server

logs-dns: ## Follow DNS logs only
	$(DC) logs -f desse-dns

logs-admin: ## Follow admin panel logs only
	$(DC) logs -f desse-admin

shell-server: ## Open a shell in the server container
	$(DC) exec desse-server /bin/sh

backup: ## Backup DB data
	@bash scripts/backup.sh

restore: ## Restore from latest backup
	@bash scripts/restore.sh

disable-systemd-resolved: ## Free port 53 (Linux)
	sudo systemctl stop systemd-resolved && sudo systemctl disable systemd-resolved
	@echo "✅ systemd-resolved disabled"

enable-systemd-resolved: ## Re-enable systemd-resolved after shutdown
	sudo systemctl enable systemd-resolved && sudo systemctl start systemd-resolved
	@echo "✅ systemd-resolved re-enabled"
