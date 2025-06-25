# Makefile para facilitar comandos Docker

# Variables
DOCKER_IMAGE = mikrotik-ipv6-automation
DOCKER_TAG = latest
CONTAINER_NAME = mikrotik-automation

# Build commands
.PHONY: build
build:
	@echo "🔨 Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

.PHONY: build-no-cache
build-no-cache:
	@echo "🔨 Building Docker image (no cache)..."
	docker build --no-cache -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Run commands
.PHONY: run
run:
	@echo "🚀 Running Mikrotik automation..."
	docker-compose up --build

.PHONY: run-detached
run-detached:
	@echo "🚀 Running Mikrotik automation (detached)..."
	docker-compose up -d --build

.PHONY: run-once
run-once:
	@echo "🚀 Running Mikrotik automation (once)..."
	docker run --rm \
		-v $(PWD)/hosts.txt:/app/hosts.txt:ro \
		-v $(PWD)/device_configs.txt:/app/device_configs.txt:ro \
		-v $(PWD)/.env:/app/.env:ro \
		-v $(PWD)/logs:/app/logs \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

# Development commands
.PHONY: shell
shell:
	@echo "🐚 Opening shell in container..."
	docker run --rm -it \
		-v $(PWD):/app \
		--entrypoint /bin/bash \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

.PHONY: test
test:
	@echo "🧪 Running tests in container..."
	docker run --rm \
		-v $(PWD):/app \
		$(DOCKER_IMAGE):$(DOCKER_TAG) \
		python -m pytest tests/ -v

# Cleanup commands
.PHONY: stop
stop:
	@echo "🛑 Stopping containers..."
	docker-compose down

.PHONY: clean
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) 2>/dev/null || true
	docker system prune -f

.PHONY: logs
logs:
	@echo "📋 Showing logs..."
	docker-compose logs -f

# Setup commands
.PHONY: setup
setup:
	@echo "⚙️  Setting up environment..."
	cp .env.example .env || echo "Please create .env file"
	cp hosts.txt.example hosts.txt || echo "Please create hosts.txt file"
	mkdir -p logs

.PHONY: help
help:
	@echo "🆘 Available commands:"
	@echo "  build          - Build Docker image"
	@echo "  build-no-cache - Build Docker image without cache"
	@echo "  run            - Run with docker-compose"
	@echo "  run-detached   - Run detached with docker-compose"
	@echo "  run-once       - Run once with docker run"
	@echo "  shell          - Open shell in container"
	@echo "  test           - Run tests"
	@echo "  stop           - Stop containers"
	@echo "  clean          - Clean up containers and images"
	@echo "  logs           - Show logs"
	@echo "  setup          - Setup environment files"
	@echo "  help           - Show this help" 