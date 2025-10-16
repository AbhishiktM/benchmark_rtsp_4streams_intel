# .PHONY: setup start stop clean logs monitor

# # One-command setup for new systems
# setup:
# 	@echo "Setting up Universal DLStreamer Pipeline..."
# 	docker network create dlstreamer_shared_net || true
# 	docker compose -f docker-compose.streams.yml up -d
# 	sleep 10
# 	docker compose -f docker-compose.dlstreamer.yml --profile auto up -d
# 	@echo "✅ Setup complete! Monitor with: make monitor"

# # Start services
# start:
# 	docker compose -f docker-compose.streams.yml up -d
# 	docker compose -f docker-compose.dlstreamer.yml --profile auto up -d

# # Stop services  
# stop:
# 	docker compose -f docker-compose.dlstreamer.yml down
# 	docker compose -f docker-compose.streams.yml down

# # Clean everything
# clean:
# 	docker compose -f docker-compose.dlstreamer.yml down -v
# 	docker compose -f docker-compose.streams.yml down -v
# 	docker network rm dlstreamer_shared_net || true
# 	docker system prune -f

# # View logs
# logs:
# 	docker logs -f benchmark_monitor

# # Monitor performance
# monitor:
# 	@echo "🔍 System Detection:"
# 	@docker logs dlstreamer_auto 2>/dev/null | grep -E "(detected|Selected)" || echo "Container not running"
# 	@echo "\n📊 Current Performance:"
# 	@docker logs benchmark_monitor 2>/dev/null | tail -10 || echo "No benchmark data yet"

# # Check status
# status:
# 	@echo "📋 Service Status:"
# 	@docker compose -f docker-compose.streams.yml ps
# 	@docker compose -f docker-compose.dlstreamer.yml ps
.PHONY: setup start stop restart clean logs logs-streams gpu-monitor test-gpu test-streams help

# Default target
help:
	@echo "Intel Arc A770 Video Analytics Pipeline"
	@echo "Available commands:"
	@echo "  make setup        - Build and start all services"
	@echo "  make start        - Start all services"
	@echo "  make stop         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make clean        - Remove containers, volumes, network"
	@echo "  make logs         - Show DLStreamer logs"
	@echo "  make logs-streams - Show camera feeder logs"
	@echo "  make gpu-monitor  - Monitor GPU usage"
	@echo "  make test-gpu     - Test GPU access"
	@echo "  make test-streams - Test RTSP streams"

# Setup everything from scratch
setup:
	@echo "Setting up Intel Arc A770 video analytics pipeline..."
	docker-compose down -v
	docker-compose build
	docker-compose up -d
	@echo "Waiting for services to start..."
	sleep 10
	@echo "Setup complete. Use 'make logs' to monitor progress."

# Start services
start:
	docker-compose up -d

# Stop services
stop:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# Clean everything
clean:
	@echo "Cleaning up all containers, volumes, and networks..."
	docker-compose down -v
	docker system prune -f
	@echo "Cleanup complete."

# Show DLStreamer logs
logs:
	docker logs -f dlstreamer_arc

# Show camera feeder logs
logs-streams:
	@echo "Camera feeder logs:"
	docker logs cam0-feeder --tail 20
	docker logs cam2-feeder --tail 20
	docker logs cam4-feeder --tail 20
	docker logs cam6-feeder --tail 20

# Monitor GPU usage
gpu-monitor:
	@echo "Monitoring GPU usage (Ctrl+C to stop):"
	sudo intel_gpu_top

# Test GPU access
test-gpu:
	@echo "Testing GPU access..."
	docker exec dlstreamer_arc ls -la /dev/dri/
	@echo "VAAPI info:"
	docker exec dlstreamer_arc vainfo --device /dev/dri/renderD129
	@echo "OpenVINO devices:"
	docker exec dlstreamer_arc python3 -c "from openvino.runtime import Core; print(Core().available_devices)"

# Test RTSP streams
test-streams:
	@echo "Testing RTSP streams..."
	for cam in cam0 cam2 cam4 cam6; do \
		echo "Testing $$cam:"; \
		ffprobe rtsp://localhost:8554/$$cam 2>&1 | grep "Stream #0:0" || echo "Stream $$cam not ready"; \
	done
