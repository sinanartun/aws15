```
sudo dnf install -y docker
```






```
sudo usermod -aG docker ec2-user
```

```
sudo systemctl enable --now docker
```
```
systemctl status docker
```

```
sudo systemctl stop docker

```


```
sudo mkdir -p /home/ec2-user/app/docker
sudo chown -R root:root /home/ec2-user/app/docker

```


```
docker run -d -p 3000:8080 --gpus all --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:cuda
```