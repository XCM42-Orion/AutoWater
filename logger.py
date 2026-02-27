import traceback

#DEBUG!!
debug_flag = True

class Logger:
    def info(self, message):
        print(f"[\033[34mINFO\033[0m] {message}")
    def error(self, message):
        if debug_flag:
            raise
        print(f"[\033[31mERROR\033[0m] {message}")
    def debug(self, message):
        print(f"[\033[32mDEBUG\033[0m] {message}")
    def warning(self, message):
        print(f"[\033[33mWARNING\033[0m] {message}")