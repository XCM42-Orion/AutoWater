from module import *
from message_utils import *
import logger

import asyncio
import math

import threading

class CallableHookEventData:
    '''注意,ret是一个列表，要访问返回值应该使用ret[0]'''
    def __init__(self, ret, target, args, kwargs, bypass_calling=False):
        self.ret = ret
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.bypass_calling = bypass_calling

class EventType:
    event_id_count = 5

    EVENT_UNDEFINED = -1       #data : Any
    EVENT_INIT = 0             #data : None
    EVENT_RECV_MSG = 1         #data : Message
    EVENT_SEND_MSG = 2         #data : tuple[EventContext(Proxy),Message]
    EVENT_NOTICE_MSG = 3



    SPECIAL_APPLY_CONTEXT = 4       #如果module中需要申请一个context来沟通，此context中的操作仍然将被视为一个事件

    class CustomEventNamespace:
        def __init__(self, module_name):
            self.module_name = module_name

    targets_of_callable_hook_events = {}

    def register_event(name, module: str | Module):
        if isinstance(module, Module):
            module_name = module.__class__.__name__
        else:
            module_name = module

            
        if not hasattr(EventType, module_name):
            setattr(EventType, module_name, EventType.CustomEventNamespace(module_name))
        setattr(getattr(EventType, module_name), name, EventType.event_id_count)
        EventType.event_id_count += 1

    def register_callable_hook_event(name, module:Module, target:Callable, event_handler):
        '''只支持Module内注册hook event'''
        '''**记得使用此函数的返回值*覆盖*你需要hook的Callable对象'''
        '''原函数在优先级0被调用，此后可以通过event.data[0]来修改返回值'''
        '''如果要修改返回值，注意不能直接return，而是要通过event.data.ret.append(返回值)
        （注意，不可以覆盖ret的列表，这会导致返回值无法读取)，也就是只能通过append来添加返回值）来修改被hook函数的返回值'''
        if isinstance(module, Module):
            module_name = module.__class__.__name__
        else:
            module_name = module

            
        if not hasattr(EventType, module_name):
            setattr(EventType, module_name, EventType.CustomEventNamespace(module_name))
        setattr(getattr(EventType, module_name), name, EventType.event_id_count)
        EventType.targets_of_callable_hook_events[EventType.event_id_count] = target

        event_type = EventType.event_id_count


        def _wrapper_event_sync(*args,**kwargs):
            ret = list()
            event = Event(event_type, CallableHookEventData(ret,target,args,kwargs))
            # 创建一个新的事件循环并在新线程中运行
            loop = asyncio.new_event_loop()
            result = None
            exception = None

            def run():
                nonlocal result, exception
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        event_handler.dispatch_custom_event(event, module)
                    )
                except Exception as e:
                    raise e
                finally:
                    loop.close()

            thread = threading.Thread(target=run)
            thread.daemon = True
            thread.start()
            thread.join()

            if exception is not None:
                raise exception
            result = ret[0]
            return result
        
        async def _wrapper_event_async(*args,**kwargs):
            ret = list()

            event = Event(event_type, CallableHookEventData(ret,target,args,kwargs))
            await event_handler.dispatch_custom_event(event, module)

            result = ret[0]
            return result

        async def _wrapper_call(event, context):
            if not event.data.bypass_calling:
                if asyncio.iscoroutinefunction(event.data.target):
                    event.data.ret.append(await event.data.target(*event.data.args,**event.data.kwargs))
                else:
                    event.data.ret.append(event.data.target(*event.data.args,**event.data.kwargs))

        event_handler._inner_register_listener(module, event_type, _wrapper_call, 0)

        EventType.event_id_count += 1

        return _wrapper_event_async if asyncio.iscoroutinefunction(target) else _wrapper_event_sync

from collections import defaultdict
from typing import *
import json
from message_utils import *
import functools

#现在可以自定义event了

class Event:
    def __init__(self,event_type: EventType,data: Any):
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

        #事件被哪些module处理过
        #形式：dict[module_classname(str):priority(int)]
        self.history = []

        #标记初始化完成防止__setattr__拦截__init__里面的设置行为
        self.status = 1
    
    def block_event(self):
        self.blocked = True

from history import *

#区分不同函数对Context的使用，便于实现日志记录、钩子等
#现在可以截获所有对context.mod的使用——llm计费等功能成为可能
#目前hook只能装在event上，后期可能会支持装在所有的config.mod访问上，可以拦截访问或返回修改后的信息
class EventContextProxy:
    class MessageHandlerProxy:
        def __init__(self, context_proxy, module: Module, message_handler):
            self.module = module
            self.message_handler = message_handler
            self.context_proxy = context_proxy

        def __getattr__(self, name: str):
            target = getattr(self.message_handler, name, None)

            if target == None:
                return object.__getattribute__(self, name)

            if isinstance(target, Callable):
                if name == 'send_message' or name == 'send_emoji_like' or name == 'send_poke':
                    @functools.wraps(target)
                    async def wrapper(*args, **kwargs):
                        kwargs['module'] = self.module
                        kwargs['proxy'] = self
                        
                        # 调用原始方法
                        return await target(*args, **kwargs)
                
                    return wrapper
                else:
                    return target
            else:
                return target
        #send_message反馈:发送了什么信息
        def feedback(self, data):
            self.context_proxy.update_history(Action(ActionType.ACTION_MSG_SEND, data, self.module, self.context_proxy.event))


    def __init__(self, module: Module, event_context,event: Event):
        #该context所有者信息
        self.module = module
        self.event_context = event_context

        #该context所有者正处于的过程
        self.event = event

        #管理context生命周期:context不能长时间保留，只能随取随用，用完自动销毁
        self.valid = True

        #记录当前context作用域内的活动记录
        self.history = list()

        self.message_handler_proxy = self.MessageHandlerProxy(self, module, event_context.message_handler)
        self.logger = list()


    def __getattr__(self, name: str):
        if not self.valid:
            if name != 'update_history' and name != 'dump_history':
                raise BaseException("无效的context: context生命周期已结束并被销毁")
        
        if name == 'destroy':
            self.valid = False
            #销毁总会成功
            return lambda: True

        ########################
        if name == 'update_history':
            return self.update_history
        elif name == 'dump_history':
            return self.dump_history
        ########################

        if name == 'message_handler':
            return self.message_handler_proxy
        else:
            return getattr(self.event_context, name)

    def update_history(self, action):
        self.history.append(action)

    def dump_history(self):
        return self.history

#把原来的config,messagehandler等等东西扔在一起，并方便不同module通信
#通信方法：context.mod.<类名>
class EventContext:
    def __init__(self):
        self.message_handler = None
        self.event_handler = None

        #其实就是module_handler，写成mod是为了好看，方便调用别的module的内容
        self.mod = None

        #这个context是哪个module拥有的
        self.owner: str = None
        
        self.utilities = None
        self.log = None



#把listener和module联系起来并记录listener的响应函数，可以被直接当作函数调用，对module透明
class Listener:
    def __init__(self, module: Module, callback: Callable, event_type: EventType):
        self.module = module
        self.module_classname = type(module).__name__
        self.callback = callback
        self.event_type = event_type
        self.pre_hook = []
        self.post_hook = []

    def add_pre_hook(self, source_module_classname: str, hook_callback: Callable, priority):
        self.pre_hook.append((priority, source_module_classname, hook_callback))
    
    def add_post_hook(self, source_module_classname: str, hook_callback: Callable, priority):
        self.post_hook.append((priority, source_module_classname, hook_callback))

    async def call_async(self, event: Event, context: EventContextProxy) -> Any:
        """
        将任意参数转发给callback函数，并处理hook和history记录逻辑（异步，当callback为coroutinue时调用）
        
        参数:
            *args: 任意位置参数
            **kwargs: 任意关键字参数
            
        返回:
            callback函数的返回值
        """
        for each in sorted(self.pre_hook, key=lambda x: x[0], reverse=True):
            #pre_hook返回False将导致消息被拦截，不会发送给listener
            if not each[2](each[1], event, context):
                return False
            


        ret = await self.callback(event, context)

        context.update_history(Action(ActionType.ACTION_RETURN, ret, self.module, event))

        for each in sorted(self.post_hook, key=lambda x: x[0], reverse=True):
            #post_hook返回False将导致消息被认为失败
            #post_hook回调格式：callback(被hook的module类名,listener返回值,事件,context,这个listener处理过程中产生了什么action
            if not each[2](each[1], ret, event, context, context.dump_history()):
                return False
            
        context.destroy()
        return ret

    def call_sync(self, event: Event, context: EventContextProxy) -> Any:
        """
        将任意参数转发给callback函数，并处理hook和history记录逻辑（同步版，当callback为普通函数时调用）
        
        参数:
            *args: 任意位置参数
            **kwargs: 任意关键字参数
            
        返回:
            callback函数的返回值
        """
        for each in sorted(self.pre_hook, key=lambda x: x[0], reverse=True):
            #pre_hook返回False将导致消息被拦截，不会发送给listener
            if not each[2](each[1], event, context):
                return False
            

        ret =  self.callback(event, context)

        context.update_history(Action(ActionType.ACTION_RETURN, ret, self.module, event))

        for each in sorted(self.post_hook, key=lambda x: x[0], reverse=True):
            #post_hook返回False将导致消息被认为失败
            #post_hook回调格式：callback(被hook的module类名,listener返回值,事件,context,这个listener处理过程中产生了什么action
            if not each[2](each[1], ret, event, context, context.dump_history()):
                return False
            
        context.destroy()
        return ret






#################################################################################################################################
#EventHandler核心实现


class EventHandler:
    def __init__(self, message_handler):
        # 存储监听器的数据结构
        # event_type -> priority -> list[listener]
        self.listeners: Dict[EventType, Dict[int, List[Listener]]] = defaultdict(
            lambda: defaultdict(list)
        )
        # 存储协程任务
        self.tasks: List[asyncio.Task] = []
        self.message_handler = message_handler
    
    def _inner_register_listener(self, module: Module, event_type: EventType, callback: Callable, priority: int):
        """注册监听器，可以指定优先级"""
        """仅供message_handler使用，注册时请使用message_handler.register_listener"""
        '''WARNING:priority越大越优先'''
        self.listeners[event_type][priority].append(Listener(module, callback, event_type))

    def register_pre_hook(self, module: Module, targeted_module_classname: str, event_type: EventType, callback: Callable, priority:int = 0):
        #*或EVENT_UNDEFINED表示通配符
        if self.listeners.get(event_type):
            if event_type != EventType.EVENT_UNDEFINED:
                for priority, listeners in self.listeners[event_type]:
                    for index, each_listener in enumerate(listeners):
                        if each_listener.module_classname == targeted_module_classname:
                            self.listeners[event_type][priority][index].add_pre_hook(targeted_module_classname, callback, priority)
                            return True
            else:
                for each_event_type in self.listeners:
                    for priority, listeners in each_event_type:
                        for index, each_listener in enumerate(listeners):
                            if each_listener.module_classname == targeted_module_classname:
                                self.listeners[event_type][priority][index].add_pre_hook(targeted_module_classname, callback, priority)
                                return True
            return False
        else:
            return False
        
    def register_post_hook(self, module: Module, targeted_module_classname: str, event_type: EventType, callback: Callable, priority:int = 0):
        #*或EVENT_UNDEFINED表示通配符
        #注意！！！post_hook优先级越高，执行得越早（而不是越晚!）
        if self.listeners.get(event_type):
            if event_type != EventType.EVENT_UNDEFINED:
                for priority, listeners in self.listeners[event_type]:
                    for index, each_listener in enumerate(listeners):
                        if each_listener.module_classname == targeted_module_classname:
                            self.listeners[event_type][priority][index].add_post_hook(targeted_module_classname, callback, priority)
                            return True
            else:
                for each_event_type in self.listeners:
                    for priority, listeners in each_event_type:
                        for index, each_listener in enumerate(listeners):
                            if each_listener.module_classname == targeted_module_classname:
                                self.listeners[event_type][priority][index].add_post_hook(targeted_module_classname, callback, priority)
                                return True
            return False
        else:
            return False
        
    def apply_for_context(self, module: Module) -> EventContext:
        """申请一个context供module使用，此context内的所有操作都会被记录为SPECIAL_APPLY_CONTEXT"""
        context = EventContext()
        context.message_handler = self.message_handler
        context.event_handler = self
        context.mod = self.message_handler.module_handler
        context.owner = type(module).__name__
        context.log = self.message_handler.logger

        event = Event(EventType.SPECIAL_APPLY_CONTEXT,None)

        proxy = EventContextProxy(module, context, event)

        return proxy
    
    async def dispatch_event(self, event: Event, context: EventContext):
        await self._dispatch_event(event, context)

    async def dispatch_custom_event(self, event: Event, module: Module):
        await self.dispatch_event(event, self.apply_for_context(module))
    
    async def _dispatch_event(self, event: Event, real_context: EventContext):
        event_type = event.event_type

        """分发事件，按照优先级顺序执行"""
        if event_type not in self.listeners:
            return

        # 获取该事件类型的所有监听器
        corresponding_listeners = self.listeners[event_type]   #得到Dict[Priority(以int表示), List[Callable]]
        
        # 按优先级从高到低排序
        sorted_priorities = sorted(corresponding_listeners.keys(), reverse=True)
        


        for priority in sorted_priorities:
            #获取当前优先级的监听器
            listeners = corresponding_listeners[priority]

            #如果当前优先级没有任何监听器
            if not listeners:
                continue
            
            # 为同一优先级的监听器创建协程任务
            tasks = []

            for listener in listeners:
                #一个context代理
                context = EventContextProxy(listener.module, real_context, event)
                loop = asyncio.get_running_loop()
                try:
                    if asyncio.iscoroutinefunction(listener.callback):
                        # 如果是协程函数，直接创建任务
                        tasks.append(asyncio.create_task(
                            listener.call_async(event, context)
                        ))
                    else:
                        # 请尽可能使用协程函数
                        tasks.append(
                            loop.run_in_executor(None, listener.call_sync, event, context)
                        )
                except Exception as e:
                    print(f"Error creating task for listener: {e}")

            # 等待同一优先级的全部监听器执行完成
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=not logger.debug_flag)
                
                # 处理执行结果中的异常
                for i, result in enumerate(results):
                    #便于追踪这个消息被哪些module处理过，结果如何，这些module有没有发信息
                    event.history.extend(context.dump_history())
                    if isinstance(result, Exception):
                        #这里不要使用mod.get_classname_by_instance，因为context已经被销毁。注意,context在对应listener执行完会被立刻销毁，只能在用户的module内使用
                        print(f"Listener {type(listeners[i].module).__name__} failed with error {type(result)}: {result}")
                
                #清理已完成的任务
                for task in tasks:
                    if not task.done():
                        task.cancel()

            if event.blocked:
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