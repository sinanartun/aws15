# Hard Disk Setup
```
sudo dnf update
sudo dnf upgrade --releasever=2023.9.20251027 -y
```

## Install Required Tools

```bash
sudo dnf install -y xfsprogs e2fsprogs
```

## Format and Mount the Disk

```bash
sudo mkfs.xfs -f /dev/nvme1n1
sudo mkdir -p /home/ec2-user/app
sudo mount /dev/nvme1n1 /home/ec2-user/app
sudo chown ec2-user:ec2-user /home/ec2-user/app
```

## Configure Persistent Mount

Get the UUID:

```bash
sudo blkid -s UUID -o value /dev/nvme1n1
```

Edit fstab:

```bash
sudo nano /etc/fstab
```

Add this line (replace `<UUID>` with the actual UUID):

```
UUID=<UUID>  /home/ec2-user/app  xfs  defaults,nofail,noatime  0  2
```

## Verify the Configuration

```bash
sudo umount /home/ec2-user/app
sudo mount -a
df -h | grep app
lsblk
```