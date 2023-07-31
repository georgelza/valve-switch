# Valve Switches

Python code to read mqtt topics and then toggle GPIO pins which in turn open/close Garden valves,

## Register Service

1. copy <file>.service  /etc/systemd/system/<file>.service
2. systemctl daemon-reload
3. systemctl start <file>
4. systemctl enable <file>
5. systemctl status example.service