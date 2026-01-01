import random
from collections import deque
from typing import *
import json
import os
from logger import Logger

class Module:
    def __init__(self):
        '''WARNING:__init__会被自动加载器无参数使用，若要重写__init__，务必保证无参数调用'''
    #注意，加载与卸载函数应该是非异步的
    def register(self, message_handler, event_handler, module_handler):
        '''模块的初始化函数，是必须的，会被系统调用，若要重写，务必保证不要改变参数形式'''
    
    def unregister(self):
        '''模块的卸载函数，不是必须的'''
    



#暂未实现，目前单纯靠classname来区分不同module
#这个类相当于classname: str
class ModuleAttribute:

    #给用户看的名（如Example Module）
    name : str | None = None

    #注册名（如example_module）
    #目前暂时为类名
    register_name : str | None = None

    #是否是内置module
    is_builtin : bool = True

    #前置module
    #目前无用
    prerequisite : list[str] = []

    #版本
    version : str | None = None

    #作者
    author : str| None = None

    #描述
    desc : str | None = None

    def __str__(self) -> str:
        return f"Module {self.name} ({self.version}) by {self.author}: {self.desc}"

    def __repr__(self) -> str:
        return f"Module {self.name} ({self.version}) by {self.author}: {self.desc}"


    

            
    
class ModuleHandler:
    def __init__(self):
        self.__module = dict()
        self.__attribute = dict()

        # 构建依赖图和入度表
        self.graph: Dict[str, List[str]] = {}  # 模块依赖图
        self.reverse_graph: Dict[str, List[str]] = {}  # 反向依赖图：谁依赖我
        self.in_degree: Dict[str, int] = {}    # 每个模块的入度（前置依赖数量）
        self.modules_by_name: Dict[str, Any] = {}  # 模块名到模块实例的映射
        self.loaded_modules = set()  # 当前已加载的模块集合
        self.logger = Logger()

    # 给定json的目录路径，加载ModuleAttribute类
    def load_attribute(self, json_path: str) -> ModuleAttribute | None:
        
        attribute_data = None
        if os.path.exists(json_path):
            with open(json_path+'/attribute.json') as f:
                attribute_data=json.load(f)
        else:
            raise FileNotFoundError('\033[91m[Error]\033[0m路径下不存在attribute.json文件')
        try:
            attribute = ModuleAttribute( 
                name = attribute_data['name'],
                register_name = attribute_data['register_name'],
                version = attribute_data['version'],
                author = attribute_data['author'],
                desc = attribute_data['desc'])
        except Exception:
            self.logger
            raise Exception('\033[91m[Error]\033[0mModuleAttribute信息不完整')
        
        attribute.prerequisite = attribute_data['prerequisite'] if 'prerequisite' in attribute_data else []
        
        return attribute

    def register_module(self, instance:Module, attribute:ModuleAttribute):
        #用modulehandler.classname访问别的module类
        # 获取实例的类型名
        type_name = instance.__class__.__name__
        # 将实例的引用（而不是拷贝）作为属性添加到当前对象中
        setattr(self, type_name, instance)

        self.__module[attribute.register_name] = instance
        self.__attribute[attribute.register_name] = attribute

    def load_module(self, module_dict, message_handler):
        # 初始化数据结构
        for class_name, module_instance in module_dict.items():
            self.modules_by_name[class_name] = module_instance
            self.graph[class_name] = []
            self.reverse_graph[class_name] = []
            self.in_degree[class_name] = 0
        
        # 构建依赖关系
        for class_name, module_instance in module_dict.items():
            try:
                prerequisites = module_instance.prerequisite
            except:
                prerequisites = []
            
            for prereq in prerequisites:
                if prereq in self.graph:
                    # prereq -> class_name 的依赖关系
                    self.graph[prereq].append(class_name)
                    # 反向依赖：class_name 依赖于 prereq
                    self.reverse_graph[class_name].append(prereq)
                    self.in_degree[class_name] += 1
        
        # 拓扑排序：找到所有入度为0的模块（没有前置依赖）
        queue = deque([class_name for class_name, degree in self.in_degree.items() if degree == 0])
        load_order: List[str] = []
        
        # 处理循环依赖检测
        processed_count = 0
        
        while queue:
            current = queue.popleft()
            load_order.append(current)
            processed_count += 1
            
            # 减少依赖当前模块的其他模块的入度
            for dependent in self.graph[current]:
                self.in_degree[dependent] -= 1
                if self.in_degree[dependent] == 0:
                    queue.append(dependent)

        # 检查是否有循环依赖
        if processed_count != len(module_dict):
            # 找出形成循环的模块
            remaining = [class_name for class_name, degree in self.in_degree.items() if degree > 0]
            raise RuntimeError(f"[\033[31mERROR\033[0m]发现循环依赖，无法确定加载顺序。涉及模块: {remaining}")
        
        # 按照正确的顺序初始化模块
        for class_name in load_order:
            module_instance = self.modules_by_name[class_name]
            self.logger.debug('模块' + class_name + '已加载')
            # 模块的初始化
            module_instance.register(message_handler, message_handler.event_handler, self)
            # 将模块加入module管理器
            attribute = ModuleAttribute()
            attribute.resigter_name = class_name
            self.register_module(module_instance, attribute)
            self.loaded_modules.add(class_name)


    def unload_module(self, module:Module | ModuleAttribute | str, force_unload = False):
        register_name = ''
        instance = None
        if isinstance(module, Module):
            register_name = self.get_classname_by_instance(module)
            instance = module
        elif isinstance(module, ModuleAttribute):
            register_name = module.register_name
            instance = self.get_module_by_classname(register_name)
        elif isinstance(module, str):
            register_name = module
            instance = self.get_module_by_classname(register_name)
    

        if register_name not in self.loaded_modules:
            self.logger.error(f'模块 {register_name} 未加载，无法卸载')
            return []
        
        # 查找所有需要卸载的模块（BFS遍历依赖树）
        to_unload = []
        queue = deque([register_name])
        visited = set()
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            # 获取当前模块的依赖者
            dependents = self.get_all_dependents(current)
            
            # 如果有其他模块依赖此模块且不是强制卸载，则不能卸载
            if dependents and not force_unload:
                self.logger.warning(f'模块 {current} 被以下模块依赖，无法卸载: {dependents}')
                self.logger.info('使用 force_unload=True 可以强制卸载')
                return []
            
            # 添加到卸载列表
            to_unload.append(current)
            
            # 将所有依赖者也加入队列
            for dependent in dependents:
                queue.append(dependent)
        
        # 按照反向拓扑顺序卸载（先卸载依赖者，再卸载被依赖者）
        unloaded_modules = []
        for module_name in reversed(to_unload):
            if self._unload_single_module(module_name):
                unloaded_modules.append(module_name)
        
        return unloaded_modules
    
    def get_all_dependents(self, module_name: str) -> List[str]:
        """获取所有直接或间接依赖指定模块的模块"""
        dependents = []
        visited = set()
        
        def dfs(current):
            if current in visited:
                return
            visited.add(current)
            
            for dependent in self.graph.get(current, []):
                if dependent in self.loaded_modules:
                    dependents.append(dependent)
                    dfs(dependent)
        
        dfs(module_name)
        return dependents
    
    def _unload_single_module(self, module_name: str) -> bool:
        """卸载单个模块"""
        if module_name not in self.loaded_modules:
            return False
        
        try:
            # 获取模块实例
            instance = self.__module.get(module_name)
            if instance:
                # 调用模块的卸载函数
                if hasattr(instance, 'unregister'):
                    instance.unregister()
            
            # 从各种数据结构中移除
            if module_name in self.__module:
                del self.__module[module_name]
            
            if module_name in self.__attribute:
                del self.__attribute[module_name]
            
            # 从动态属性中移除
            if hasattr(self, module_name):
                delattr(self, module_name)
            
            # 从已加载集合中移除
            self.loaded_modules.remove(module_name)
            
            self.logger.debug(f'模块 {module_name} 已卸载')
            return True
            
        except Exception as e:
            self.logger.error(f'卸载模块 {module_name} 时出错: {e}')
            return False
    
    def unload_all(self):
        """卸载所有模块"""
        all_modules = list(self.loaded_modules)
        unloaded = []
        
        for module_name in all_modules:
            if self._unload_single_module(module_name):
                unloaded.append(module_name)
        
        self.logger.debug('已卸载所有模块')
        return unloaded
    
    def get_module_dependencies(self, module_name: str) -> Dict[str, List[str]]:
        """获取模块的依赖关系信息"""
        if module_name not in self.loaded_modules:
            return {}
        
        return {
            'module': module_name,
            'dependencies': self.reverse_graph.get(module_name, []),  # 依赖哪些模块
            'dependents': self.graph.get(module_name, [])  # 被哪些模块依赖
        }
    
    def is_safe_to_unload(self, module_name: str) -> bool:
        """检查是否可以安全卸载模块（没有其他模块依赖它）"""
        dependents = self.get_all_dependents(module_name)
        return len(dependents) == 0



    #通过module的类名获得module的实例
    def get_module_by_classname(self, classname):
        return getattr(self, classname, None)
    #通过module的实例获得module的类名
    def get_classname_by_instance(self,instance):
        return type(instance).__name__
    



####################################################################################




import sys
import importlib.util
import importlib
from pathlib import Path

def scan_module():
    """
    扫描/module_list目录下的所有.py文件，导入所有Module子类，
    创建实例并调用register()方法，返回所有实例列表
    """
    module_instances = {}
    module_classes = {}
    base_module_path = Path(__file__).parent / "module_list"
    
    def is_module_subclass(cls):
        """检查类是否是Module的子类且不是Module本身"""
        try:
            return (issubclass(cls, Module) and 
                   cls is not Module and 
                   cls.__module__ != 'builtins')
        except (TypeError, AttributeError):
            return False
    
    def import_module_from_file(file_path):
        """从文件路径导入模块"""
        # 将文件路径转换为模块名
        rel_path = file_path.relative_to(base_module_path)
        module_name = str(rel_path).replace(os.path.sep, '.').replace('.py', '')
        
        # 如果模块已经被导入过，直接返回
        if module_name in sys.modules:
            return sys.modules[module_name]
        
        # 使用importlib导入模块
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            Logger().error(f"Error importing module {module_name}: {e}")
            # 如果导入失败，从sys.modules中移除
            if module_name in sys.modules:
                del sys.modules[module_name]
            return None
    
    # 扫描所有.py文件
    py_files = []
    for root, dirs, files in os.walk(base_module_path):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                py_files.append(Path(root) / file)
    
    # 导入所有模块
    for py_file in py_files:
        module = import_module_from_file(py_file)
        if module is None:
            continue
            
        # 扫描模块中的所有类
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # 检查是否是类且是Module的子类
            if isinstance(attr, type) and is_module_subclass(attr):
                class_name = attr.__name__
                
                # 确保每个类只被导入一次
                if class_name not in module_classes:
                    module_classes[class_name] = attr
                    
                    try:
                        instance = attr()
                        if hasattr(instance, 'register'):
                            module_instances[class_name] = instance
                    except Exception as e:
                        Logger().error(f"Error instantiating {class_name} or calling register(): {e}")
    
    return module_instances

