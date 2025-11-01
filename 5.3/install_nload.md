```
sudo dnf install -y gcc make autoconf automake libtool ncurses-devel git
cd /tmp
git clone https://github.com/rolandriegel/nload.git
cd nload
autoreconf -i
./configure
make
sudo make install
```