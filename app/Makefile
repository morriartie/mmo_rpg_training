# Makefile for game_api

.PHONY: run build test clean migrate populate populate-docker

# Variables
DOCKER_COMPOSE = docker-compose
APP_SERVICE = api

# Run the application using Docker Compose
run:
	$(DOCKER_COMPOSE) up --build

# Build Docker images
build:
	$(DOCKER_COMPOSE) build

# Run tests (placeholder - add your test commands)
test:
	echo "Running tests..."
	# Add your test commands here

# Clean Docker containers and volumes
clean:
	$(DOCKER_COMPOSE) down -v
	docker system prune -f

# Apply database migrations
migrate:
	$(DOCKER_COMPOSE) run $(APP_SERVICE) python -c "from database import init_databases; init_databases()"

# Access application logs
logs:
	$(DOCKER_COMPOSE) logs -f $(APP_SERVICE)

# Run a shell in the application container
shell:
	$(DOCKER_COMPOSE) run $(APP_SERVICE) sh

# Format code using black
format:
	$(DOCKER_COMPOSE) run $(APP_SERVICE) black .

# Lint code using flake8
lint:
	$(DOCKER_COMPOSE) run $(APP_SERVICE) flake8 .

# Populate database locally
populate:
	python populate_db.py

# Populate database in Docker
populate-docker:
	$(DOCKER_COMPOSE) run $(APP_SERVICE) python populate_db.py

# Run with populate
run-populated: build populate-docker
	$(DOCKER_COMPOSE) up
