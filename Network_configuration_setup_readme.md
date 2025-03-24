## Configure the Network for Server-Robot communication
Before running the server and robot, configure `ras_conf.yaml`:
```bash
nano ras_docker/configs/ras_conf.yaml
```
Update transport settings based on your network setup:

### 1. Using a Remote IP (Cloud Server)
```yaml
ras:
  transport:
    implementation: default
    file_server:
      use_external: true
      ip: dev2.deepklarity.ai (for example)
      port: 9501
    mqtt:
      use_external: true
      ip: dev2.deepklarity.ai (for example)
      port: 9500
```
### 2. Using a Local Wi-Fi Network
```yaml
ras:
  transport:
    implementation: default
    file_server:
      use_external: false
      ip: <YOUR_WIFI_IP>
      port: 2122
    mqtt:
      use_external: false
      ip: <YOUR_WIFI_IP>
      port: 2383
```
### 3. Running on the Same Machine (Localhost)
```yaml
ras:
  transport:
    implementation: default
    file_server:
      use_external: false
      ip: localhost
      port: 2122
    mqtt:
      use_external: false
      ip: localhost
      port: 2383
```
