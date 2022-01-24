import requests
import os
import time

if __name__ == "__main__":
    code = os.system("ping -c 4 api.aliyundrive.com")
    print(code)

    times = []
    for i in range(4):
        start = time.perf_counter()
        r = requests.head("https://api.aliyundrive.com")
        end = time.perf_counter()
        times.append(end-start)

    for i, t in enumerate(times):
        print(f"Time {i}: {t:.6f} s")

    print("Hello world!")