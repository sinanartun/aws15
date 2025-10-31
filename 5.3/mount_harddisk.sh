#!/usr/bin/env bash
set -euo pipefail

DEVICE="/dev/nvme1n1"
MOUNTPOINT="/home/ec2-user/app"
FSTYPE="xfs"
MOUNT_OPTS="defaults,nofail,noatime,x-systemd.device-timeout=10s"
LABEL_NAME="appdata"   # optional

# 0) Pre-flight
command -v mkfs.xfs >/dev/null 2>&1 || sudo dnf install -y xfsprogs
sudo mkdir -p "$MOUNTPOINT"

# 1) Create FS if missing (DANGER: mkfs wipes data)
if ! sudo blkid -s TYPE -o value "$DEVICE" >/dev/null 2>&1; then
  echo "[INFO] No filesystem on $DEVICE; creating $FSTYPE"
  sudo mkfs.xfs -f -L "$LABEL_NAME" "$DEVICE"
else
  curfs=$(sudo blkid -s TYPE -o value "$DEVICE" || true)
  echo "[INFO] $DEVICE already has filesystem: $curfs"
  if [[ "$curfs" != "$FSTYPE" ]]; then
    echo "[WARN] Expected $FSTYPE but found $curfs on $DEVICE. Aborting."
    exit 1
  fi
fi

# 2) Get UUID
UUID=$(sudo blkid -s UUID -o value "$DEVICE")

# 3) Update /etc/fstab (replace existing line for this mountpoint or device)
FSTAB_LINE="UUID=${UUID}  ${MOUNTPOINT}  ${FSTYPE}  ${MOUNT_OPTS}  0  0"
sudo cp /etc/fstab /etc/fstab.bak.$(date +%F-%H%M%S)
sudo awk -v dev="$DEVICE" -v mp="$MOUNTPOINT" '
  $1 ~ "^UUID=" || $1 ~ "^/dev/" {
    if ($2 == mp || $1 == dev) next  # drop old line for same mountpoint/device
  }
  { print }
' /etc/fstab.bak.$(date +%F-%H%M%S) | sudo tee /etc/fstab.tmp >/dev/null
echo "$FSTAB_LINE" | sudo tee -a /etc/fstab.tmp >/dev/null
sudo mv /etc/fstab.tmp /etc/fstab

# 4) Mount (remount if already mounted)
if mountpoint -q "$MOUNTPOINT"; then
  sudo umount "$MOUNTPOINT"
fi
sudo mount -a

# 5) Ownership
sudo chown ec2-user:ec2-user "$MOUNTPOINT"

# 6) Optional: enable weekly TRIM (good for EBS/SSD)
if systemctl list-unit-files | grep -q fstrim.timer; then
  sudo systemctl enable --now fstrim.timer || true
fi

# 7) Verify
df -h | grep -E "Filesystem|$MOUNTPOINT"
lsblk -f
echo "[OK] Mounted $DEVICE at $MOUNTPOINT with UUID=$UUID"
