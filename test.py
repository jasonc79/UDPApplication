import subprocess
import time
port = 54789
domain_name = "www.metalhead.com."
query_type = "A"
timeout = 5
num_clients = 10

for i in range(num_clients):
    print(f"Launching client {i + 1}")
    subprocess.Popen(['python3', 'client.py', str(port), domain_name, query_type, str(timeout)])
    # time.sleep(0.1)  # Optional: small delay to stagger the launches slightly

print(f"Launched {num_clients} client processes.")