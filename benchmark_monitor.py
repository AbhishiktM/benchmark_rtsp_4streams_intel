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
Enhanced DLStreamer Benchmark Monitor with Universal Hardware Detection
"""

import json
import os
import time
import threading
import subprocess
from collections import defaultdict, deque
from datetime import datetime
import psutil
import docker
from kafka import KafkaConsumer
from kafka.errors import KafkaError

class UniversalSystemProfiler:
    """Universal hardware detection for Intel, AMD, and NVIDIA systems"""
    
    def __init__(self):
        self.system_info = self._detect_system()
        
    def _detect_system(self):
        """Detect system hardware capabilities universally"""
        return {
            'cpu': self._detect_cpu(),
            'memory': self._detect_memory(),
            'gpu': self._detect_gpu(),
            'storage': self._detect_storage(),
            'capabilities': self._detect_capabilities()
        }
    
    def _detect_cpu(self):
        """Universal CPU detection"""
        cpu_info = {
            'physical_cores': psutil.cpu_count(logical=False),
            'logical_cores': psutil.cpu_count(logical=True),
            'architecture': os.uname().machine,
            'vendor': 'Unknown',
            'model': 'Unknown',
            'performance_class': 'Unknown'
        }
        
        try:
            # Get CPU frequency
            freq = psutil.cpu_freq()
            if freq:
                cpu_info['base_frequency_mhz'] = freq.min
                cpu_info['max_frequency_mhz'] = freq.max
                cpu_info['current_frequency_mhz'] = freq.current
            
            # Get CPU model and vendor
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            cpu_info['model'] = line.split(':')[1].strip()
                            break
                        elif 'vendor_id' in line:
                            vendor = line.split(':')[1].strip().lower()
                            if 'intel' in vendor or 'genuineintel' in vendor:
                                cpu_info['vendor'] = 'Intel'
                            elif 'amd' in vendor or 'authenticamd' in vendor:
                                cpu_info['vendor'] = 'AMD'
            except:
                pass
            
            # Detect vendor from model name if not found
            if cpu_info['vendor'] == 'Unknown':
                model = cpu_info['model'].lower()
                if 'intel' in model:
                    cpu_info['vendor'] = 'Intel'
                elif 'amd' in model or 'ryzen' in model:
                    cpu_info['vendor'] = 'AMD'
            
            # Performance classification
            total_cores = cpu_info['logical_cores']
            max_freq = cpu_info.get('max_frequency_mhz', 0)
            
            if total_cores >= 16 and max_freq >= 3500:
                cpu_info['performance_class'] = 'High'
            elif total_cores >= 8 and max_freq >= 3000:
                cpu_info['performance_class'] = 'Medium'
            else:
                cpu_info['performance_class'] = 'Low'
                
            # Intel-specific features
            if cpu_info['vendor'] == 'Intel':
                cpu_info['supports_quicksync'] = True
                cpu_info['supports_vaapi'] = True
            else:
                cpu_info['supports_quicksync'] = False
                cpu_info['supports_vaapi'] = False
                
            return cpu_info
            
        except Exception as e:
            print(f"Error detecting CPU: {e}")
            return cpu_info
    
    def _detect_memory(self):
        """Universal memory detection"""
        try:
            mem = psutil.virtual_memory()
            return {
                'total_gb': round(mem.total / (1024**3), 2),
                'available_gb': round(mem.available / (1024**3), 2),
                'percent_used': mem.percent,
                'performance_class': 'High' if mem.total >= 16*(1024**3) else 'Medium' if mem.total >= 8*(1024**3) else 'Low'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _detect_gpu(self):
        """Universal GPU detection for Intel, AMD, and NVIDIA"""
        gpu_info = {
            'nvidia_available': False,
            'intel_available': False,
            'amd_available': False,
            'devices': [],
            'vaapi_support': False
        }
        
        # Check NVIDIA GPU
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 3:
                            gpu_info['nvidia_available'] = True
                            gpu_info['devices'].append({
                                'vendor': 'NVIDIA',
                                'name': parts[0],
                                'memory_mb': int(parts[1].split()[0]),
                                'driver_version': parts[2],
                                'supports_inference': False,  # OpenVINO limitation
                                'supports_decode': True,
                                'recommended_mode': 'HYBRID'  # GPU decode + CPU inference
                            })
        except:
            pass
        
        # Check VAAPI support (Intel/AMD)
        try:
            result = subprocess.run(['vainfo'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                vainfo_output = result.stdout.lower()
                gpu_info['vaapi_support'] = True
                
                # Detect Intel GPU
                if 'intel' in vainfo_output:
                    gpu_info['intel_available'] = True
                    gpu_info['devices'].append({
                        'vendor': 'Intel',
                        'name': 'Intel Integrated Graphics',
                        'memory_mb': 0,  # Shared memory
                        'driver_version': 'VAAPI',
                        'supports_inference': True,  # OpenVINO native support
                        'supports_decode': True,
                        'recommended_mode': 'GPU'  # Both decode and inference
                    })
                
                # Detect AMD GPU
                elif any(keyword in vainfo_output for keyword in ['amd', 'radeon', 'mesa']):
                    gpu_info['amd_available'] = True
                    gpu_info['devices'].append({
                        'vendor': 'AMD',
                        'name': 'AMD GPU (VAAPI)',
                        'memory_mb': 0,  # Unknown
                        'driver_version': 'VAAPI',
                        'supports_inference': False,  # Limited OpenVINO support
                        'supports_decode': True,
                        'recommended_mode': 'HYBRID'  # GPU decode + CPU inference
                    })
        except:
            pass
        
        # Performance classification
        if gpu_info['intel_available']:
            gpu_info['performance_class'] = 'High'
            gpu_info['recommended_for_inference'] = True
            gpu_info['optimal_mode'] = 'GPU'
        elif gpu_info['nvidia_available'] or gpu_info['amd_available']:
            gpu_info['performance_class'] = 'Medium'
            gpu_info['recommended_for_inference'] = False
            gpu_info['optimal_mode'] = 'HYBRID'
        else:
            gpu_info['performance_class'] = 'None'
            gpu_info['recommended_for_inference'] = False
            gpu_info['optimal_mode'] = 'CPU'
            
        return gpu_info
    
    def _detect_storage(self):
        """Universal storage detection"""
        try:
            disk = psutil.disk_usage('/')
            return {
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'used_percent': round((disk.used / disk.total) * 100, 2)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _detect_capabilities(self):
        """Universal capability detection"""
        capabilities = {
            'recommended_device': 'CPU',
            'max_concurrent_streams': 1,
            'supports_hardware_decode': False,
            'thermal_throttling_risk': 'Unknown',
            'optimization_recommendations': []
        }
        
        cpu = self.system_info.get('cpu', {})
        gpu = self.system_info.get('gpu', {})
        memory = self.system_info.get('memory', {})
        
        # Determine recommended device based on available hardware
        if gpu.get('intel_available'):
            capabilities['recommended_device'] = 'GPU'
            capabilities['supports_hardware_decode'] = True
            capabilities['optimization_recommendations'].append("Intel GPU detected - optimal for OpenVINO")
        elif gpu.get('nvidia_available'):
            capabilities['recommended_device'] = 'HYBRID'
            capabilities['supports_hardware_decode'] = True
            capabilities['optimization_recommendations'].append("NVIDIA GPU detected - use for decode, CPU for inference")
        elif gpu.get('amd_available'):
            capabilities['recommended_device'] = 'HYBRID'
            capabilities['supports_hardware_decode'] = True
            capabilities['optimization_recommendations'].append("AMD GPU detected - use for decode, CPU for inference")
        else:
            capabilities['recommended_device'] = 'CPU'
            capabilities['optimization_recommendations'].append("No GPU detected - CPU-only processing")
        
        # Estimate max concurrent streams
        logical_cores = cpu.get('logical_cores', 4)
        memory_gb = memory.get('total_gb', 8)
        
        if capabilities['recommended_device'] == 'GPU':
            capabilities['max_concurrent_streams'] = min(8, max(4, logical_cores // 2))
        elif capabilities['recommended_device'] == 'HYBRID':
            capabilities['max_concurrent_streams'] = min(6, max(3, logical_cores // 3))
        else:
            capabilities['max_concurrent_streams'] = max(1, min(4, logical_cores // 4))
        
        # Thermal throttling risk assessment
        cpu_class = cpu.get('performance_class', 'Low')
        cpu_vendor = cpu.get('vendor', 'Unknown')
        max_freq = cpu.get('max_frequency_mhz', 0)
        
        if 'laptop' in cpu.get('model', '').lower() or max_freq < 3000:
            capabilities['thermal_throttling_risk'] = 'High'
            capabilities['optimization_recommendations'].append("Laptop CPU detected - monitor thermal throttling")
        elif cpu_class == 'High' and cpu_vendor in ['Intel', 'AMD']:
            capabilities['thermal_throttling_risk'] = 'Low'
        else:
            capabilities['thermal_throttling_risk'] = 'Medium'
            
        return capabilities
    
    def get_optimal_config(self, num_streams=4, dual_models=True):
        """Get optimal configuration for given workload"""
        config = {
            'device': self.system_info['capabilities']['recommended_device'],
            'expected_performance': 'Unknown',
            'recommendations': [],
            'warnings': []
        }
        
        cpu = self.system_info.get('cpu', {})
        gpu = self.system_info.get('gpu', {})
        capabilities = self.system_info['capabilities']
        
        # Performance estimation based on detected hardware
        max_streams = capabilities['max_concurrent_streams']
        if num_streams > max_streams:
            config['warnings'].append(f"Requesting {num_streams} streams but system optimal for {max_streams}")
        
        # Device-specific recommendations
        if config['device'] == 'GPU' and gpu.get('intel_available'):
            config['expected_performance'] = 'High (20-30 FPS per stream)'
            config['recommendations'].extend(capabilities['optimization_recommendations'])
        elif config['device'] == 'HYBRID':
            config['expected_performance'] = 'Medium-High (10-20 FPS per stream)'
            config['recommendations'].extend(capabilities['optimization_recommendations'])
        else:
            if capabilities['thermal_throttling_risk'] == 'High':
                config['expected_performance'] = 'Low (2-8 FPS per stream)'
                config['warnings'].append("High thermal throttling risk detected")
                config['recommendations'].append("Consider reducing concurrent streams or upgrading hardware")
            else:
                config['expected_performance'] = 'Medium (8-15 FPS per stream)'
        
        # Model-specific recommendations
        if dual_models:
            config['recommendations'].append("Consider single model for 2x performance improvement")
            
        return config
    
    def print_system_profile(self):
        """Print comprehensive universal system profile"""
        print("\n" + "="*70)
        print("UNIVERSAL SYSTEM HARDWARE PROFILE")
        print("="*70)
        
        # CPU Info
        cpu = self.system_info.get('cpu', {})
        print(f"\n🖥️  CPU Information:")
        print(f"   Vendor: {cpu.get('vendor', 'Unknown')}")
        print(f"   Model: {cpu.get('model', 'Unknown')}")
        print(f"   Cores: {cpu.get('physical_cores', 'Unknown')} physical, {cpu.get('logical_cores', 'Unknown')} logical")
        print(f"   Frequency: {cpu.get('current_frequency_mhz', 'Unknown')} MHz (max: {cpu.get('max_frequency_mhz', 'Unknown')} MHz)")
        print(f"   Performance Class: {cpu.get('performance_class', 'Unknown')}")
        print(f"   QuickSync Support: {cpu.get('supports_quicksync', False)}")
        
        # Memory Info
        memory = self.system_info.get('memory', {})
        print(f"\n💾 Memory Information:")
        print(f"   Total: {memory.get('total_gb', 'Unknown')} GB")
        print(f"   Available: {memory.get('available_gb', 'Unknown')} GB")
        print(f"   Performance Class: {memory.get('performance_class', 'Unknown')}")
        
        # GPU Info
        gpu = self.system_info.get('gpu', {})
        print(f"\n🎮 GPU Information:")
        print(f"   VAAPI Support: {gpu.get('vaapi_support', False)}")
        if gpu.get('devices'):
            for device in gpu['devices']:
                print(f"   {device['vendor']}: {device['name']}")
                print(f"     Decode Support: {device['supports_decode']}")
                print(f"     Inference Support: {device['supports_inference']}")
                print(f"     Recommended Mode: {device['recommended_mode']}")
                if device['memory_mb'] > 0:
                    print(f"     Memory: {device['memory_mb']} MB")
        else:
            print("   No GPU detected")
        print(f"   Performance Class: {gpu.get('performance_class', 'None')}")
        print(f"   Optimal Mode: {gpu.get('optimal_mode', 'CPU')}")
        
        # Capabilities
        capabilities = self.system_info.get('capabilities', {})
        print(f"\n⚡ System Capabilities:")
        print(f"   Recommended Device: {capabilities.get('recommended_device', 'Unknown')}")
        print(f"   Max Concurrent Streams: {capabilities.get('max_concurrent_streams', 'Unknown')}")
        print(f"   Hardware Decode Support: {capabilities.get('supports_hardware_decode', False)}")
        print(f"   Thermal Throttling Risk: {capabilities.get('thermal_throttling_risk', 'Unknown')}")
        
        print(f"\n💡 Optimization Recommendations:")
        for rec in capabilities.get('optimization_recommendations', []):
            print(f"   • {rec}")
        
        print("\n" + "="*70)

class EnhancedBenchmarkMonitor:
    def __init__(self, kafka_broker="kafka:9092", topic="dlstreamer_output"):
        self.kafka_broker = kafka_broker
        self.topic = topic
        self.benchmark_dir = "/benchmark_results"
        
        # Initialize universal system profiler
        self.profiler = UniversalSystemProfiler()
        
        # Print system profile
        self.profiler.print_system_profile()
        
        # Get optimal configuration
        self.optimal_config = self.profiler.get_optimal_config(num_streams=4, dual_models=True)
        print(f"\n🎯 Optimal Configuration for 4 streams with dual models:")
        print(f"   Device: {self.optimal_config['device']}")
        print(f"   Expected Performance: {self.optimal_config['expected_performance']}")
        for rec in self.optimal_config['recommendations']:
            print(f"   💡 {rec}")
        for warn in self.optimal_config['warnings']:
            print(f"   ⚠️  {warn}")
        
        # Performance tracking per camera
        self.camera_metrics = defaultdict(lambda: {
            'frame_count': 0,
            'start_time': None,
            'last_update': None,
            'fps_history': deque(maxlen=60),
            'cpu_history': deque(maxlen=60),
            'memory_history': deque(maxlen=60),
            'inference_times': deque(maxlen=100),
            'total_frames': 0,
            'active': False,
            'first_frame_time': None,
            'last_frame_time': None
        })
        
        # System monitoring
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            print(f"Docker client initialization failed: {e}")
            self.docker_client = None
            
        self.dlstreamer_container = None
        
        # Create benchmark directory
        os.makedirs(self.benchmark_dir, exist_ok=True)
        
        print(f"\n📊 Enhanced Universal Benchmark Monitor initialized")
        print(f"Kafka: {kafka_broker}, Topic: {topic}")
        print(f"Results will be saved to: {self.benchmark_dir}")

    # [Rest of the benchmark monitor methods remain the same as in the previous version]
    # ... (include all the other methods from the previous benchmark_monitor.py)

if __name__ == "__main__":
    monitor = EnhancedBenchmarkMonitor()
    monitor.run()
