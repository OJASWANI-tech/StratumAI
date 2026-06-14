import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

# Base data
cities = ["New York", "Los Angeles", "Chicago", "Houston", "Miami", "San Francisco", "Dallas", "Seattle"]
routes = ["Route A", "Route B", "Route C", "Route D", "Route E"]
vehicle_types = ["Bus", "Train", "Flight"]

# Generate 100 rows
data = []
for i in range(100):
    origin = random.choice(cities)
    destination = random.choice([c for c in cities if c != origin])
    route = random.choice(routes)
    vehicle = random.choice(vehicle_types)
    
    # Departure time randomly in a day
    dep_hour = np.random.randint(0, 24)
    dep_minute = np.random.randint(0, 60)
    departure_time = datetime(2025, 8, 24, dep_hour, dep_minute)
    
    # Distance depends on city pairs (approximate)
    distance_km = np.random.randint(50, 2500)
    
    # Duration depends on vehicle type
    if vehicle == "Bus":
        speed = np.random.randint(40, 80)
    elif vehicle == "Train":
        speed = np.random.randint(80, 200)
    else:  # Flight
        speed = np.random.randint(400, 900)
    duration_hours = distance_km / speed
    duration_minutes = int(duration_hours * 60)
    
    # Add random events
    delay_min = np.random.randint(-15, 90)  # early or late
    canceled = np.random.choice([0,1], p=[0.95, 0.05])  # 5% chance of cancellation
    
    arrival_time = departure_time + timedelta(minutes=duration_minutes + delay_min)
    
    # Passengers vary by vehicle
    if vehicle == "Bus":
        passengers = np.random.randint(10, 60)
    elif vehicle == "Train":
        passengers = np.random.randint(50, 500)
    else:
        passengers = np.random.randint(50, 300)
    
    # Congestion factor affecting fuel and time
    congestion = np.random.uniform(0.8, 1.5)
    fuel_used = round(distance_km * np.random.uniform(0.05, 0.2) * congestion, 2)
    
    # Revenue varies by passengers, distance, and vehicle
    revenue = round(passengers * distance_km * np.random.uniform(0.1, 0.5), 2)
    
    data.append([
        route, origin, destination, vehicle, departure_time.time(), arrival_time.time(),
        passengers, distance_km, delay_min, fuel_used, revenue, canceled, congestion
    ])

columns = ["Route", "Origin", "Destination", "VehicleType", "DepartureTime", "ArrivalTime",
           "Passengers", "Distance_km", "Delay_min", "FuelUsed_Liters", "Revenue_USD",
           "Canceled", "CongestionFactor"]

df = pd.DataFrame(data, columns=columns)

# Shuffle
df = df.sample(frac=1).reset_index(drop=True)

# Save CSV
df.to_csv("interesting_transportation_dataset.csv", index=False)

print("Sample rows:")
print(df.head())
