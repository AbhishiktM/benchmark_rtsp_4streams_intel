.PHONY: setup start stop clean logs monitor

# One-command setup for new systems
setup:
	@echo "Setting up Universal DLStreamer Pipeline..."
	docker network create dlstreamer_shared_net || true
	docker compose -f docker-compose.streams.yml up -d
	sleep 10
	docker compose -f docker-compose.dlstreamer.yml --profile auto up -d
	@echo "✅ Setup complete! Monitor with: make monitor"

# Start services
start:
	docker compose -f docker-compose.streams.yml up -d
	docker compose -f docker-compose.dlstreamer.yml --profile auto up -d

# Stop services  
stop:
	docker compose -f docker-compose.dlstreamer.yml down
	docker compose -f docker-compose.streams.yml down

# Clean everything
clean:
	docker compose -f docker-compose.dlstreamer.yml down -v
	docker compose -f docker-compose.streams.yml down -v
	docker network rm dlstreamer_shared_net || true
	docker system prune -f

# View logs
logs:
	docker logs -f benchmark_monitor

# Monitor performance
monitor:
	@echo "🔍 System Detection:"
	@docker logs dlstreamer_auto 2>/dev/null | grep -E "(detected|Selected)" || echo "Container not running"
	@echo "\n📊 Current Performance:"
	@docker logs benchmark_monitor 2>/dev/null | tail -10 || echo "No benchmark data yet"

# Check status
status:
	@echo "📋 Service Status:"
	@docker compose -f docker-compose.streams.yml ps
	@docker compose -f docker-compose.dlstreamer.yml ps
