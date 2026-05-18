import sys
import time
import socket
import random
import string
import threading
from colorama import Fore, init

init()

DARK_BLUE = Fore.BLUE
LIGHT_BLUE = Fore.LIGHTBLUE_EX
ERRORRED = Fore.LIGHTRED_EX

ASCII_ART = """
     ██╗██████╗     ██████╗ ██╗███╗   ██╗ ██████╗     ██╗   ██╗██████╗ 
     ██║██╔══██╗    ██╔══██╗██║████╗  ██║██╔════╝     ██║   ██║╚════██╗
     ██║██████╔╝    ██████╔╝██║██╔██╗ ██║██║  ███╗    ██║   ██║ █████╔╝
     ██║██╔═══╝     ██╔═══╝ ██║██║╚██╗██║██║   ██║    ╚██╗ ██╔╝██╔═══╝ 
     ██║██║         ██║     ██║██║ ╚████║╚██████╔╝     ╚████╔╝ ███████╗
     ╚═╝╚═╝         ╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝       ╚═══╝  ╚══════╝
                                                                  
"""

def slow_print(text, speed=0.05):
    for line in text.splitlines():
        sys.stdout.write(DARK_BLUE + line + '\n')
        sys.stdout.flush()
        time.sleep(0.05)

def generate_payload(mode, size):
    if mode == "1":
        return ''.join(random.choices(string.ascii_letters + string.digits, k=size)).encode()
    elif mode == "2":
        return b'\x00' * size
    elif mode == "3":
        return b'\xff' * size
    elif mode == "4":
        return ''.join(random.choices(string.ascii_uppercase, k=size)).encode()
    elif mode == "5":
        return ''.join(random.choices(string.punctuation, k=size)).encode()
    elif mode == "6":
        return bytes(random.getrandbits(8) for _ in range(size))
    else:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=size)).encode()

def scan_port(ip, port, open_ports, banner_dict):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.3)
    try:
        sock.connect((ip, port))
        open_ports.append(port)
        try:
            sock.sendall(b"HEAD / HTTP/1.1\r\n\r\n")
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip().split('\n')[0]
            if banner:
                banner_dict[port] = banner
        except:
            pass
    except:
        pass
    finally:
        sock.close()

def run_port_scan(ip, scan_type):
    sys.stdout.write(LIGHT_BLUE + f"\n [+] Scanning ports on {ip}...\n")
    sys.stdout.flush()
    
    if scan_type == "1":
        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 1433, 3306, 3389, 5000, 8080]
    elif scan_type == "2":
        ports = list(range(1, 1024))
    elif scan_type == "3":
        ports = [80, 443, 8080, 8443, 8000, 3000, 5000]
    else:
        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 1433, 3306, 3389, 5000, 8080]

    open_ports = []
    banner_dict = {}
    threads = []
    
    for port in ports:
        t = threading.Thread(target=scan_port, args=(ip, port, open_ports, banner_dict))
        threads.append(t)
        t.start()
        if len(threads) >= 100:
            for thread in threads:
                thread.join()
            threads = []
            
    for t in threads:
        t.join()
        
    if open_ports:
        sys.stdout.write(LIGHT_BLUE + " [+] Active ports discovered:\n")
        for port in sorted(open_ports):
            banner_info = f" | Banner: {banner_dict[port]}" if port in banner_dict else ""
            sys.stdout.write(LIGHT_BLUE + f"   - Port {port}{banner_info}\n")
    else:
        sys.stdout.write(ERRORRED + " [!] No responses discovered during port mapping.\n")
    sys.stdout.flush()

def worker_ping(thread_id, resolved_ip, port, total_packets, payload_size, timeout, delay, mode_choice, jitter_opt, stats_collector):
    payload = generate_payload(mode_choice, payload_size)
    consecutive_drops = 0
    max_consecutive_drops = 0
    
    packets_to_send = total_packets
    
    for i in range(1, packets_to_send + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        start_time = time.time()
        stats_collector['sent'] += 1
        
        try:
            sock.connect((resolved_ip, port))
            sock.sendall(payload)
            latency = (time.time() - start_time) * 1000
            stats_collector['latencies'].append(latency)
            stats_collector['received'] += 1
            consecutive_drops = 0
            
            sys.stdout.write(LIGHT_BLUE + f" [T{thread_id}] Packets sent to {resolved_ip}\n")
            sys.stdout.write(LIGHT_BLUE + f" [T{thread_id}] Packet set to {resolved_ip} | seq={i}/{packets_to_send} | size={payload_size}B | status=VERIFIED | time={latency:.2f}ms\n")
        except socket.timeout:
            consecutive_drops += 1
            if consecutive_drops > max_consecutive_drops:
                max_consecutive_drops = consecutive_drops
            sys.stdout.write(LIGHT_BLUE + f" [T{thread_id}] Packets sent to {resolved_ip}\n")
            sys.stdout.write(LIGHT_BLUE + f" [T{thread_id}] Packet set to {resolved_ip} | seq={i}/{packets_to_send} | size={payload_size}B | status=TIMEOUT\n")
        except Exception:
            consecutive_drops += 1
            if consecutive_drops > max_consecutive_drops:
                max_consecutive_drops = consecutive_drops
            sys.stdout.write(LIGHT_BLUE + f" [T{thread_id}] Packets sent to {resolved_ip}\n")
            sys.stdout.write(LIGHT_BLUE + f" [T{thread_id}] Packet set to {resolved_ip} | seq={i}/{packets_to_send} | size={payload_size}B | status=REFUSED/DROPPED\n")
        finally:
            sock.close()
        sys.stdout.flush()
            
        current_delay = delay
        if jitter_opt == 'y':
            current_delay = delay + random.uniform(-delay * 0.5, delay * 0.5)
            if current_delay < 0:
                current_delay = 0
                
        time.sleep(current_delay)
        
    if max_consecutive_drops > stats_collector['max_drops']:
        stats_collector['max_drops'] = max_consecutive_drops

def main():
    slow_print(ASCII_ART, 0.01)

    sys.stdout.write(LIGHT_BLUE + " Enter Target IP/Domain: ")
    sys.stdout.flush()
    target_ip = sys.stdin.readline().strip()
    if not target_ip:
        sys.stdout.write(ERRORRED + " [!] Target cannot be empty.\n")
        sys.stdout.flush()
        while True:
            time.sleep(1)

    try:
        resolved_ip = socket.gethostbyname(target_ip)
    except socket.gaierror:
        sys.stdout.write(ERRORRED + " [!] Error: Could not resolve host name.\n")
        sys.stdout.flush()
        while True:
            time.sleep(1)

    sys.stdout.write(LIGHT_BLUE + " Select Port Scan Profile:\n  [1] Common Ports\n  [2] Full Privileged Scan (1-1023)\n  [3] Web Vector Framework Only\n  [4] Skip Mapping\n Choice: ")
    sys.stdout.flush()
    scan_profile = sys.stdin.readline().strip()
    if scan_profile in ["1", "2", "3"]:
        run_port_scan(resolved_ip, scan_profile)
        sys.stdout.write("\n")
        sys.stdout.flush()

    sys.stdout.write(LIGHT_BLUE + " Enter Target Port [Default 5000]: ")
    sys.stdout.flush()
    port_input = sys.stdin.readline().strip()
    port = int(port_input) if port_input else 5000

    try:
        sys.stdout.write(LIGHT_BLUE + " Enter Amount of Pings per thread: ")
        sys.stdout.flush()
        ping_count = int(sys.stdin.readline().strip())
    except ValueError:
        sys.stdout.write(ERRORRED + " [!] Invalid count.\n")
        sys.stdout.flush()
        while True:
            time.sleep(1)

    try:
        sys.stdout.write(LIGHT_BLUE + " Enter Concurrent Thread Workers [Default 1]: ")
        sys.stdout.flush()
        thread_count = int(sys.stdin.readline().strip() or "1")
    except ValueError:
        thread_count = 1

    sys.stdout.write(LIGHT_BLUE + " Select Payload Type:\n  [1] Alphanumeric\n  [2] Zero-Bytes (Null)\n  [3] Hex FF\n  [4] Caps Only\n  [5] Special Characters\n  [6] Full Random Hex Matrix\n")
    sys.stdout.write(LIGHT_BLUE + " Choice [Default 1]: ")
    sys.stdout.flush()
    mode_choice = sys.stdin.readline().strip() or "1"

    try:
        sys.stdout.write(LIGHT_BLUE + " Enter Payload Size in Bytes [Default 32]: ")
        sys.stdout.flush()
        payload_size = int(sys.stdin.readline().strip() or "32")
        
        sys.stdout.write(LIGHT_BLUE + " Enter Timeout in Seconds [Default 1.0]: ")
        sys.stdout.flush()
        timeout = float(sys.stdin.readline().strip() or "1.0")
        
        sys.stdout.write(LIGHT_BLUE + " Enter Delay between pings in Seconds [Default 0.1]: ")
        sys.stdout.flush()
        delay = float(sys.stdin.readline().strip() or "0.1")
    except ValueError:
        sys.stdout.write(ERRORRED + " [!] Invalid inputs. Using defaults.\n")
        sys.stdout.flush()
        payload_size = 32
        timeout = 1.0
        delay = 0.1

    sys.stdout.write(LIGHT_BLUE + " Enable randomized delay jitter? (y/n): ")
    sys.stdout.flush()
    jitter_opt = sys.stdin.readline().strip().lower()

    sys.stdout.write(LIGHT_BLUE + f"\n [+] Target IP: {resolved_ip}\n")
    sys.stdout.write(LIGHT_BLUE + f" [+] Target Port: {port}\n")
    sys.stdout.write(LIGHT_BLUE + f" [+] Thread Parallelism Matrix: {thread_count} Worker Nodes\n")
    sys.stdout.write(LIGHT_BLUE + f" [+] Total Packet Sequences per Worker: {ping_count}\n")
    sys.stdout.write(LIGHT_BLUE + f" [+] Total Structural Payload Size: {payload_size} bytes\n")
    sys.stdout.write(LIGHT_BLUE + f" [+] Max Timeout Configuration: {timeout}s\n")
    sys.stdout.write(LIGHT_BLUE + " [+] Launching pinging...\n\n")
    sys.stdout.flush()

    stats_collector = {
        'sent': 0,
        'received': 0,
        'latencies': [],
        'max_drops': 0
    }

    workers = []
    for t_id in range(1, thread_count + 1):
        w = threading.Thread(target=worker_ping, args=(t_id, resolved_ip, port, ping_count, payload_size, timeout, delay, mode_choice, jitter_opt, stats_collector))
        workers.append(w)
        w.start()

    for w in workers:
        w.join()

    if stats_collector['sent'] > 0:
        loss_percent = ((stats_collector['sent'] - stats_collector['received']) / stats_collector['sent']) * 100
    else:
        loss_percent = 0.0
    
    sys.stdout.write("\n" + LIGHT_BLUE + " Pinging completed:\n")
    sys.stdout.write(LIGHT_BLUE + f" [+]  - Total Transmitted Matrix: {stats_collector['sent']}\n")
    sys.stdout.write(LIGHT_BLUE + f" [+] - Total Received Matrix: {stats_collector['received']}\n")
    sys.stdout.write(LIGHT_BLUE + f" [+]- Operational Loss Delta: {stats_collector['sent'] - stats_collector['received']} ({loss_percent:.1f}% loss)\n")
    sys.stdout.write(LIGHT_BLUE + f" [+] - Max Consecutive Worker Drops: {stats_collector['max_drops']}\n")
    
    if stats_collector['latencies']:
        min_lat = min(stats_collector['latencies'])
        max_lat = max(stats_collector['latencies'])
        avg_lat = sum(stats_collector['latencies']) / len(stats_collector['latencies'])
        variance = sum((x - avg_lat) ** 2 for x in stats_collector['latencies']) / len(stats_collector['latencies'])
        sys.stdout.write(LIGHT_BLUE + f" [+] - Jitter/Variance Minimum latency: {min_lat:.2f}ms\n")
        sys.stdout.write(LIGHT_BLUE + f" [+] - Jitter/Variance Maximum latency: {max_lat:.2f}ms\n")
        sys.stdout.write(LIGHT_BLUE + f" [+] - Jitter/Variance Average latency: {avg_lat:.2f}ms\n")
        sys.stdout.write(LIGHT_BLUE + f" [+] - Jitter Statistical Variance: {variance:.2f}\n")
    else:
        sys.stdout.write(ERRORRED + "  [!] - Latency Metrics Profile: Unavailable due to 100% packet loss.\n")
    sys.stdout.flush()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except ValueError:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.stdout.write("\n" + LIGHT_BLUE + " [+] IP PING V2 has been terminated by keyboard interrupt pressed by user\n")
        sys.stdout.flush()
        while True:
            time.sleep(1)
    except Exception:
        while True:
            time.sleep(1)