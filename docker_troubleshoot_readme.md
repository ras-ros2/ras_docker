## Docker Setup (Permission Access)

### 1. Add Your User to the Docker Group
To run Docker commands without `sudo`, add your user to the `docker` group:
```bash
sudo usermod -aG docker $USER
```
Log out and log back in or apply changes immediately:
```bash
newgrp docker
```
Now, test with:
```bash
docker ps
```
If it works without `sudo`, the docker setup is successful.
### 2. Use `sudo` for Docker Commands (Alternative)
If you prefer not to modify group permissions, always run Docker commands with `sudo`:
```bash
sudo docker ps
```

### 3. Check Docker Daemon Permissions
Check permissions of the Docker socket file:
```bash
ls -l /var/run/docker.sock
```
It output should look like the following:
```bash
srw-rw---- 1 root docker 0 <current_date> <current_time> /var/run/docker.sock
```
Fix permissions if incorrect:
```bash
sudo chown root:docker /var/run/docker.sock
sudo chmod 660 /var/run/docker.sock
```

### 4. Restart Docker Service
Restart Docker after making changes:
```bash
sudo systemctl restart docker
```

### 5. Check Docker Daemon Status
Ensure Docker is running:
```bash
sudo systemctl status docker
```
If not running, start it:
```bash
sudo systemctl start docker
```
 - run the following command to check the status of the `docker images`:
 ```bash
 docker images
 ```
 If this command returns output, it means the docker images are currently loaded. If it returns nothing, the docker images are not in use.
 
 - run the following command to check for the status of the `docker containers`:
 ```bash
 docker ps
 ```
 If this command returns output, it means the docker container is currently loaded. If it returns nothing, the docker container is not in use.
