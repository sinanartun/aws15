# Live monitoring

```
watch -n 1 nvidia-smi
```


# Check CUDA

```
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv
echo $CUDA_VISIBLE_DEVICES
```



sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/network.conf >/dev/null <<'EOF'
[Service]
Environment=OLLAMA_HOST=0.0.0.0
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama