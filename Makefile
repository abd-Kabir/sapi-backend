# Variables
COMPOSE=docker-compose

# Targets
.PHONY: build up down restart migrate collectstatic logs prune

# Rebuild the project
build:
	$(COMPOSE) build

# Start the services
up:
	$(COMPOSE) up -d

# Stop the services
down:
	$(COMPOSE) down

# Restart the services
restart: down build up

# View logs
logs:
	$(COMPOSE) logs -f

# Clean up unused Docker resources
prune:
	docker system prune -f