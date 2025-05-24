import random
import time
from datetime import datetime, timedelta
import csv
import ipaddress
import os
import pandas as pd

# List of possible endpoints
endpoints = [
    "/scheduledemo.php", "/event.php", "/prototype.php",
    "/ai-assistant.php", "/jobs.php"
]

# List of possible status codes
status_codes = [200, 304, 404, 500]

# Enhanced user roles for an AI solutions website
USER_ROLES = [
    "AI Researcher", "Data Scientist", "Product Manager",
    "CTO", "Software Engineer", "Business Analyst",
    "UX Designer", "DevOps Engineer", "Marketing Specialist",
    "Sales Executive", "HR Manager", "Student"
]

# Countries and their IP ranges
countries = {
    "United States": ["12.0.0.0/8", "128.1.0.0/16", "155.55.0.0/16"],
    "United Kingdom": ["5.0.0.0/8", "25.0.0.0/8", "80.0.0.0/8"],
    "Germany": ["78.0.0.0/8", "79.0.0.0/8", "80.0.0.0/8"],
    "France": ["90.0.0.0/8", "91.0.0.0/8", "92.0.0.0/8"],
    "Japan": ["110.0.0.0/8", "111.0.0.0/8", "112.0.0.0/8"],
    "India": ["115.0.0.0/8", "116.0.0.0/8", "117.0.0.0/8"],
    "Brazil": ["177.0.0.0/8", "179.0.0.0/8", "189.0.0.0/8"],
    "Australia": ["1.0.0.0/8", "14.0.0.0/8", "27.0.0.0/8"],
    "Canada": ["24.0.0.0/8", "70.0.0.0/8", "142.0.0.0/8"],
    "China": ["36.0.0.0/8", "42.0.0.0/8", "58.0.0.0/8"],
    "South Africa": ["41.0.0.0/8", "105.0.0.0/8", "196.0.0.0/8"],
    "Mexico": ["187.0.0.0/8", "189.0.0.0/8", "200.0.0.0/8"],
    "Russia": ["46.0.0.0/8", "79.0.0.0/8", "95.0.0.0/8"],
    "South Korea": ["112.0.0.0/8", "114.0.0.0/8", "175.0.0.0/8"],
    "Singapore": ["116.0.0.0/8", "118.0.0.0/8", "175.0.0.0/8"],
    "Italy": ["79.0.0.0/8", "80.0.0.0/8", "93.0.0.0/8"],
    "Spain": ["80.0.0.0/8", "81.0.0.0/8", "95.0.0.0/8"],
    "Netherlands": ["82.0.0.0/8", "84.0.0.0/8", "94.0.0.0/8"],
    "Sweden": ["83.0.0.0/8", "85.0.0.0/8", "89.0.0.0/8"],
    "Switzerland": ["85.0.0.0/8", "86.0.0.0/8", "91.0.0.0/8"]
}

if __name__ != "__main__":
    __all__ = ['countries', 'USER_ROLES']  # Make these available for import

def generate_ip(country):
    """Generate a random IP address within the country's range"""
    if country not in countries:
        country = random.choice(list(countries.keys()))
    
    network = random.choice(countries[country])
    net = ipaddress.ip_network(network)
    
    network_addr = int(net.network_address)
    broadcast_addr = int(net.broadcast_address)
    
    random_ip = ipaddress.ip_address(random.randint(network_addr + 1, broadcast_addr - 1))
    return str(random_ip)

def generate_log_entry():
    """Generate a single log entry with complete information"""
    log_time = datetime.now() - timedelta(
        days=random.randint(0, 30), 
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59))
    # Include full datetime in the timestamp
    time_str = log_time.strftime("%Y-%m-%d %H:%M:%S")
    
    country = random.choice(list(countries.keys()))
    ip = generate_ip(country)
    endpoint = random.choice(endpoints)
    status = random.choice(status_codes)
    user_role = random.choice(USER_ROLES)
    
    # Age group based on role
    if user_role in ["Student"]:
        age_group = "18-24"
    elif user_role in ["AI Researcher", "Software Engineer", "UX Designer"]:
        age_group = random.choice(["25-34", "35-44"])
    else:
        age_group = random.choice(["35-44", "45-54", "55+"])
    
    return [time_str, ip, "GET", endpoint, status, country, user_role, age_group]

def generate_logs(num_entries=1000, output_file="data/server_logs.csv", refresh=False):
    """Generate log entries and save to CSV with refresh option"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    mode = 'w' if refresh else 'a'
    header = refresh or not os.path.exists(output_file)
    
    with open(output_file, mode, newline='') as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(["timestamp", "ip", "method", "endpoint", "status", 
                           "country", "user_role", "age_group"])
        
        for _ in range(num_entries):
            entry = generate_log_entry()
            writer.writerow(entry)
    
    # Remove duplicates if appending
    if not refresh:
        df = pd.read_csv(output_file)
        df = df.drop_duplicates()
        df.to_csv(output_file, index=False)
    
    print(f"Generated {num_entries} log entries in {output_file}")

if __name__ == "__main__":
    generate_logs(5000)