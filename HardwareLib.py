import psutil
import subprocess
import json
import platform

class HardwareLib:
    def __init__(self):
        self.cpuProber = Linux_CPU_Prober()
        self.gpuProber = Linux_GPU_Prober()
        self.upsProber = Linux_UPS_Prober()
        print(f"Hardware Info: Platform established as {platform.system()} running on {self.cpuProber.cpuModel} CPU with {self.gpuProber.gpuModel} GPU.")
        if self.upsProber.upsPresent:
            print(f"Hardware Info: UPS is present.")
        else:
            print(f"Hardware Info: UPS is not present.")

    # GPU
    def get_gpu_temp(self):
        return self.gpuProber.get_gpu_temp()

    def get_gpu_usage(self):
        return self.gpuProber.get_gpu_usage()

    # CPU
    def get_cpu_usage(self):
        return self.cpuProber.get_cpu_usage()

    def get_cpu_temp(self):
        return self.cpuProber.get_cpu_temp()
    
    # UPS
    def get_current_load(self):
        return self.upsProber.get_current_load()
    
class Linux_UPS_Prober:
    
    def __init__(self):
        try:
            self.upsWattage = float(subprocess.run(["/usr/bin/apcaccess", "-up", "NOMPOWER"], text=True, capture_output=True).stdout.strip())
            self.upsPresent = True
            print(f"Detected {self.upsWattage} Watt UPS")
        except:
            self.upsWattage = None
            self.upsPresent = False
    
    def get_current_load(self):
        if self.upsPresent:
            upsLoad = float(subprocess.run(["apcaccess", "-up", "LOADPCT"], text=True, capture_output=True).stdout.strip())
            return (upsLoad / 100)*self.upsWattage
        else:
            return None

class Linux_CPU_Prober:
    
    def __init__(self):
        try:
            temperatures = psutil.sensors_temperatures()
            temp = temperatures['coretemp'][0][1]
            self.cpuModel = "Intel"
        except:
            try:
                temperatures = psutil.sensors_temperatures()
                temp = temperatures['k10temp'][0][1]
                self.cpuModel = "AMD"
            except:
                self.cpuModel = None
        print(f"Detected {self.cpuModel} CPU")
    
    def get_cpu_usage(self):
        try:
            return int(psutil.cpu_percent(interval=1))
        except:
            return None
            
    def get_cpu_temp(self):
        try:
            temperatures = psutil.sensors_temperatures()
            if self.cpuModel == "Intel":
                temp = temperatures['coretemp'][0][1]
            elif self.cpuModel == "AMD":
                temp = temperatures['k10temp'][0][1]
            return int(temp)
        except:
            return None
    
class Linux_GPU_Prober:

    def __init__(self):
        if self.get_nvidia_gpu_temp():
            self.gpuModel = "Nvidia"
        elif self.get_amd_gpu_temp():
            self.gpuModel = "AMD"
        elif self.get_intel_gpu_temp():
            self.gpuModel = "Intel"
        else:
            self.gpuModel = None
        print(f"Detected {self.gpuModel} GPU")

    def get_nvidia_gpu_temp(self):
        try:
            result = subprocess.run(['/usr/bin/nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            temp = result.stdout.decode('utf-8').strip()
            return int(temp)
        except:
            return None

    def get_nvidia_gpu_usage(self):
        import subprocess
        try:
            result = subprocess.run(['/usr/bin/nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            usage = result.stdout.decode('utf-8').strip()
            return int(usage)
        except:
            return None

    def get_amd_gpu_temp(self):
        try:
            temperatures = psutil.sensors_temperatures()
            return int(temperatures['amdgpu'][0][1])
        except:
            return get_amd_gpu_temp_backup()


    def get_amd_gpu_temp_backup(self):
        try:
            result = subprocess.run(['/opt/rocm/bin/rocm-smi', '--showtemp'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            output = result.stdout.decode('utf-8')
            # Parse the output to find the temperature
            for line in output.splitlines():
                if "Temperature" in line:
                    # Example output line: "Temperature: 45 C"
                    temp = int(line.split(":")[1].strip().split(" ")[0])
                    print(f"Using AMD backup method")
                    return temp
        except:
            return None
            
    def get_amd_gpu_usage(self):
        import subprocess
        import json
        try:
            result = subprocess.run(['/opt/rocm/bin/rocm-smi', '--showuse', '--json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            output = json.loads(result.stdout.decode('utf-8').strip())
            return int(output['card0']['GPU use (%)'])
            # Parse the output to find the usage
        except:
            return None

    def get_intel_gpu_temp(self):
        try:
            result = subprocess.run(['intel_gpu_top', '-l', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            output = result.stdout.decode('utf-8')
            # Parse the output for temperature line
            for line in output.splitlines():
                if "temperature" in line:
                    # Example: temperature = 45 C
                    temp = int(line.split(":")[1].strip().split(" ")[0])
                    return temp
        except:
            return None
            
    def get_intel_gpu_usage(self):
        import subprocess
        try:
            result = subprocess.run(['intel_gpu_top', '-b', '-l', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            output = result.stdout.decode('utf-8')
            # Parse the output for utilization
            for line in output.splitlines():
                if "Usage" in line:
                    # Example: Usage: 45%
                    usage = int(line.split(":")[1].strip().replace('%', '').strip())
                    return usage
        except:
            return None

    def get_gpu_temp(self):
        match self.gpuModel:
            case "Nvidia":
                return self.get_nvidia_gpu_temp()
            case "AMD":
                return self.get_amd_gpu_temp()
            case "Intel":
                return self.get_intel_gpu_temp()
            case _:
                return None
                
    def get_gpu_usage(self):
        match self.gpuModel:
            case "Nvidia":
                return self.get_nvidia_gpu_usage()
            case "AMD":
                return self.get_amd_gpu_usage()
            case "Intel":
                return self.get_intel_gpu_usage()
            case _:
                return None
