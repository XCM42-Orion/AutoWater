from module import Module
from logger import Logger


class delay(Module):
    def __init__(self):
        super().__init__()
        self.delay_time = 0  # 默认延迟时间为0秒
        self.logger = Logger()

    def register(self, message_handler, event_handler, module_handler):
        return super().register(message_handler, event_handler, module_handler)

    def standard_delay(self,input,output):
        """
        标准回复时间是为了模拟人的阅读与打字速度。
        标准等待时间由输入和输出时间两部分组成：
        如果字符数小于 10 ，则输入时间为 0 s，否则为 字符数*0.2 s。
        输出时间等于 回复长度*0.3 s 。
        """
        input_length = len(input)
        output_length = len(output)

        if input_length < 10:
            input_time = 0
        else:
            input_time = input_length * 0.2

        output_time = output_length * 0.3
        self.delay_time = input_time + output_time
        self.logger.info(f"计算延迟时间: 输入时间 {input_time:.2f}s + 输出时间 {output_time:.2f}s = 总计 {self.delay_time:.2f}s")
        return self.delay_time
    
    def only_output_delay(self, output):
        """
        仅输出延迟时间。
        输出时间等于 回复长度*0.3 +1 s 。
        """
        output_length = len(output)
        self.delay_time = output_length * 0.3 + 1
        self.logger.info(f"计算延迟时间: 输出时间 {self.delay_time:.2f}s")
        return self.delay_time
    
    def only_input_delay(self, input):
        """
        仅输入延迟时间。
        如果字符数小于 10 ，则输入时间为 0 s，否则为 字符数*0.2 s。
        """
        input_length = len(input)
        if input_length < 10:
            self.delay_time = 0
        else:
            self.delay_time = input_length * 0.2
        self.logger.info(f"计算延迟时间: 输入时间 {self.delay_time:.2f}s")
        return self.delay_time
    
    def constant_delay(self, time):
        """
        固定延迟时间。
        直接返回设定的时间。
        """
        self.delay_time = time
        self.logger.info(f"计算延迟时间: 固定时间 {self.delay_time:.2f}s")
        return self.delay_time