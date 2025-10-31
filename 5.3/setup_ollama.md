# 1. Prepare folders


```
sudo mkdir -p /home/ec2-user/app/ollama
sudo chown -R ec2-user:ec2-user /home/ec2-user/app/ollama
```


# 2. Download Ollama 
Download Ollama  manually instead of using the install script
The default install script hardcodes /usr/local.
We’ll extract it to your desired directory manually.


```
cd /home/ec2-user/app/ollama
curl -fsSL https://ollama.com/download/Ollama-linux-amd64.tgz -o ollama.tgz
tar -xzf ollama.tgz
rm ollama.tgz
```


```
find /home/ec2-user/app/ollama -type d | sed 's|[^/]*/|│   |g;s|│   \([^│]\)|├── \1|'

```

```
/home/ec2-user/app/ollama/
│   │   │   ├── ollama
│   │   │   │   ├── bin
│   │   │   │   ├── lib
│   │   │   │   │   ├── ollama
│   │   │   │   │   │   ├── cuda_v12
│   │   │   │   │   │   ├── cuda_v13

```


# 3. Add Ollama to your PATH

So the ollama command is available globally.


```
echo 'export PATH="/home/ec2-user/app/ollama/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

```

```
which ollama

```
```~/app/ollama/bin/ollama```


# 4. Configure data directory (models, configs, etc.)

By default, Ollama stores models under /usr/share/ollama or ~/.ollama.
Let’s move all model/data storage to your /home/ec2-user/app mount:

```
mkdir -p /home/ec2-user/app/ollama-data
echo 'export OLLAMA_MODELS="/home/ec2-user/app/ollama-data"' >> ~/.bashrc
echo 'export OLLAMA_HOME="/home/ec2-user/app/ollama-data"' >> ~/.bashrc
source ~/.bashrc

```

# 5. Run this once before starting:
```
mkdir -p /home/ec2-user/app/ollama-data/models
sudo chown -R ec2-user:ec2-user /home/ec2-user/app/ollama /home/ec2-user/app/ollama-data
```

# 6. Start Ollama as a background service (optional)
```
sudo tee /etc/systemd/system/ollama.service > /dev/null <<'EOF'
[Unit]
Description=Ollama Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/app/ollama
ExecStart=/home/ec2-user/app/ollama/bin/ollama serve

# Environment variables
Environment="OLLAMA_HOME=/home/ec2-user/app/ollama-data"
Environment="OLLAMA_MODELS=/home/ec2-user/app/ollama-data/models"
Environment="OLLAMA_HOST=0.0.0.0"

# Service behavior
Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now ollama

```
Check service status:
```
systemctl status ollama

```


```
● ollama.service - Ollama Service
     Loaded: loaded (/etc/systemd/system/ollama.service; enabled; preset: disabled)
     Active: 🟢 Active (running) since Fri 2025-10-31 16:42:37 UTC
   Main PID: 63490 (ollama)
      Tasks: 12 (limit: 76062)
     Memory: 13.2M
        CPU: 947ms
     CGroup: /system.slice/ollama.service
             └─63490 /home/ec2-user/app/ollama/bin/ollama serve
```



```
ss -tulpen | grep 11434
```