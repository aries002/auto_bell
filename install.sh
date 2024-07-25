mkdir ~/.config/systemd/user
cp ./auto_bell.service ~/.config/systemd/user/

/usr/bin/python3 ./install.py

systemctl --user daemon-reload
systemctl --user enable auto_bell.service
systemctl --user  start auto_bell.service

