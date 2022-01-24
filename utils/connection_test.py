import argparse
import time

import requests


def test_connection(url: str, count: int = 4) -> str:
    times = []
    for i in range(count):
        t_start = time.perf_counter()
        try:
            requests.head(url)
        except:
            times.append(-1)
            continue
        else:
            t_end = time.perf_counter()
            times.append(t_end - t_start)

    result = "Connection test for url: {}\n".format(url)
    for i, t in enumerate(times):
        result += "Count:\t{}\tElapsed Time:\t{:.6f} s\t\n".format(i, t)
    result += "Average Time:\t{:.6f} s\t\n".format(sum(times)/count)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str, help="Site url to test.")
    parser.add_argument("-c", dest="count", type=int, help="Times to test.", default=4)

    args = parser.parse_args()

    test_result = test_connection(args.url, args.count)
    print(test_result)
