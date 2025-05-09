import gpsd
import time
from math import radians, cos, sin, sqrt, atan2

# Configuration Constants
MAX_JUMP_METERS = 100
MAX_HDOP = 5.0
MIN_SATELLITES = 4
SPOOF_COOLDOWN = 10  # seconds

# ANSI escape code for red color
RED = "\033[91m"
RESET = "\033[0m"

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the Earth."""
    R = 6371000  # Radius of the Earth in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2)**2 + cos(phi1) * cos(phi2) * sin(dlambda / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def log_alert(message):
    """Prints red-colored alert message."""
    print(f"{RED}{message}{RESET}")

def detect_gps_spoof():
    """Continuously monitors GPS data to detect possible spoofing or jamming events."""
    gpsd.connect()
    last_lat = last_lon = None
    last_spoof_time = 0

    while True:
        try:
            packet = gpsd.get_current()

            lat = getattr(packet, "lat", None)
            lon = getattr(packet, "lon", None)
            sats = getattr(packet, "sats", 0) or 0
            hdop = getattr(packet, "hdop", None)
            mode = getattr(packet, "mode", 0)

            if lat is not None and lon is not None:
                fix_status = "FIX" if mode >= 2 else "NO FIX"
                hdop_display = f"{hdop:.1f}" if hdop is not None else "N/A"
                print(f"[{fix_status}] Lat: {lat:.6f}, Lon: {lon:.6f} | Sats: {sats} | HDOP: {hdop_display}")

                if mode >= 2:
                    if sats < MIN_SATELLITES:
                        log_alert(f"! Low satellite count: {sats} — possible jamming")

                    if hdop is not None and hdop > MAX_HDOP:
                        log_alert(f"!! High HDOP ({hdop}) — possible spoof")

                    if last_lat is not None and last_lon is not None:
                        dist = haversine(last_lat, last_lon, lat, lon)
                        if dist > MAX_JUMP_METERS:
                            now = time.time()
                            if now - last_spoof_time > SPOOF_COOLDOWN:
                                log_alert(f"!!! Sudden jump of {dist:.1f} meters — possible spoof")
                                last_spoof_time = now

                    last_lat, last_lon = lat, lon
                else:
                    print("No valid GPS fix yet. Spoof detection paused.")
            else:
                log_alert("! No valid lat/lon data available.")

            time.sleep(5)

        except Exception as e:
            log_alert(f"! Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    detect_gps_spoof()
