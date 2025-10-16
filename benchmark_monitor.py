# #!/usr/bin/env python3
# """
# Enhanced DLStreamer Benchmark Monitor - Fixed Docker API Issues
# """

# import json
# import os
# import time
# import threading
# import subprocess
# from collections import defaultdict, deque
# from datetime import datetime
# import psutil
# import docker
# from kafka import KafkaConsumer
# from kafka.errors import KafkaError

# class EnhancedBenchmarkMonitor:
#     def __init__(self, kafka_broker="kafka:9092", topic="dlstreamer_output"):
#         self.kafka_broker = kafka_broker
#         self.topic = topic
#         self.benchmark_dir = "/benchmark_results"
        
#         # Performance tracking per camera
#         self.camera_metrics = defaultdict(lambda: {
#             'frame_count': 0,
#             'start_time': None,
#             'last_update': None,
#             'fps_history': deque(maxlen=60),
#             'cpu_history': deque(maxlen=60),
#             'memory_history': deque(maxlen=60),
#             'inference_times': deque(maxlen=100),
#             'total_frames': 0,
#             'active': False,
#             'first_frame_time': None,
#             'last_frame_time': None
#         })
        
#         # System monitoring
#         try:
#             self.docker_client = docker.from_env()
#         except Exception as e:
#             print(f"Docker client initialization failed: {e}")
#             self.docker_client = None
            
#         self.dlstreamer_container = None
        
#         # System info
#         self.cpu_count = psutil.cpu_count()
#         self.cpu_count_logical = psutil.cpu_count(logical=True)
        
#         # Create benchmark directory
#         os.makedirs(self.benchmark_dir, exist_ok=True)
        
#         print(f"Enhanced Benchmark Monitor initialized")
#         print(f"Kafka: {kafka_broker}, Topic: {topic}")
#         print(f"CPU: {self.cpu_count} cores, {self.cpu_count_logical} threads")
#         print(f"Results will be saved to: {self.benchmark_dir}")

#     def get_container_stats(self):
#         """Get CPU and memory stats for DLStreamer container - Fixed API compatibility"""
#         try:
#             if not self.docker_client:
#                 return self.get_fallback_stats()
                
#             if not self.dlstreamer_container:
#                 containers = self.docker_client.containers.list()
#                 for container in containers:
#                     if 'dlstreamer' in container.name.lower():
#                         self.dlstreamer_container = container
#                         break
            
#             if self.dlstreamer_container:
#                 try:
#                     stats = self.dlstreamer_container.stats(stream=False)
                    
#                     # Handle different Docker API versions
#                     cpu_stats = stats.get('cpu_stats', {})
#                     precpu_stats = stats.get('precpu_stats', {})
#                     memory_stats = stats.get('memory_stats', {})
                    
#                     # Calculate CPU percentage with error handling
#                     cpu_percent = 0.0
#                     try:
#                         cpu_usage = cpu_stats.get('cpu_usage', {})
#                         precpu_usage = precpu_stats.get('cpu_usage', {})
                        
#                         if 'total_usage' in cpu_usage and 'total_usage' in precpu_usage:
#                             cpu_delta = cpu_usage['total_usage'] - precpu_usage['total_usage']
#                             system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)
                            
#                             if system_delta > 0:
#                                 # Try to get number of CPUs from percpu_usage or fallback
#                                 percpu_usage = cpu_usage.get('percpu_usage', [])
#                                 num_cpus = len(percpu_usage) if percpu_usage else self.cpu_count_logical
#                                 cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0
#                     except Exception as e:
#                         print(f"CPU calculation error: {e}")
#                         cpu_percent = psutil.cpu_percent()
                    
#                     # Calculate memory usage with error handling
#                     memory_percent = 0.0
#                     memory_usage_mb = 0.0
#                     try:
#                         if 'usage' in memory_stats and 'limit' in memory_stats:
#                             memory_usage = memory_stats['usage']
#                             memory_limit = memory_stats['limit']
#                             memory_percent = (memory_usage / memory_limit) * 100.0
#                             memory_usage_mb = memory_usage / (1024 * 1024)
#                     except Exception as e:
#                         print(f"Memory calculation error: {e}")
#                         memory_percent = psutil.virtual_memory().percent
#                         memory_usage_mb = psutil.virtual_memory().used / (1024 * 1024)
                    
#                     return {
#                         'cpu_percent': round(cpu_percent, 2),
#                         'memory_percent': round(memory_percent, 2),
#                         'memory_usage_mb': round(memory_usage_mb, 2)
#                     }
#                 except Exception as e:
#                     print(f"Container stats error: {e}")
#                     return self.get_fallback_stats()
#         except Exception as e:
#             print(f"Docker stats error: {e}")
            
#         return self.get_fallback_stats()

#     def get_fallback_stats(self):
#         """Fallback to system stats when Docker API fails"""
#         return {
#             'cpu_percent': psutil.cpu_percent(),
#             'memory_percent': psutil.virtual_memory().percent,
#             'memory_usage_mb': psutil.virtual_memory().used / (1024 * 1024)
#         }

#     def get_detailed_cpu_stats(self):
#         """Get per-core CPU usage and frequencies"""
#         try:
#             # Get per-core usage
#             per_core_usage = psutil.cpu_percent(percpu=True, interval=0.1)
            
#             # Get CPU frequency
#             cpu_freq = psutil.cpu_freq()
            
#             # Get CPU temperature (if available)
#             cpu_temp = 0
#             try:
#                 temps = psutil.sensors_temperatures()
#                 if 'coretemp' in temps:
#                     cpu_temp = temps['coretemp'][0].current
#                 elif 'k10temp' in temps:  # AMD CPUs
#                     cpu_temp = temps['k10temp'][0].current
#                 elif 'acpi' in temps:
#                     cpu_temp = temps['acpi'][0].current
#             except:
#                 pass
                
#             # Get load average (Linux only)
#             load_avg = [0, 0, 0]
#             try:
#                 load_avg = os.getloadavg()
#             except:
#                 pass
            
#             return {
#                 'per_core_usage': per_core_usage,
#                 'avg_core_usage': round(sum(per_core_usage) / len(per_core_usage), 2),
#                 'max_core_usage': round(max(per_core_usage), 2),
#                 'min_core_usage': round(min(per_core_usage), 2),
#                 'cpu_frequency_mhz': round(cpu_freq.current, 2) if cpu_freq else 0,
#                 'cpu_frequency_max_mhz': round(cpu_freq.max, 2) if cpu_freq else 0,
#                 'cpu_temperature_c': round(cpu_temp, 1),
#                 'load_average_1min': round(load_avg[0], 2),
#                 'load_average_5min': round(load_avg[1], 2),
#                 'load_average_15min': round(load_avg[2], 2),
#                 'active_cores': sum(1 for usage in per_core_usage if usage > 10),
#                 'cores_over_90': sum(1 for usage in per_core_usage if usage > 90),
#                 'cores_over_95': sum(1 for usage in per_core_usage if usage > 95)
#             }
#         except Exception as e:
#             print(f"Error getting detailed CPU stats: {e}")
#             return {
#                 'per_core_usage': [],
#                 'avg_core_usage': 0,
#                 'max_core_usage': 0,
#                 'min_core_usage': 0,
#                 'cpu_frequency_mhz': 0,
#                 'cpu_frequency_max_mhz': 0,
#                 'cpu_temperature_c': 0,
#                 'load_average_1min': 0,
#                 'load_average_5min': 0,
#                 'load_average_15min': 0,
#                 'active_cores': 0,
#                 'cores_over_90': 0,
#                 'cores_over_95': 0
#             }

#     def get_gpu_stats(self):
#         """Get GPU utilization if available - Fixed nvidia-smi detection"""
#         try:
#             # Try to get NVIDIA GPU stats
#             result = subprocess.run([
#                 'nvidia-smi', 
#                 '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,clocks.gr,clocks.mem', 
#                 '--format=csv,noheader,nounits'
#             ], capture_output=True, text=True, timeout=5)
            
#             if result.returncode == 0 and result.stdout.strip():
#                 values = result.stdout.strip().split(', ')
#                 if len(values) >= 4:
#                     gpu_util = float(values[0]) if values[0] != '[N/A]' and values[0] != 'N/A' else 0
#                     mem_used = float(values[1]) if values[1] != '[N/A]' and values[1] != 'N/A' else 0
#                     mem_total = float(values[2]) if values[2] != '[N/A]' and values[2] != 'N/A' else 0
#                     temp = float(values[3]) if values[3] != '[N/A]' and values[3] != 'N/A' else 0
#                     power = float(values[4]) if len(values) > 4 and values[4] != '[N/A]' and values[4] != 'N/A' else 0
#                     clock_gpu = float(values[5]) if len(values) > 5 and values[5] != '[N/A]' and values[5] != 'N/A' else 0
#                     clock_mem = float(values[6]) if len(values) > 6 and values[6] != '[N/A]' and values[6] != 'N/A' else 0
                    
#                     return {
#                         'gpu_available': True,
#                         'gpu_utilization_percent': gpu_util,
#                         'gpu_memory_used_mb': mem_used,
#                         'gpu_memory_total_mb': mem_total,
#                         'gpu_memory_percent': (mem_used / mem_total) * 100 if mem_total > 0 else 0,
#                         'gpu_temperature_c': temp,
#                         'gpu_power_watts': power,
#                         'gpu_clock_mhz': clock_gpu,
#                         'gpu_memory_clock_mhz': clock_mem
#                     }
#         except Exception as e:
#             # Don't print error every time - only once
#             if not hasattr(self, '_gpu_error_logged'):
#                 print(f"GPU monitoring not available: {e}")
#                 self._gpu_error_logged = True
        
#         return {
#             'gpu_available': False,
#             'gpu_utilization_percent': 0,
#             'gpu_memory_used_mb': 0,
#             'gpu_memory_total_mb': 0,
#             'gpu_memory_percent': 0,
#             'gpu_temperature_c': 0,
#             'gpu_power_watts': 0,
#             'gpu_clock_mhz': 0,
#             'gpu_memory_clock_mhz': 0
#         }

#     def get_inference_timing_stats(self, camera_id):
#         """Calculate detailed timing statistics"""
#         metrics = self.camera_metrics[camera_id]
#         current_time = time.time()
        
#         # Calculate frame processing intervals
#         if len(metrics['fps_history']) >= 2:
#             recent_fps = list(metrics['fps_history'])[-10:]
#             fps_variance = sum((fps - sum(recent_fps)/len(recent_fps))**2 for fps in recent_fps) / len(recent_fps)
#             fps_stability = 1 / (1 + fps_variance) if fps_variance > 0 else 1
#         else:
#             fps_variance = 0
#             fps_stability = 1
        
#         # Calculate processing efficiency
#         target_fps = 30
#         current_fps = self.calculate_fps(camera_id)
#         processing_efficiency = (current_fps / target_fps) * 100 if target_fps > 0 else 0
        
#         # Calculate frame drop rate
#         if metrics['first_frame_time'] and current_time > metrics['first_frame_time']:
#             elapsed_time = current_time - metrics['first_frame_time']
#             expected_frames = elapsed_time * target_fps
#             actual_frames = metrics['total_frames']
#             frame_drop_rate = ((expected_frames - actual_frames) / expected_frames) * 100 if expected_frames > 0 else 0
#             frames_behind = expected_frames - actual_frames
#         else:
#             frame_drop_rate = 0
#             frames_behind = 0
#             expected_frames = 0
        
#         avg_inference_time = sum(metrics['inference_times']) / len(metrics['inference_times']) if metrics['inference_times'] else 0
        
#         return {
#             'fps_variance': round(fps_variance, 2),
#             'fps_stability_score': round(fps_stability, 3),
#             'processing_efficiency_percent': round(processing_efficiency, 2),
#             'frame_drop_rate_percent': round(frame_drop_rate, 2),
#             'expected_frames_total': round(expected_frames, 0),
#             'frames_behind_schedule': round(frames_behind, 0),
#             'average_inference_time_ms': round(avg_inference_time, 2)
#         }

#     def process_kafka_message(self, message):
#         """Process incoming Kafka message and extract metrics"""
#         try:
#             data = json.loads(message.value.decode('utf-8'))
            
#             # Extract camera ID from tags or message
#             camera_id = None
#             if 'tags' in data:
#                 tags = json.loads(data['tags']) if isinstance(data['tags'], str) else data['tags']
#                 camera_id = tags.get('camera')
            
#             if not camera_id and 'camera' in data:
#                 camera_id = data['camera']
                
#             if not camera_id:
#                 if 'video' in data:
#                     video_path = data['video']
#                     if 'cam' in video_path:
#                         import re
#                         match = re.search(r'cam(\d+)', video_path)
#                         if match:
#                             camera_id = f"cam{match.group(1)}"
            
#             if not camera_id:
#                 return
            
#             current_time = time.time()
#             metrics = self.camera_metrics[camera_id]
            
#             # Initialize if first message
#             if not metrics['active']:
#                 metrics['start_time'] = current_time
#                 metrics['first_frame_time'] = current_time
#                 metrics['active'] = True
#                 print(f"Started monitoring camera: {camera_id}")
            
#             # Update frame count
#             metrics['frame_count'] += 1
#             metrics['total_frames'] += 1
#             metrics['last_update'] = current_time
#             metrics['last_frame_time'] = current_time
            
#             # Extract inference time if available
#             if 'inference_time' in data:
#                 metrics['inference_times'].append(data['inference_time'])
#             elif 'timestamp' in data:
#                 try:
#                     if isinstance(data['timestamp'], (int, float)):
#                         msg_time = data['timestamp']
#                         if msg_time > 1e12:
#                             msg_time = msg_time / 1000
#                     else:
#                         msg_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')).timestamp()
                    
#                     processing_time = (current_time - msg_time) * 1000
#                     if 0 < processing_time < 10000:
#                         metrics['inference_times'].append(processing_time)
#                 except Exception:
#                     pass
            
#         except Exception as e:
#             print(f"Error processing message: {e}")

#     def calculate_fps(self, camera_id):
#         """Calculate FPS for a specific camera"""
#         metrics = self.camera_metrics[camera_id]
#         if not metrics['active'] or not metrics['start_time']:
#             return 0.0
        
#         current_time = time.time()
#         elapsed_time = current_time - metrics['start_time']
        
#         if elapsed_time > 0:
#             fps = metrics['frame_count'] / elapsed_time
#             return round(fps, 2)
#         return 0.0

#     def log_metrics(self):
#         """Enhanced metrics logging with error handling"""
#         while True:
#             try:
#                 current_time = time.time()
#                 system_stats = self.get_container_stats()
#                 detailed_cpu = self.get_detailed_cpu_stats()
#                 gpu_stats = self.get_gpu_stats()
                
#                 # System-wide metrics
#                 system_memory = psutil.virtual_memory()
#                 system_disk = psutil.disk_usage('/')
                
#                 for camera_id, metrics in self.camera_metrics.items():
#                     if not metrics['active']:
#                         continue
                    
#                     # Calculate current FPS
#                     fps = self.calculate_fps(camera_id)
                    
#                     # Get detailed timing stats
#                     timing_stats = self.get_inference_timing_stats(camera_id)
                    
#                     # Store metrics history
#                     metrics['fps_history'].append(fps)
#                     metrics['cpu_history'].append(system_stats['cpu_percent'])
#                     metrics['memory_history'].append(system_stats['memory_percent'])
                    
#                     # Calculate averages
#                     avg_fps = sum(metrics['fps_history']) / len(metrics['fps_history']) if metrics['fps_history'] else 0
#                     avg_cpu = sum(metrics['cpu_history']) / len(metrics['cpu_history']) if metrics['cpu_history'] else 0
#                     avg_memory = sum(metrics['memory_history']) / len(metrics['memory_history']) if metrics['memory_history'] else 0
                    
#                     # Enhanced benchmark data
#                     benchmark_data = {
#                         'timestamp': datetime.now().isoformat(),
#                         'camera_id': camera_id,
#                         'current_fps': fps,
#                         'average_fps': round(avg_fps, 2),
#                         'total_frames': metrics['total_frames'],
#                         'container_cpu_percent': system_stats['cpu_percent'],
#                         'container_cpu_average': round(avg_cpu, 2),
#                         'system_cpu_per_core': detailed_cpu['per_core_usage'],
#                         'system_cpu_average': detailed_cpu['avg_core_usage'],
#                         'system_cpu_max_core': detailed_cpu['max_core_usage'],
#                         'system_cpu_min_core': detailed_cpu['min_core_usage'],
#                         'cpu_cores_total': self.cpu_count_logical,
#                         'cpu_cores_active': detailed_cpu['active_cores'],
#                         'cpu_cores_over_90': detailed_cpu['cores_over_90'],
#                         'cpu_cores_over_95': detailed_cpu['cores_over_95'],
#                         'cpu_frequency_current_mhz': detailed_cpu['cpu_frequency_mhz'],
#                         'cpu_frequency_max_mhz': detailed_cpu['cpu_frequency_max_mhz'],
#                         'cpu_temperature_c': detailed_cpu['cpu_temperature_c'],
#                         'system_load_1min': detailed_cpu['load_average_1min'],
#                         'system_load_5min': detailed_cpu['load_average_5min'],
#                         'system_load_15min': detailed_cpu['load_average_15min'],
#                         'container_memory_percent': system_stats['memory_percent'],
#                         'container_memory_mb': system_stats['memory_usage_mb'],
#                         'container_memory_average': round(avg_memory, 2),
#                         'system_memory_total_gb': round(system_memory.total / (1024**3), 2),
#                         'system_memory_used_gb': round(system_memory.used / (1024**3), 2),
#                         'system_memory_percent': system_memory.percent,
#                         'system_memory_available_gb': round(system_memory.available / (1024**3), 2),
#                         'gpu_available': gpu_stats['gpu_available'],
#                         'gpu_utilization_percent': gpu_stats['gpu_utilization_percent'],
#                         'gpu_memory_used_mb': gpu_stats['gpu_memory_used_mb'],
#                         'gpu_memory_total_mb': gpu_stats['gpu_memory_total_mb'],
#                         'gpu_memory_percent': round(gpu_stats['gpu_memory_percent'], 2),
#                         'gpu_temperature_c': gpu_stats['gpu_temperature_c'],
#                         'gpu_power_watts': gpu_stats['gpu_power_watts'],
#                         'gpu_clock_mhz': gpu_stats['gpu_clock_mhz'],
#                         'gpu_memory_clock_mhz': gpu_stats['gpu_memory_clock_mhz'],
#                         'processing_efficiency_percent': timing_stats['processing_efficiency_percent'],
#                         'frame_drop_rate_percent': timing_stats['frame_drop_rate_percent'],
#                         'fps_stability_score': timing_stats['fps_stability_score'],
#                         'fps_variance': timing_stats['fps_variance'],
#                         'frames_behind_schedule': timing_stats['frames_behind_schedule'],
#                         'expected_frames_total': timing_stats['expected_frames_total'],
#                         'average_inference_time_ms': timing_stats['average_inference_time_ms'],
#                         'uptime_seconds': round(current_time - metrics['start_time'], 2) if metrics['start_time'] else 0,
#                         'disk_usage_percent': system_disk.percent,
#                         'disk_free_gb': round(system_disk.free / (1024**3), 2)
#                     }
                    
#                     # Enhanced console output
#                     gpu_status = f"GPU: {gpu_stats['gpu_utilization_percent']:.1f}%" if gpu_stats['gpu_available'] else "GPU: N/A"
#                     thermal_status = f"Temp: {detailed_cpu['cpu_temperature_c']:.1f}°C" if detailed_cpu['cpu_temperature_c'] > 0 else ""
                    
#                     print(f"[{camera_id}] FPS: {fps:.1f} ({timing_stats['processing_efficiency_percent']:.1f}% eff) | "
#                           f"CPU: {detailed_cpu['avg_core_usage']:.1f}% ({detailed_cpu['cores_over_95']}/{self.cpu_count_logical} maxed) | "
#                           f"{gpu_status} | "
#                           f"Drops: {timing_stats['frame_drop_rate_percent']:.1f}% | "
#                           f"Frames: {metrics['total_frames']} | "
#                           f"{thermal_status}")
                    
#                     # Save enhanced data
#                     json_file = os.path.join(self.benchmark_dir, f"{camera_id}_detailed_benchmark.json")
                    
#                     # Load existing data
#                     benchmark_history = []
#                     if os.path.exists(json_file):
#                         try:
#                             with open(json_file, 'r') as f:
#                                 benchmark_history = json.load(f)
#                         except:
#                             benchmark_history = []
                    
#                     # Append new data
#                     benchmark_history.append(benchmark_data)
                    
#                     # Keep only last 1000 entries
#                     if len(benchmark_history) > 1000:
#                         benchmark_history = benchmark_history[-1000:]
                    
#                     # Save updated data
#                     with open(json_file, 'w') as f:
#                         json.dump(benchmark_history, f, indent=2)
                
#                 # Reset frame counts for next interval
#                 for metrics in self.camera_metrics.values():
#                     if metrics['active']:
#                         metrics['frame_count'] = 0
#                         metrics['start_time'] = current_time
                
#                 time.sleep(5)
                
#             except Exception as e:
#                 print(f"Error in enhanced metrics logging: {e}")
#                 time.sleep(5)

#     def run(self):
#         """Main monitoring loop with error handling"""
#         print("Starting enhanced benchmark monitor...")
        
#         # Start metrics logging thread
#         metrics_thread = threading.Thread(target=self.log_metrics, daemon=True)
#         metrics_thread.start()
        
#         # Wait for Kafka to be ready
#         time.sleep(10)
        
#         try:
#             consumer = KafkaConsumer(
#                 self.topic,
#                 bootstrap_servers=[self.kafka_broker],
#                 group_id='enhanced_benchmark_monitor_group',
#                 value_deserializer=lambda m: m,
#                 auto_offset_reset='latest',
#                 enable_auto_commit=True,
#                 consumer_timeout_ms=1000
#             )
            
#             print(f"Connected to Kafka topic: {self.topic}")
#             print("Monitoring DLStreamer inference messages...")
            
#             for message in consumer:
#                 self.process_kafka_message(message)
                
#         except KafkaError as e:
#             print(f"Kafka error: {e}")
#         except KeyboardInterrupt:
#             print("Enhanced benchmark monitor stopped by user")
#         except Exception as e:
#             print(f"Unexpected error: {e}")

# if __name__ == "__main__":
#     monitor = EnhancedBenchmarkMonitor()
#     monitor.run()
#!/usr/bin/env python3
"""
Benchmark Monitor for Intel Arc A770 Video Processing Pipeline
Monitors Kafka messages and system performance
"""

import json
import time
import csv
import argparse
import threading
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict, deque

import psutil
from kafka import KafkaConsumer

class PerformanceMonitor:
    """Monitors system and GPU performance"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.stats = defaultdict(lambda: defaultdict(list))
        self.fps_counters = defaultdict(lambda: deque(maxlen=30))  # 30 second window
        self.running = True
        
    def get_gpu_stats(self) -> Dict[str, float]:
        """Get GPU utilization stats"""
        try:
            import subprocess
            result = subprocess.run(
                ["intel_gpu_top", "-J", "-s", "1000"], 
                capture_output=True, text=True, timeout=2
            )
            
            if result.returncode == 0:
                # Parse intel_gpu_top JSON output
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('{'):
                        data = json.loads(line)
                        engines = data.get('engines', {})
                        return {
                            'render_3d': engines.get('Render/3D', {}).get('busy', 0),
                            'video': engines.get('Video', {}).get('busy', 0),
                            'blitter': engines.get('Blitter', {}).get('busy', 0)
                        }
        except Exception as e:
            print(f"GPU stats error: {e}")
        
        return {'render_3d': 0, 'video': 0, 'blitter': 0}
    
    def get_system_stats(self) -> Dict[str, float]:
        """Get system performance stats"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_gb': psutil.virtual_memory().used / (1024**3)
        }
    
    def calculate_fps(self, camera: str, task: str) -> float:
        """Calculate FPS for camera/task combination"""
        key = f"{camera}_{task}"
        timestamps = self.fps_counters[key]
        
        if len(timestamps) < 2:
            return 0.0
        
        # Calculate FPS over the time window
        time_span = timestamps[-1] - timestamps[0]
        if time_span > 0:
            return (len(timestamps) - 1) / time_span
        return 0.0
    
    def update_fps(self, camera: str, task: str) -> None:
        """Update FPS counter for camera/task"""
        key = f"{camera}_{task}"
        self.fps_counters[key].append(time.time())
    
    def save_results(self) -> None:
        """Save performance results to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"{self.output_dir}/performance_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'camera', 'task', 'fps', 
                'cpu_percent', 'memory_percent', 'memory_used_gb',
                'gpu_render_3d', 'gpu_video', 'gpu_blitter'
            ])
            
            for camera_task, fps_list in self.fps_counters.items():
                if '_' in camera_task:
                    camera, task = camera_task.split('_', 1)
                    fps = self.calculate_fps(camera, task)
                    
                    # Get latest system stats
                    sys_stats = self.get_system_stats()
                    gpu_stats = self.get_gpu_stats()
                    
                    writer.writerow([
                        datetime.now().isoformat(),
                        camera, task, fps,
                        sys_stats['cpu_percent'],
                        sys_stats['memory_percent'],
                        sys_stats['memory_used_gb'],
                        gpu_stats['render_3d'],
                        gpu_stats['video'],
                        gpu_stats['blitter']
                    ])
        
        print(f"Results saved to: {csv_file}")

class KafkaMonitor:
    """Monitors Kafka messages for video processing results"""
    
    def __init__(self, kafka_broker: str, kafka_topic: str, perf_monitor: PerformanceMonitor):
        self.kafka_broker = kafka_broker
        self.kafka_topic = kafka_topic
        self.perf_monitor = perf_monitor
        self.message_count = 0
        self.start_time = time.time()
        
    def start_monitoring(self) -> None:
        """Start monitoring Kafka messages"""
        print(f"Connecting to Kafka: {self.kafka_broker}")
        print(f"Monitoring topic: {self.kafka_topic}")
        
        try:
            consumer = KafkaConsumer(
                self.kafka_topic,
                bootstrap_servers=[self.kafka_broker],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=1000
            )
            
            print("Connected to Kafka, waiting for messages...")
            
            for message in consumer:
                if not self.perf_monitor.running:
                    break
                
                self.process_message(message.value)
                self.message_count += 1
                
                # Print status every 100 messages
                if self.message_count % 100 == 0:
                    self.print_status()
                    
        except Exception as e:
            print(f"Kafka monitoring error: {e}")
    
    def process_message(self, message: Dict) -> None:
        """Process individual Kafka message"""
        try:
            # Extract camera and task from message
            camera = message.get('tags', {}).get('camera', 'unknown')
            task = message.get('tags', {}).get('task', 'unknown')
            
            if camera != 'unknown' and task != 'unknown':
                self.perf_monitor.update_fps(camera, task)
                
        except Exception as e:
            print(f"Message processing error: {e}")
    
    def print_status(self) -> None:
        """Print current monitoring status"""
        elapsed = time.time() - self.start_time
        msg_per_sec = self.message_count / elapsed if elapsed > 0 else 0
        
        print(f"\n=== Performance Status ===")
        print(f"Messages processed: {self.message_count}")
        print(f"Messages/sec: {msg_per_sec:.1f}")
        print(f"Elapsed time: {elapsed:.1f}s")
        
        # Print FPS for each camera/task
        for camera_task in self.perf_monitor.fps_counters:
            if '_' in camera_task:
                camera, task = camera_task.split('_', 1)
                fps = self.perf_monitor.calculate_fps(camera, task)
                print(f"  {camera} ({task}): {fps:.1f} FPS")
        
        # Print system stats
        sys_stats = self.perf_monitor.get_system_stats()
        gpu_stats = self.perf_monitor.get_gpu_stats()
        
        print(f"CPU: {sys_stats['cpu_percent']:.1f}%")
        print(f"Memory: {sys_stats['memory_percent']:.1f}% ({sys_stats['memory_used_gb']:.1f} GB)")
        print(f"GPU Render/3D: {gpu_stats['render_3d']:.1f}%")
        print(f"GPU Video: {gpu_stats['video']:.1f}%")
        print("=" * 25)

def main():
    parser = argparse.ArgumentParser(description="Benchmark Monitor for Video Processing")
    parser.add_argument("--kafka-broker", required=True, help="Kafka broker address")
    parser.add_argument("--kafka-topic", required=True, help="Kafka topic to monitor")
    parser.add_argument("--output-dir", required=True, help="Output directory for results")
    parser.add_argument("--duration", type=int, default=0, help="Monitoring duration in seconds (0 = infinite)")
    
    args = parser.parse_args()
    
    # Create performance monitor
    perf_monitor = PerformanceMonitor(args.output_dir)
    
    # Create Kafka monitor
    kafka_monitor = KafkaMonitor(args.kafka_broker, args.kafka_topic, perf_monitor)
    
    # Start monitoring in separate thread
    monitor_thread = threading.Thread(target=kafka_monitor.start_monitoring)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    try:
        # Run for specified duration or until interrupted
        if args.duration > 0:
            time.sleep(args.duration)
        else:
            while True:
                time.sleep(10)
                kafka_monitor.print_status()
                
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    
    finally:
        perf_monitor.running = False
        perf_monitor.save_results()
        print("Monitoring stopped")

if __name__ == "__main__":
    main()
