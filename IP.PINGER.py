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
██╗██████╗     ██████╗ ██╗███╗   ██╗ ██████╗ ███████╗██████╗ 
██║██╔══██╗    ██╔══██╗██║████╗  ██║██╔════╝ ██╔════╝██╔══██╗
██║██████╔╝    ██████╔╝██║██╔██╗ ██║██║  ███╗█████╗  ██████╔╝
██║██╔═══╝     ██╔═══╝ ██║██║╚██╗██║██║   ██║██╔══╝  ██╔══██╗
██║██║         ██║     ██║██║ ╚████║╚██████╔╝███████╗██║  ██║
╚═╝╚═╝         ╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
"""

def slow_print(text, speed=0.05):
    for line in text.splitlines():
        sys.stdout.write(DARK_BLUE + line + '\n')
        sys.stdout.flush()
        time.sleep(speed)

def generate_payload(mode, size):
    if mode == "1":
        return ''.join(random.choices(string.ascii_letters + string.digits, k=size)).encode()
    elif mode == "2":
        return b'\x00' * size
    elif mode == "3":
        return b'\xff' * size
    else:
        return ''.join(random.choices(string.ascii_uppercase, k=size)).encode()

def scan_port(ip, port, open_ports):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.3)
    try:
        sock.connect((ip, port))
        open_ports.append(port)
    except:
        pass
    finally:
        sock.close()

def run_port_scan(ip):
    sys.stdout.write(LIGHT_BLUE + f"\n [+] Scanning common ports on {ip}...\n")
    sys.stdout.flush()
    common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 1433, 3306, 3389, 5000, 8080]
    open_ports = []
    threads = []
    
    for port in common_ports:
        t = threading.Thread(target=scan_port, args=(ip, port, open_ports))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    if open_ports:
        sys.stdout.write(LIGHT_BLUE + f" [+] Active ports discovered: {', '.join(map(str, open_ports))}\n")
    else:
        sys.stdout.write(ERRORRED + " [!] No common ports responded during brief scan.\n")
    sys.stdout.flush()

def main():
    slow_print(ASCII_ART, 0.05)

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

    sys.stdout.write(LIGHT_BLUE + " Run quick pre-ping port scan? (y/n): ")
    sys.stdout.flush()
    run_scan = sys.stdin.readline().strip().lower()
    if run_scan == 'y':
        run_port_scan(resolved_ip)
        sys.stdout.write("\n")
        sys.stdout.flush()

    sys.stdout.write(LIGHT_BLUE + " Enter Target Port [Default 5000]: ")
    sys.stdout.flush()
    port_input = sys.stdin.readline().strip()
    port = int(port_input) if port_input else 5000

    try:
        sys.stdout.write(LIGHT_BLUE + " Enter Amount of Pings: ")
        sys.stdout.flush()
        ping_count = int(sys.stdin.readline().strip())
    except ValueError:
        sys.stdout.write(ERRORRED + " [!] Invalid count.\n")
        sys.stdout.flush()
        while True:
            time.sleep(1)

    sys.stdout.write(LIGHT_BLUE + " Select Payload Type:\n  [1] Alphanumeric\n  [2] Zero-Bytes (Null)\n  [3] Hex FF\n  [4] Caps Only\n")
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
    sys.stdout.write(LIGHT_BLUE + f" [+] Total Packets: {ping_count}\n")
    sys.stdout.write(LIGHT_BLUE + f" [+] Payload configuration: {payload_size} bytes\n")
    sys.stdout.write(LIGHT_BLUE + f" [+] Timeout limitation: {timeout}s\n")
    sys.stdout.write(LIGHT_BLUE + " [+] Launching target verification...\n\n")
    sys.stdout.flush()
    
    sent_packets = 0
    received_packets = 0
    latencies = []
    consecutive_drops = 0
    max_consecutive_drops = 0

    payload = generate_payload(mode_choice, payload_size)

    for i in range(1, ping_count + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        start_time = time.time()
        sent_packets += 1
        
        try:
            sock.connect((resolved_ip, port))
            sock.sendall(payload)
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)
            received_packets += 1
            consecutive_drops = 0
            
            sys.stdout.write(LIGHT_BLUE + f" [+] Packets sent to {resolved_ip}\n")
            sys.stdout.write(LIGHT_BLUE + f" [+] Packet set to {resolved_ip} | seq={i}/{ping_count} | size={payload_size}B | status=VERIFIED | time={latency:.2f}ms\n")
        except socket.timeout:
            consecutive_drops += 1
            if consecutive_drops > max_consecutive_drops:
                max_consecutive_drops = consecutive_drops
            sys.stdout.write(LIGHT_BLUE + f" [+] Packets sent to {resolved_ip}\n")
            sys.stdout.write(LIGHT_BLUE + f" [+] Packet set to {resolved_ip} | seq={i}/{ping_count} | size={payload_size}B | status=TIMEOUT\n")
        except Exception:
            consecutive_drops += 1
            if consecutive_drops > max_consecutive_drops:
                max_consecutive_drops = consecutive_drops
            sys.stdout.write(LIGHT_BLUE + f" [+] Packets sent to {resolved_ip}\n")
            sys.stdout.write(LIGHT_BLUE + f" [+] Packet set to {resolved_ip} | seq={i}/{ping_count} | size={payload_size}B | status=REFUSED/DROPPED\n")
        finally:
            sock.close()
        sys.stdout.flush()
            
        current_delay = delay
        if jitter_opt == 'y':
            current_delay = delay + random.uniform(-delay * 0.5, delay * 0.5)
            if current_delay < 0:
                current_delay = 0
                
        time.sleep(current_delay)

    loss_percent = ((sent_packets - received_packets) / sent_packets) * 100
    
    sys.stdout.write("\n" + LIGHT_BLUE + " Diagnostic Metrics Baseline:\n")
    sys.stdout.write(LIGHT_BLUE + f" [+]  - Packets Transmitted: {sent_packets}\n")
    sys.stdout.write(LIGHT_BLUE + f" [+] - Packets Received: {received_packets}\n")
    sys.stdout.write(LIGHT_BLUE + f" [+]- Packets Loss Delta: {sent_packets - received_packets} ({loss_percent:.1f}% loss)\n")
    sys.stdout.write(LIGHT_BLUE + f" [+] - Max Consecutive Drops: {max_consecutive_drops}\n")
    
    if latencies:
        min_lat = min(latencies)
        max_lat = max(latencies)
        avg_lat = sum(latencies) / len(latencies)
        variance = sum((x - avg_lat) ** 2 for x in latencies) / len(latencies)
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
        sys.stdout.write("\n" + LIGHT_BLUE + " [+] Operational loop terminated by user context request.\n")
        sys.stdout.flush()
        while True:
            time.sleep(1)
    except Exception:
        while True:
            time.sleep(1)