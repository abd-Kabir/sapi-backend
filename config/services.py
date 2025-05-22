import threading


def run_with_thread(func, args):
    t = threading.Thread(target=func, args=args)
    t.start()
