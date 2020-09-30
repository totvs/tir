import psutil

def system_info():
    print(f"CPU USAGE: {psutil.cpu_percent()}%")
    print(f"MEMORY USAGE: {psutil.virtual_memory().percent}%")
    print(f"MEMORY AVALIABLE: {round(psutil.virtual_memory().available * 100 / psutil.virtual_memory().total, 2)}%")

if __name__ == "__main__":
    system_info()