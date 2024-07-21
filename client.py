import socket
import sys
import random

# Usage: python3 client.py server_port qname qtype timeout
# qtype = (A, NS, CNAME)

def main():
    if (len(sys.argv) != 5):
        sys.exit(f"Usage: python3 client.py <server_port> <qname> <qtype> <timeout>")
    server_port = int(sys.argv[1])
    qname = sys.argv[2]
    qtype = sys.argv[3]
    timeout = int(sys.argv[4])
    send_query(server_port, qname, qtype, timeout)

def send_query(server_port: int, qname: str, qtype: str, timeout: int):
    try:
        id = random.getrandbits(16)
        request = f'{qname}\n{qtype}\n{timeout}\n{id}'
        soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        soc.settimeout(timeout)
        soc.sendto(request.encode(), ('localhost', server_port))
        response, _ = soc.recvfrom(1024)
        print(response.decode())
    except socket.timeout:
        print(f"timeout\n")

if __name__ == '__main__':
    main()