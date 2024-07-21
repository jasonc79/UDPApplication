#! /usr/bin/env python3

"""
Mimicing a simplified version of DNS

"""
import datetime
import socket
import sys
import threading
import random
import time
from dns import Dns
def main():
    if (len(sys.argv) != 2):
        sys.exit(f"Usage: python3 server.py <server_port>")
    try:
        server_port = int(sys.argv[1])
    except ValueError:
        sys.exit('Error: server_port must be an integer')
    
    dns = Dns("master.txt")
    server = Server(server_port, dns)
    try:
        server.run()
    except KeyboardInterrupt:
        print(f'\nExiting...')


class Server:
    def __init__(self, server_port: int, dns: Dns) -> None:
        self.server_port = server_port
        self.dns = dns
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', self.server_port))

    def run(self):
        print(f'Server running on port {self.server_port}...')
        print('Press Ctrl+C to exit.')
        while True:
            data, addr = self.sock.recvfrom(1024)
            child = threading.Thread(target=self._process_request, args=(data, addr))
            child.start()

    def _process_request(self, data: bytes, addr: tuple[str, int]) -> None:
        """The main server logic, which processes the incoming request and sends
           the response back to the client.

           Additional error checking should be added here, to handle invalid
           requests, but this has been omitted for simplicity.

        Args:
            data (bytes): The incoming request data.
            addr (tuple[str, int]): The address of the client.
        """
        request = data.decode().split('\n')
        domain_name = request[0]
        type = request[1]
        timeout = request[2]
        id = request[3]
        sent_time = datetime.datetime.now()
        time.sleep(random.randint(0, 4))
        response = self.dns.process_query(domain_name, type, id)
        # Log the request and response to the terminal
        response_time = datetime.datetime.now()
        delay = response_time.timestamp() - sent_time.timestamp()
        ip, port = addr
        print(f'[{sent_time}] rcv {port}: {id} {domain_name} {type} (delay: {delay}s)')
        print(f'[{response_time}] snd {port}: {id} {domain_name} {type}')
        self.sock.sendto(response.encode(), addr)


if __name__ == '__main__':
    main()