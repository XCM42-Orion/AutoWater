from module import *
from enum import Enum

class EventType(Enum):
    EVENT_INIT = 0
    EVENT_RECV_MSG = 1
    EVENT_PRE_SEND_MSG = 2
    EVENT_NOTICE_MSG = 3

import asyncio
from collections import defaultdict
from typing import *
import json
from message_utils import *

#把原来的config,messagehandler等等东西扔在一起，并方便不同module通信
#通信方法：context.mod.<类名>
class EventContext:
    def __init__(self):
        self.message_handler = None
        self.event_handler = None

        #其实就是module_handler，写成mod是为了好看，方便调用别的module的内容
        self.mod = None
        
        self.utilities = None
        self.log = None


#现在可以自定义event了

class Event:
    def __init__(self,event_type: EventType,context: EventContext,data: Any):
        self.event_type = event_type

        #-1异常event 0未初始化的event 1已经初始化的event
        self.status = 0

        #阻塞消息
        self.blocked = False

        #同一个priority 只能一个listener修改消息
        #现在是线程不安全的，以后可做成线程安全的

        #数据初始化
        #这里存储着message / notice
        self.data = data

        #事件上下文
        self.context = context

        #事件被哪些module处理过
        #形式：dict[module_classname(str):priority(int)]
        self.history = []

        #标记初始化完成防止__setattr__拦截__init__里面的设置行为
        self.status = 1
    
    def block_event(self):
        self.blocked = True

#内部类，便于把listener和module联系起来并记录listener的响应函数，可以被直接当作函数调用，对module透明
class Listener:
    def __init__(self, module: Module, callback: Callable):
        self.module = module
        self.callback = callback


    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        将任意参数原样转发给callback函数
        
        参数:
            *args: 任意位置参数
            **kwargs: 任意关键字参数
            
        返回:
            callback函数的返回值
        """
        if asyncio.iscoroutinefunction(self.callback):
            return await self.callback(*args, **kwargs)
        else:
            return self.callback(*args, **kwargs)

class EventHandler:
    def __init__(self):
        # 存储监听器的数据结构
        # event_type -> priority -> list[listener]
        self.listeners: Dict[EventType, Dict[int, List[Callable]]] = defaultdict(
            lambda: defaultdict(list)
        )
        # 存储协程任务
        self.tasks: List[asyncio.Task] = []
    
    def _inner_register_listener(self, module: Module, event_type: EventType, callback: Callable, priority: int):
        """注册监听器，可以指定优先级"""
        """仅供message_handler使用，注册时请使用message_handler.register_listener"""
        '''WARNING:priority越小越优先'''
        self.listeners[event_type][priority].append(Listener(module, callback))
    
    async def dispatch_event(self, event: Event):
        event_type = event.event_type
        context = event.context
        """分发事件，按照优先级顺序执行"""
        if event_type not in self.listeners:
            return
        
        # 获取该事件类型的所有监听器
        corresponding_listeners = self.listeners[event_type]   #得到Dict[Priority(以int表示), List[Callable]]
        
        # 按优先级从高到低排序
        sorted_priorities = sorted(corresponding_listeners.keys())
        
        for priority in sorted_priorities:
            #获取当前优先级的监听器
            listeners = corresponding_listeners[priority]

            #如果当前优先级没有任何监听器
            if not listeners:
                continue
            
            # 为同一优先级的监听器创建协程任务
            tasks = []
            for listener in listeners:
                #便于追踪这个消息被哪些module处理过
                event.history.append((priority,
                    context.mod.get_classname_by_instance(listener.module)))
                try:
                    if asyncio.iscoroutinefunction(listener.callback):
                        # 如果是协程函数，直接创建任务
                        tasks.append(asyncio.create_task(
                            listener(event, context)
                        ))
                    else:
                        # 请尽可能使用协程函数
                        # 同步函数使用 to_thread 在单独线程中运行
                        tasks.append(asyncio.create_task(
                            asyncio.to_thread(listener, event, context),
                        ))
                except Exception:
                    pass  #TODO
                    #print(f"Error creating task for listener: {e}")
            
            # 等待同一优先级的全部监听器执行完成
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理执行结果中的异常
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        print(f"Listener {context.mod.get_classname_by_instance(listeners[i].module)} failed with error: {result}")
                
                # 清理已完成的任务
                for task in tasks:
                    if not task.done():
                        task.cancel()

            if event.block_event:
                #事件被阻拦
                return False

        #事件被成功全部处理
        return True
    
    def clear_tasks(self):
        """清理所有任务"""
        for task in self.tasks:
            if not task.done():
                task.cancel()
        self.tasks.clear()