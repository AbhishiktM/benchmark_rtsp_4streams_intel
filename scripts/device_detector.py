#!/usr/bin/env python3
"""
Auto-detect optimal device configuration for DLStreamer
"""

import os
import subprocess
import psutil

class DeviceDetector:
    def __init__(self):
        self.system_info = self._detect_system()
    
    def _detect_system(self):
        """Detect system hardware capabilities"""
        return {
            'cpu': self._detect_cpu(),
            'gpu': self._detect_gpu(),
            'memory': self._detect_memory()
        }
    
    def _detect_cpu(self):
        """Detect CPU specifications"""
        cpu_info = {
            'cores': psutil.cpu_count(logical=True),
            'frequency': psutil.cpu_freq().max if psutil.cpu_freq() else 0,
            'model': 'Unknown'
        }
        
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        cpu_info['model'] = line.split(':')[1].strip()
                        break
        except:
            pass
            
        return cpu_info
    
    def _detect_gpu(self):
        """Detect GPU capabilities"""
        gpu_info = {
            'nvidia_available': False,
            'intel_available': False,
            'devices': []
        }
        
        # Check NVIDIA
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_info['nvidia_available'] = True
                gpu_info['devices'].append({
                    'vendor': 'NVIDIA',
                    'name': result.stdout.strip()
                })
        except:
            pass
        
        # Check Intel
        try:
            result = subprocess.run(['vainfo'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'H264' in result.stdout:
                gpu_info['intel_available'] = True
                gpu_info['devices'].append({
                    'vendor': 'Intel',
                    'name': 'Intel Integrated Graphics'
                })
        except:
            pass
            
        return gpu_info
    
    def _detect_memory(self):
        """Detect memory specifications"""
        mem = psutil.virtual_memory()
        return {
            'total_gb': round(mem.total / (1024**3), 2),
            'available_gb': round(mem.available / (1024**3), 2)
        }
    
    def get_optimal_config(self, num_streams=4, dual_models=True):
        """Get optimal configuration for workload"""
        config = {
            'device': 'CPU',
            'expected_performance': 'Unknown',
            'recommendations': [],
            'warnings': []
        }
        
        cpu = self.system_info['cpu']
        gpu = self.system_info['gpu']
        
        # Device selection logic
        if gpu['nvidia_available']:
            config['device'] = 'HYBRID'
            config['expected_performance'] = 'High (20-30 FPS per stream)'
            config['recommendations'].append("NVIDIA GPU detected - optimal for decode")
        elif gpu['intel_available']:
            config['device'] = 'GPU'
            config['expected_performance'] = 'Medium-High (15-25 FPS per stream)'
            config['recommendations'].append("Intel GPU detected - good for OpenVINO")
        else:
            config['device'] = 'CPU'
            if cpu['cores'] >= 16 and cpu['frequency'] >= 3000:
                config['expected_performance'] = 'Medium (8-15 FPS per stream)'
            else:
                config['expected_performance'] = 'Low (2-8 FPS per stream)'
                config['warnings'].append("Limited CPU performance detected")
        
        # Workload-specific recommendations
        if num_streams > 4:
            config['warnings'].append(f"High stream count ({num_streams}) may impact performance")
        
        if dual_models:
            config['recommendations'].append("Consider single model for 2x performance")
            
        return config

if __name__ == "__main__":
    detector = DeviceDetector()
    config = detector.get_optimal_config()
    
    print("Auto-Device Detection Results:")
    print(f"Optimal Device: {config['device']}")
    print(f"Expected Performance: {config['expected_performance']}")
    
    for rec in config['recommendations']:
        print(f"* {rec}")
    for warn in config['warnings']:
        print(f"WARNING: {warn}")
