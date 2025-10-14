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

.PHONY: help setup start stop restart clean logs logs-streams gpu-monitor test-streams

help:
	@echo "Intel Arc A770 DLStreamer - Available Commands:"
	@echo ""
	@echo "Setup & Control:"
	@echo "  make setup          - Initial setup (network + build + start all)"
	@echo "  make start          - Start all services"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make clean          - Remove containers and volumes"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs           - Show DLStreamer logs"
	@echo "  make logs-streams   - Show RTSP stream logs"
	@echo "  make gpu-monitor    - Monitor GPU usage"
	@echo "  make test-streams   - Test RTSP streams availability"
	@echo ""
	@echo "Debugging:"
	@echo "  make logs-kafka     - Show Kafka logs"
	@echo "  make logs-benchmark - Show benchmark monitor logs"

setup:
	@echo "=========================================="
	@echo "Setting up Intel Arc A770 DLStreamer"
	@echo "=========================================="
	@echo ""
	@echo "Step 1: Creating Docker network..."
	docker network create dlstreamer_net 2>/dev/null || echo "Network already exists"
	@echo ""
	@echo "Step 2: Building DLStreamer image..."
	docker compose build
	@echo ""
	@echo "Step 3: Starting all services..."
	docker compose up -d
	@echo ""
	@echo "Step 4: Waiting for services to be ready..."
	@sleep 10
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  make logs           - View DLStreamer logs"
	@echo "  make test-streams   - Test RTSP streams"
	@echo "  make gpu-monitor    - Monitor GPU usage"

start:
	docker compose up -d

stop:
	docker compose down

restart:
	docker compose restart

clean:
	@echo "Cleaning up..."
	docker compose down -v
	docker network rm dlstreamer_net 2>/dev/null || true
	@echo "✅ Cleanup complete"

logs:
	docker logs -f dlstreamer_arc

logs-streams:
	@echo "RTSP Stream Logs:"
	@echo "================="
	@echo ""
	@echo "cam0-feeder:"
	@docker logs --tail 10 cam0-feeder
	@echo ""
	@echo "cam2-feeder:"
	@docker logs --tail 10 cam2-feeder
	@echo ""
	@echo "cam4-feeder:"
	@docker logs --tail 10 cam4-feeder
	@echo ""
	@echo "cam6-feeder:"
	@docker logs --tail 10 cam6-feeder

logs-kafka:
	docker logs -f kafka_dlstreamer

logs-benchmark:
	docker logs -f benchmark_monitor

gpu-monitor:
	@echo "Monitoring Intel Arc A770 GPU..."
	@echo "Press Ctrl+C to exit"
	@echo ""
	sudo intel_gpu_top

test-streams:
	@echo "Testing RTSP streams..."
	@echo ""
	@echo "cam0: rtsp://localhost:8554/cam0"
	@ffprobe -v error -show_entries stream=codec_name,width,height -of default=noprint_wrappers=1 rtsp://localhost:8554/cam0 2>&1 | head -5 || echo "❌ cam0 not available"
	@echo ""
	@echo "cam2: rtsp://localhost:8554/cam2"
	@ffprobe -v error -show_entries stream=codec_name,width,height -of default=noprint_wrappers=1 rtsp://localhost:8554/cam2 2>&1 | head -5 || echo "❌ cam2 not available"
	@echo ""
	@echo "cam4: rtsp://localhost:8554/cam4"
	@ffprobe -v error -show_entries stream=codec_name,width,height -of default=noprint_wrappers=1 rtsp://localhost:8554/cam4 2>&1 | head -5 || echo "❌ cam4 not available"
	@echo ""
	@echo "cam6: rtsp://localhost:8554/cam6"
	@ffprobe -v error -show_entries stream=codec_name,width,height -of default=noprint_wrappers=1 rtsp://localhost:8554/cam6 2>&1 | head -5 || echo "❌ cam6 not available"
