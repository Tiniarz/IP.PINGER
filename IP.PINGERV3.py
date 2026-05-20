import os
import sys
import time
import socket
import random
import string
import threading
from colorama import Fore, init

init()

PRIMARY = Fore.YELLOW
LIGHT_WARN = Fore.LIGHTYELLOW_EX
ERRORRED = Fore.LIGHTRED_EX

ASCII_FULL = """
██╗██████╗     ██████╗ ██╗███╗   ██╗ ██████╗     ██╗   ██╗██████╗ 
██║██╔══██╗    ██╔══██╗██║████╗  ██║██╔════╝     ██║   ██║╚════██╗
██║██████╔╝    ██████╔╝██║██╔██╗ ██║██║  ███╗    ██║   ██║ █████╔╝
██║██╔═══╝     ██╔═══╝ ██║██║╚██╗██║██║   ██║    ╚██╗ ██╔╝ ╚═══██╗
██║██║         ██║     ██║██║ ╚████║╚██████╔╝     ╚████╔╝ ██████╔╝
╚═╝╚═╝         ╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝       ╚═══╝  ╚═════╝ 
"""

ASCII_MEDIUM = """
  _  ____    ____  _  _      _____   _    _____ 
/ \/  __\  /  __\/ \/ \  /|/  __/  / \ |\\__  \
| ||  \/|  |  \/|| || |\ ||| |  _  | | //  /  |
| ||  __/  |  __/| || | \||| |_//  | \//  _\  |
\_/\_/     \_/   \_/\_/  \|\____\  \__/  /____/
                                                
"""

ASCII_SMALL = "IP PINGER V3"
ASCII_MINI = "IP"

def is_termux():
    return "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux")

def get_terminal_width():
    try:
        return os.get_terminal_size().columns
    except (AttributeError, ValueError, OSError):
        return 80

def print_responsive_header():
    if is_termux():
        sys.stdout.write(PRIMARY + f" {ASCII_MINI}\n")
        sys.stdout.write(PRIMARY + "═" * 30 + "\n")
        sys.stdout.flush()
        return

    width = get_terminal_width()
    
    if width >= 70:
        for line in ASCII_FULL.splitlines():
            if line.strip():
                sys.stdout.write(PRIMARY + line + "\n")
    elif width >= 48:
        for line in ASCII_MEDIUM.splitlines():
            if line.strip():
                sys.stdout.write(PRIMARY + line + "\n")
    elif width >= 20:
        sys.stdout.write(PRIMARY + f"\n  === {ASCII_SMALL} ===\n")
    else:
        sys.stdout.write(PRIMARY + f" {ASCII_MINI}\n")
        
    sys.stdout.write(PRIMARY + "═" * width + "\n")
    sys.stdout.flush()

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
    elif mode == "7":
        return ("CACHE-CONTROL: NO-CACHE\r\nPRAGMA: NO-CACHE\r\n" * (size // 40)).encode()
    elif mode == "8":
        return ("A" * size).encode()
    else:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=size)).encode()

def scan_port(ip, port, open_ports, banner_dict):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    try:
        sock.connect((ip, port))
        open_ports.append(port)
        try:
            sock.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
            banner = sock.recv(512).decode('utf-8', errors='ignore').strip().split('\n')[0]
            if banner:
                banner_dict[port] = banner[:50]
        except:
            pass
    except:
        pass
    finally:
        sock.close()

def run_port_scan(ip, scan_type):
    sys.stdout.write(PRIMARY + f"\n ┌─── [!] Mapping network endpoint target layout: {ip}\n")
    sys.stdout.flush()
    
    if scan_type == "1":
        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 1433, 3306, 3389, 5000, 8080]
    elif scan_type == "2":
        ports = list(range(1, 1024))
    elif scan_type == "3":
        ports = [80, 443, 8080, 8443, 8000, 3000, 5000, 9000, 9100]
    elif scan_type == "4":
        ports = [22, 111, 2049, 3306, 5432, 6379, 9200, 27017]
    elif scan_type == "5":
        ports = [53, 67, 68, 69, 123, 161, 443, 500, 4500]
    else:
        return

    open_ports = []
    banner_dict = {}
    threads = []
    
    for port in ports:
        t = threading.Thread(target=scan_port, args=(ip, port, open_ports, banner_dict))
        threads.append(t)
        t.start()
        if len(threads) >= 120:
            for thread in threads:
                thread.join()
            threads = []
            
    for t in threads:
        t.join()
        
    if open_ports:
        sys.stdout.write(PRIMARY + " ├─── [+] Map successful. Open points identified:\n")
        for port in sorted(open_ports):
            banner_info = f" -> Verification Data: {banner_dict[port]}" if port in banner_dict else ""
            sys.stdout.write(PRIMARY + f" │    └── Endpoint Layer {port}{banner_info}\n")
    else:
        sys.stdout.write(ERRORRED + " ├─── [!] Endpoint discovery mapping array found no responsive vectors.\n")
    sys.stdout.write(PRIMARY + " └" + "─" * 40 + "\n")
    sys.stdout.flush()

def worker_ping(thread_id, resolved_ip, port, total_packets, payload_size, timeout, delay, mode_choice, jitter_opt, sock_type, output_mode, stats_collector):
    payload = generate_payload(mode_choice, payload_size)
    consecutive_drops = 0
    max_consecutive_drops = 0
    
    for i in range(1, total_packets + 1):
        if sock_type == "2":
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
        sock.settimeout(timeout)
        start_time = time.time()
        stats_collector['sent'] += 1
        
        try:
            if sock_type == "2":
                sock.sendto(payload, (resolved_ip, port))
                if timeout > 0:
                    sock.recvfrom(1024)
            else:
                sock.connect((resolved_ip, port))
                sock.sendall(payload)
                
            latency = (time.time() - start_time) * 1000
            stats_collector['latencies'].append(latency)
            stats_collector['received'] += 1
            consecutive_drops = 0
            
            if output_mode == "1":
                sys.stdout.write(PRIMARY + f" ┌── [W{thread_id:03d}] SUCCESS ── {resolved_ip}\n")
                sys.stdout.write(PRIMARY + f" └── [NODE] seq={i}/{total_packets} | size={payload_size}B | status=VERIFIED | time={latency:.2f}ms\n")
            elif output_mode == "2":
                sys.stdout.write(PRIMARY + "─")
        except socket.timeout:
            consecutive_drops += 1
            if consecutive_drops > max_consecutive_drops:
                max_consecutive_drops = consecutive_drops
            if output_mode == "1":
                sys.stdout.write(PRIMARY + f" ┌── [W{thread_id:03d}] FAILURE ── {resolved_ip}\n")
                sys.stdout.write(ERRORRED + f" └── [ALERT] seq={i}/{total_packets} | size={payload_size}B | status=TIMEOUT EXPIRED\n")
            elif output_mode == "2":
                sys.stdout.write(ERRORRED + "弾")
        except Exception:
            consecutive_drops += 1
            if consecutive_drops > max_consecutive_drops:
                max_consecutive_drops = consecutive_drops
            if output_mode == "1":
                sys.stdout.write(PRIMARY + f" ┌── [W{thread_id:03d}] EXCEPTION ── {resolved_ip}\n")
                sys.stdout.write(ERRORRED + f" └── [ALERT] seq={i}/{total_packets} | size={payload_size}B | status=VECTOR REFUSED\n")
            elif output_mode == "2":
                sys.stdout.write(ERRORRED + "×")
        finally:
            sock.close()
        sys.stdout.flush()
            
        current_delay = delay
        if jitter_opt == 'y':
            current_delay = delay + random.uniform(-delay * 0.4, delay * 0.4)
            if current_delay < 0:
                current_delay = 0
                
        time.sleep(current_delay)
        
    if max_consecutive_drops > stats_collector['max_drops']:
        stats_collector['max_drops'] = max_consecutive_drops

def main():
    print_responsive_header()

    sys.stdout.write(PRIMARY + " ╔═══[ CONFIGURATION WIZARD ]\n")
    sys.stdout.write(PRIMARY + " ║\n")
    
    sys.stdout.write(PRIMARY + " ╠═[?] Enter target here (IP/Domain): ")
    sys.stdout.flush()
    target_ip = sys.stdin.readline().strip()
    if not target_ip:
        sys.stdout.write(ERRORRED + " ╚═[!] ERROR: There was no IP address or Domain applied.\n")
        sys.stdout.flush()
        while True: time.sleep(1)

    try:
        resolved_ip = socket.gethostbyname(target_ip)
    except socket.gaierror:
        sys.stdout.write(ERRORRED + " ╚═[!] ERROR: Namespace resolution mapping failed.\n")
        sys.stdout.flush()
        while True: time.sleep(1)

    sys.stdout.write(PRIMARY + " ║\n ╠═[?] Transport Protocol Standard Selection:\n │   [1] TCP Handshake Connection\n │   [2] UDP Stateless Transmission\n │   Choice [Default 1]: ")
    sys.stdout.flush()
    sock_type = sys.stdin.readline().strip() or "1"

    sys.stdout.write(PRIMARY + " ║\n ╠═[?] IPv4 Advanced Options Mode?\n │   [1] Standard Transmission\n │   [2] Keep-Alive Headers Mapping\n │   [3] High-Priority TOS Flag\n │   Choice [Default 1]: ")
    sys.stdout.flush()
    ipv4_option = sys.stdin.readline().strip() or "1"

    sys.stdout.write(PRIMARY + " ║\n ╠═[?] Network Structural Pre-Scan Mapping Type:\n │   [1] Standard Diagnostic Common Vectors\n │   [2] Full System Core Vector Range (1-1023)\n │   [3] Web Application Transport Profiles Only\n │   [4] Infrastructure Services (Database/SSH/NFS)\n │   [5] Core Router Protocol Vectors\n │   [6] Skip Integration Map Routine\n │   Choice: ")
    sys.stdout.flush()
    scan_profile = sys.stdin.readline().strip()
    if scan_profile in ["1", "2", "3", "4", "5"]:
        run_port_scan(resolved_ip, scan_profile)
        sys.stdout.write(PRIMARY + " ║\n")
        sys.stdout.flush()

    sys.stdout.write(PRIMARY + " ╠═[?] Network Architecture Target Port [Default 80]: ")
    sys.stdout.flush()
    port_input = sys.stdin.readline().strip()
    port = int(port_input) if port_input else 80

    try:
        sys.stdout.write(PRIMARY + " ╠═[?] Target Packet Count per Processing Node: ")
        sys.stdout.flush()
        ping_count = int(sys.stdin.readline().strip())
    except ValueError:
        sys.stdout.write(ERRORRED + " ╚═[!] ERROR: Specified counting data parameter is unreadable.\n")
        sys.stdout.flush()
        while True: time.sleep(1)

    try:
        sys.stdout.write(PRIMARY + " ╠═[?] Concurrent Worker Subprocess Allocation [Default 1]: ")
        sys.stdout.flush()
        thread_count = int(sys.stdin.readline().strip() or "1")
    except ValueError:
        thread_count = 1

    sys.stdout.write(PRIMARY + " ║\n ╠═[?] Payload Frame Content Configuration Profile:\n │   [1] Alphanumeric Text Sequence Matrix\n │   [2] Zero-Fill Content Field Structure (Null)\n │   [3] Maximum Bit State Payload Struct (Hex FF)\n │   [4] Capitalized Variable String Structures\n │   [5] Symbol Array Fragmentation Elements\n │   [6] Non-Deterministic Pseudo Random Matrix\n │   [7] Cache Bypass String Blocks\n │   [8] Monolithic Structural Blocks (Static A)\n │   Choice [Default 1]: ")
    sys.stdout.flush()
    mode_choice = sys.stdin.readline().strip() or "1"

    try:
        sys.stdout.write(PRIMARY + " ║\n ╠═[?] Enter volume in Bytes [Default 64]: ")
        sys.stdout.flush()
        payload_size = int(sys.stdin.readline().strip() or "64")
        
        sys.stdout.write(PRIMARY + " ╠═[?] Network Expiration Limit in Seconds [Default 2.0]: ")
        sys.stdout.flush()
        timeout = float(sys.stdin.readline().strip() or "2.0")
        
        sys.stdout.write(PRIMARY + " ╠═[?] Delay Space Buffer Duration between Nodes [Default 0.2]: ")
        sys.stdout.flush()
        delay = float(sys.stdin.readline().strip() or "0.2")
    except ValueError:
        sys.stdout.write(LIGHT_WARN + " │   [!] Input execution values wrong. Using default parameters.\n")
        sys.stdout.flush()
        payload_size = 64
        timeout = 2.0
        delay = 0.2

    sys.stdout.write(PRIMARY + " ╠═[?] Interject Randomized Micro Jitter Into Wait Spacing? (y/n): ")
    sys.stdout.flush()
    jitter_opt = sys.stdin.readline().strip().lower()

    sys.stdout.write(PRIMARY + " ║\n ╠═[?] Output Diagnostics Tracking Mode:\n │   [1] Real-time High-Density Stacked TUI Intercept\n │   [2] Compact inline graphical sequence visualizer\n │   Choice [Default 1]: ")
    sys.stdout.flush()
    output_mode = sys.stdin.readline().strip() or "1"

    sys.stdout.write(PRIMARY + " ║\n ╠═[?] Session Logging Options:\n │   [1] Screen Output Only\n │   [2] High-Performance Cache Buffer Only\n │   Choice [Default 1]: ")
    sys.stdout.flush()
    logging_option = sys.stdin.readline().strip() or "1"

    sys.stdout.write(PRIMARY + " ║\n ╚═══[ Questions are done. ]\n\n")
    
    sys.stdout.write(PRIMARY + f" ╔══════════════════════════════════════════════════════════\n")
    sys.stdout.write(PRIMARY + f" ║ [►] Destination Identity Evaluated : {resolved_ip}\n")
    sys.stdout.write(PRIMARY + f" ║ [►] Intended Delivery End Point    : {port}\n")
    sys.stdout.write(PRIMARY + f" ║ [►] Processing Threads Strategy    : {thread_count} Active Units\n")
    sys.stdout.write(PRIMARY + f" ║ [►] Operational Cycles Apportioned : {ping_count}\n")
    sys.stdout.write(PRIMARY + f" ║ [►] Frame Buffer Dimensions       : {payload_size} Bytes\n")
    sys.stdout.write(PRIMARY + f" ║ [►] MaximumLifecycle Connection   : {timeout}s\n")
    sys.stdout.write(PRIMARY + f" ╚══════════════════════════════════════════════════════════\n\n")
    sys.stdout.write(PRIMARY + " [+] Launching pinging...\n\n")
    sys.stdout.flush()

    stats_collector = {
        'sent': 0,
        'received': 0,
        'latencies': [],
        'max_drops': 0
    }

    workers = []
    for t_id in range(1, thread_count + 1):
        w = threading.Thread(target=worker_ping, args=(t_id, resolved_ip, port, ping_count, payload_size, timeout, delay, mode_choice, jitter_opt, sock_type, output_mode, stats_collector))
        workers.append(w)
        w.start()

    for w in workers:
        w.join()

    if output_mode == "2":
        sys.stdout.write("\n")

    if stats_collector['sent'] > 0:
        loss_percent = ((stats_collector['sent'] - stats_collector['received']) / stats_collector['sent']) * 100
    else:
        loss_percent = 0.0
    
    sys.stdout.write("\n" + PRIMARY + " ╔═══════════════════════════════════════════════════════════════════════════\n")
    sys.stdout.write(PRIMARY + " ║  PINGING HAS BEEN FINISHED. PING DASHBOARD\n")
    sys.stdout.write(PRIMARY + " ╠═══════════════════════════════════════════════════════════════════════════\n")
    sys.stdout.write(PRIMARY + f" ║  [+] Frame Submissions Conducted               : {stats_collector['sent']}\n")
    sys.stdout.write(PRIMARY + f" ║  [+] System Intercepts Recovered               : {stats_collector['received']}\n")
    sys.stdout.write(PRIMARY + f" ║  [+] Statistical Frame Droppage Variance       : {stats_collector['sent'] - stats_collector['received']} ({loss_percent:.2f}% drop rate)\n")
    sys.stdout.write(PRIMARY + f" ║  [+] Maximum Unbroken Sequence Failures        : {stats_collector['max_drops']}\n")
    sys.stdout.write(PRIMARY + " ╠═══════════════════════════════════════════════════════════════════════════\n")
    
    if stats_collector['latencies']:
        min_lat = min(stats_collector['latencies'])
        max_lat = max(stats_collector['latencies'])
        avg_lat = sum(stats_collector['latencies']) / len(stats_collector['latencies'])
        variance = sum((x - avg_lat) ** 2 for x in stats_collector['latencies']) / len(stats_collector['latencies'])
        sys.stdout.write(PRIMARY + f" ║  [✦] Minimal Turnaround Validation Delta       : {min_lat:.2f}ms\n")
        sys.stdout.write(PRIMARY + f" ║  [✦] Peak Turnaround Validation Delta          : {max_lat:.2f}ms\n")
        sys.stdout.write(PRIMARY + f" ║  [✦] Median Turnaround Validation Value         : {avg_lat:.2f}ms\n")
        sys.stdout.write(PRIMARY + f" ║  [✦] Calculated System Jitter Margin           : {variance:.2f}\n")
    else:
        sys.stdout.write(ERRORRED + " ║  [!] Dynamic Network Profile Data: Pinging failed due to absolute packet transmission loss.\n")
    sys.stdout.write(PRIMARY + " ╚═══════════════════════════════════════════════════════════════════════════\n")
    sys.stdout.flush()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except ValueError:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        sys.stdout.write("\n" + PRIMARY + " ╚═══[ [+] IP PING V3 has been terminated. Have a good time. ]\n")
        sys.stdout.flush()
        while True: time.sleep(1)
    except Exception:
        while True: time.sleep(1)