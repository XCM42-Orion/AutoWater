import inspect

class Logger:

    def get_caller_info():
        # 获取调用 logger 方法的帧
        frame = inspect.currentframe().f_back.f_back.f_back  # 往上三层

        code = frame.f_code
        function_name = code.co_name  # 调用 logger 的函数名
        class_name = None

        # 判断是否在类方法中（有 self 或 cls）
        local_vars = frame.f_locals
        if 'self' in local_vars:
            class_name = local_vars['self'].__class__.__name__
        elif 'cls' in local_vars:
            class_name = local_vars['cls'].__name__

        return class_name, function_name
    def print_log():
        cls, func = Logger.get_caller_info()
        return f"{cls}.{func}" if cls else f"{func}"

    def info(self, message):
        print(f"[\033[34mINFO\033[0m][\033[36m{Logger.print_log()}\033[0m]{message}")

    def error(self, message):
        print(f"[\033[31mERROR\033[0m][\033[36m{Logger.print_log()}\033[0m]{message}")

    def debug(self, message):
        print(f"[\033[32mDEBUG\033[0m][\033[36m{Logger.print_log()}\033[0m]{message}")

    def warning(self, message):
        print(f"[\033[33mWARNING\033[0m][\033[36m{Logger.print_log()}\033[0m]{message}")