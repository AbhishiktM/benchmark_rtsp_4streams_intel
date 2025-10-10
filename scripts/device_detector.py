#!/usr/bin/env python3
"""
Enhanced Auto-detect optimal device configuration for DLStreamer
Specifically detects Intel Arc GPU vs Intel iGPU
"""

import os
import subprocess
import psutil
import sys

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
            'cores': psutil.cpu_count(logical=False) or 4,
            'logical_cores': psutil.cpu_count(logical=True) or 8,
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
        """Detect GPU capabilities with Intel Arc specific detection"""
        gpu_info = {
            'nvidia_available': False,
            'intel_arc_available': False,
            'intel_igpu_available': False,
            'amd_available': False,
            'devices': [],
            'recommended_device': 'CPU',
            'arc_device_path': None  # ✅ Add this
        }
        
        # Check for Intel Arc GPU specifically
        intel_arc_detected = self._detect_intel_arc()
        if intel_arc_detected:
            gpu_info['intel_arc_available'] = True
            gpu_info['arc_device_path'] = '/dev/dri/renderD129'  # ✅ Add this
            gpu_info['devices'].append({
                'vendor': 'Intel',
                'type': 'Arc',
                'name': intel_arc_detected,
                'device_path': '/dev/dri/renderD129'  # ✅ Add this
            })
            gpu_info['recommended_device'] = 'GPU'
            return gpu_info    
        # Check for Intel iGPU (integrated graphics)
        intel_igpu_detected = self._detect_intel_igpu()
        if intel_igpu_detected:
            gpu_info['intel_igpu_available'] = True
            gpu_info['devices'].append({
                'vendor': 'Intel',
                'type': 'iGPU',
                'name': intel_igpu_detected
            })
            gpu_info['recommended_device'] = 'GPU'
            return gpu_info
        
        # Check NVIDIA
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                gpu_info['nvidia_available'] = True
                gpu_info['devices'].append({
                    'vendor': 'NVIDIA',
                    'type': 'dGPU',
                    'name': result.stdout.strip()
                })
                gpu_info['recommended_device'] = 'HYBRID'
        except:
            pass
        
        # Check AMD
        try:
            result = subprocess.run(['vainfo'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'AMD' in result.stdout:
                gpu_info['amd_available'] = True
                gpu_info['devices'].append({
                    'vendor': 'AMD',
                    'type': 'dGPU',
                    'name': 'AMD GPU'
                })
                gpu_info['recommended_device'] = 'HYBRID'
        except:
            pass
            
        return gpu_info
    
    def _detect_intel_arc(self):
        """Specifically detect Intel Arc GPU"""
        try:
            # Method 1: Check lspci for DG2 (Arc codename) or device 5690
            result = subprocess.run(['lspci', '-nn'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'VGA' in line or 'Display' in line:
                        line_lower = line.lower()
                        # Intel Arc A770 has device ID 5690
                        if '5690' in line or 'dg2' in line_lower or 'arc' in line_lower:
                            if 'a770' in line_lower or '5690' in line:
                                return 'Intel Arc A770'
                            elif 'a750' in line_lower:
                                return 'Intel Arc A750'
                            elif 'a580' in line_lower:
                                return 'Intel Arc A580'
                            elif 'a380' in line_lower:
                                return 'Intel Arc A380'
                            else:
                                return 'Intel Arc GPU'
            
            # Method 2: Check vainfo for AV1 encode support (Arc-specific)
            # Use renderD129 for Arc A770 (renderD128 is iGPU)
            env = os.environ.copy()
            env['LIBVA_DEVICE'] = '/dev/dri/renderD129'
            
            result = subprocess.run(['vainfo'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5,
                                  env=env)
            if result.returncode == 0:
                output = result.stdout
                # Arc GPUs support AV1 decode, older iGPUs don't
                if 'VAProfileAV1Profile0' in output and 'VAEntrypointVLD' in output:
                    return 'Intel Arc GPU (detected via AV1 support on renderD129)'
            
            return None
            
        except Exception as e:
            return None

    
    def _detect_intel_igpu(self):
        """Detect Intel integrated GPU (not Arc)"""
        try:
            # Check vainfo for Intel GPU
            result = subprocess.run(['vainfo'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout
                if 'intel' in output.lower() and 'ihd' in output.lower():
                    # Check if it's NOT Arc (no AV1 encode support)
                    if 'VAProfileAV1' not in output or 'VAEntrypointEncSlice' not in output:
                        # Try to get GPU generation from lspci
                        lspci_result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
                        if lspci_result.returncode == 0:
                            for line in lspci_result.stdout.split('\n'):
                                if 'VGA' in line and 'Intel' in line:
                                    if 'UHD' in line:
                                        return 'Intel UHD Graphics (iGPU)'
                                    elif 'Iris' in line:
                                        return 'Intel Iris Graphics (iGPU)'
                                    elif 'HD' in line:
                                        return 'Intel HD Graphics (iGPU)'
                        
                        return 'Intel Integrated Graphics (iGPU)'
            
            return None
            
        except Exception as e:
            return None
    
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
        
        # Device selection logic with Intel Arc priority
        if gpu['intel_arc_available']:
            config['device'] = 'GPU'
            config['expected_performance'] = 'Excellent (25-35 FPS per stream)'
            config['recommendations'].append("Intel Arc GPU detected - OPTIMAL for OpenVINO")
            config['recommendations'].append("Hardware acceleration for decode and inference")
            
        elif gpu['intel_igpu_available']:
            config['device'] = 'GPU'
            config['expected_performance'] = 'Good (15-25 FPS per stream)'
            config['recommendations'].append("Intel iGPU detected - Good for OpenVINO")
            config['recommendations'].append("Consider upgrading to Intel Arc for better performance")
            
        elif gpu['nvidia_available']:
            config['device'] = 'HYBRID'
            config['expected_performance'] = 'Medium (10-20 FPS per stream)'
            config['recommendations'].append("NVIDIA GPU detected - Use for decode only")
            config['warnings'].append("OpenVINO doesn't support NVIDIA for inference")
            config['recommendations'].append("Consider adding Intel Arc GPU for 2-3x performance")
            
        elif gpu['amd_available']:
            config['device'] = 'HYBRID'
            config['expected_performance'] = 'Medium (8-18 FPS per stream)'
            config['recommendations'].append("AMD GPU detected - Use for decode only")
            config['warnings'].append("OpenVINO has limited AMD support")
            config['recommendations'].append("Consider adding Intel Arc GPU for 3-4x performance")
            
        else:
            config['device'] = 'CPU'
            if cpu['cores'] >= 16 and cpu['frequency'] >= 3000:
                config['expected_performance'] = 'Medium (8-15 FPS per stream)'
            elif cpu['cores'] >= 8:
                config['expected_performance'] = 'Low-Medium (4-10 FPS per stream)'
            else:
                config['expected_performance'] = 'Low (2-6 FPS per stream)'
                config['warnings'].append("Limited CPU performance detected")
            
            config['recommendations'].append("CPU-only processing - Consider adding Intel Arc GPU")
        
        # Workload-specific recommendations
        if num_streams > 4:
            config['warnings'].append(f"High stream count ({num_streams}) may impact performance")
        
        if dual_models:
            config['recommendations'].append("Dual models active - Consider single model for 2x FPS")
            
        return config
    
    def print_detailed_info(self):
        """Print detailed system information"""
        print("\n" + "="*70)
        print("DETAILED HARDWARE DETECTION")
        print("="*70)
        
        # CPU Info
        cpu = self.system_info['cpu']
        print(f"\n🖥️  CPU:")
        print(f"   Model: {cpu['model']}")
        print(f"   Cores: {cpu['cores']} physical, {cpu['logical_cores']} logical")
        print(f"   Max Frequency: {cpu['frequency']:.0f} MHz")
        
        # Memory Info
        mem = self.system_info['memory']
        print(f"\n💾 Memory:")
        print(f"   Total: {mem['total_gb']} GB")
        print(f"   Available: {mem['available_gb']} GB")
        
        # GPU Info
        gpu = self.system_info['gpu']
        print(f"\n🎮 GPU Detection:")
        
        if gpu['intel_arc_available']:
            print(f"   ✅ Intel Arc GPU: DETECTED")
            for device in gpu['devices']:
                if device['type'] == 'Arc':
                    print(f"      Model: {device['name']}")
            print(f"   Status: OPTIMAL for OpenVINO")
            
        elif gpu['intel_igpu_available']:
            print(f"   ✅ Intel iGPU: DETECTED")
            for device in gpu['devices']:
                if device['type'] == 'iGPU':
                    print(f"      Model: {device['name']}")
            print(f"   Status: GOOD for OpenVINO")
            
        elif gpu['nvidia_available']:
            print(f"   ⚠️  NVIDIA GPU: DETECTED")
            for device in gpu['devices']:
                if device['vendor'] == 'NVIDIA':
                    print(f"      Model: {device['name']}")
            print(f"   Status: HYBRID mode (decode only)")
            
        elif gpu['amd_available']:
            print(f"   ⚠️  AMD GPU: DETECTED")
            print(f"   Status: HYBRID mode (decode only)")
            
        else:
            print(f"   ❌ No GPU detected")
            print(f"   Status: CPU-only processing")
        
        print(f"\n🎯 Recommended Device: {gpu['recommended_device']}")
        print("="*70 + "\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Detect optimal device for DLStreamer')
    parser.add_argument('--verbose', action='store_true', help='Print detailed information')
    args = parser.parse_args()
    
    detector = DeviceDetector()
    
    if args.verbose:
        detector.print_detailed_info()
    
    config = detector.get_optimal_config()
    
    # Print in format expected by process_video.sh
    print(f"DEVICE={config['device']}")
    print(f"INFO={config['expected_performance']}")
    print(f"STATUS={'OPTIMAL' if 'Arc' in str(detector.system_info['gpu']) else 'GOOD' if 'intel' in str(detector.system_info['gpu']).lower() else 'FALLBACK'}")
    
    if args.verbose:
        print("\n📊 Configuration:")
        print(f"   Expected Performance: {config['expected_performance']}")
        
        if config['recommendations']:
            print("\n💡 Recommendations:")
            for rec in config['recommendations']:
                print(f"   • {rec}")
        
        if config['warnings']:
            print("\n⚠️  Warnings:")
            for warn in config['warnings']:
                print(f"   • {warn}")
