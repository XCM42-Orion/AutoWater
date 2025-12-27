import pickle
import os
import time
from typing import *
from module import *
from pathlib import Path

class StorageEntry:
    def __init__(self, storage_dir, storage_id):
        self.storage_dir = storage_dir
        self._storage_registry = {}
        self._wrapped_objects = {}
        self.storage_id = storage_id
        os.makedirs(storage_dir, exist_ok=True)
    
    def bind(self, obj: Any, storage_id: str = None) -> Any:
        """绑定对象到存储管理器"""
        if storage_id is None:
            storage_id = self._generate_storage_id(obj)
        
        # 检查是否已有存储
        filepath = self._get_filepath(storage_id)
        exist = True
        data = None
        if os.path.exists(filepath):
            try:
                data = self._load_from_file(filepath)
                # 如果obj是内置类型，用数据更新它
                if isinstance(obj, (list, dict, set)):
                    if isinstance(obj, list):
                        obj[:] = data
                    elif isinstance(obj, dict):
                        obj.clear()
                        obj.update(data)
                    elif isinstance(obj, set):
                        obj.clear()
                        obj.update(data)
            except Exception as e:
                print(f"加载存储数据失败: {e}")
                raise e
        else:
            data = obj
            exist = False

        
        # 创建包装器
        wrapper = self._create_wrapper(data, storage_id)
        self._wrapped_objects[wrapper] = storage_id
        self._storage_registry[storage_id] = filepath

        if not exist:
            wrapper.save()
        
        return wrapper
    
    def _create_wrapper(self, obj: Any, storage_id: str) -> Any:
        """创建适当的包装器"""
        if isinstance(obj, list):
            return _StoredList(obj, storage_id, self)
        elif isinstance(obj, dict):
            return _StoredDict(obj, storage_id, self)
        elif isinstance(obj, set):
            return _StoredSet(obj, storage_id, self)
        elif isinstance(obj, (int, float, str, bool, bytes, type(None))):
            return _StoredImmutable(obj, storage_id, self)
        elif hasattr(obj, '__dict__'):
            # 自定义对象
            return _StoredObject(obj, storage_id, self)
        else:
            # 其他类型尝试包装
            return _StoredGeneric(obj, storage_id, self)
    
    def _save_to_file(self, storage_id: str, data: Any) -> None:
        """保存数据到文件"""
        filepath = self._get_filepath(storage_id)
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"保存失败: {e}")
    
    def _load_from_file(self, filepath: str) -> Any:
        """从文件加载数据"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    
    def _get_filepath(self, storage_id: str) -> str:
        """生成文件路径"""
        
        return os.path.join(self.storage_dir, storage_id + '.pkl')
    
    def _generate_storage_id(self, obj: Any) -> str:
        """生成存储标识符"""
        if self.storage_id:
            return self.storage_id
        #...其他特殊需求（暂无）

    def save(self):
        for wrapper, storage_id in self._wrapped_objects.items():
            wrapper.save()


# 基础包装器类
class _BaseWrapper:
    def __init__(self, wrapped_obj: Any, storage_id: str, manager: 'StorageEntry'):
        self._wrapped = wrapped_obj
        self._storage_id = storage_id
        self._manager = manager
    
    def __repr__(self):
        return f"Stored({repr(self._wrapped)})"
    
    def save(self):
        self._manager._save_to_file(self._storage_id, self._wrapped)
    
    def get_raw(self):
        """获取原始对象"""
        return self._wrapped
    
    def __hash__(self):
        return id(self)

def __eq__(self, other):
    return self is other

# List包装器
class _StoredList(_BaseWrapper, MutableSequence):
    def __init__(self, wrapped_list: list, storage_id: str, manager: 'StorageEntry'):
        super().__init__(wrapped_list, storage_id, manager)
    
    def __getitem__(self, index):
        return self._wrapped[index]
    
    def __setitem__(self, index, value):
        self._wrapped[index] = value
        self.save()
    
    def __delitem__(self, index):
        del self._wrapped[index]
        self.save()
    
    def __len__(self):
        return len(self._wrapped)
    
    def insert(self, index, value):
        self._wrapped.insert(index, value)
        self.save()
    
    def append(self, value):
        self._wrapped.append(value)
        self.save()
    
    def extend(self, values):
        self._wrapped.extend(values)
        self.save()
    
    def pop(self, index=-1):
        value = self._wrapped.pop(index)
        self.save()
        return value
    
    def remove(self, value):
        self._wrapped.remove(value)
        self.save()
    
    def clear(self):
        self._wrapped.clear()
        self.save()
    
    def __add__(self, other):
        return self._wrapped + other
    
    def __iadd__(self, other):
        self._wrapped += other
        self.save()
        return self

# Dict包装器
class _StoredDict(_BaseWrapper, MutableMapping):
    def __init__(self, wrapped_dict: dict, storage_id: str, manager: 'StorageEntry'):
        super().__init__(wrapped_dict, storage_id, manager)
    
    def __getitem__(self, key):
        return self._wrapped[key]
    
    def __setitem__(self, key, value):
        self._wrapped[key] = value
        self.save()
    
    def __delitem__(self, key):
        del self._wrapped[key]
        self.save()
    
    def __iter__(self):
        return iter(self._wrapped)
    
    def __len__(self):
        return len(self._wrapped)
    
    def clear(self):
        self._wrapped.clear()
        self.save()
    
    def update(self, other=None, **kwargs):
        if other:
            self._wrapped.update(other)
        if kwargs:
            self._wrapped.update(kwargs)
        self.save()
    
    def pop(self, key, default=None):
        value = self._wrapped.pop(key, default)
        self.save()
        return value
    
    def popitem(self):
        item = self._wrapped.popitem()
        self.save()
        return item
    
    def setdefault(self, key, default=None):
        value = self._wrapped.setdefault(key, default)
        if key not in self._wrapped:
            self.save()
        return value
    
    def get(self, key, default=None):
        return self._wrapped.get(key, default)

# Set包装器
class _StoredSet(_BaseWrapper, MutableSet):
    def __init__(self, wrapped_set: set, storage_id: str, manager: 'StorageEntry'):
        super().__init__(wrapped_set, storage_id, manager)
    
    def __contains__(self, value):
        return value in self._wrapped
    
    def __iter__(self):
        return iter(self._wrapped)
    
    def __len__(self):
        return len(self._wrapped)
    
    def add(self, value):
        if value not in self._wrapped:
            self._wrapped.add(value)
            self.save()
    
    def discard(self, value):
        if value in self._wrapped:
            self._wrapped.discard(value)
            self.save()
    
    def remove(self, value):
        self._wrapped.remove(value)
        self.save()
    
    def pop(self):
        value = self._wrapped.pop()
        self.save()
        return value
    
    def clear(self):
        self._wrapped.clear()
        self.save()
    
    def update(self, iterable):
        original_len = len(self._wrapped)
        self._wrapped.update(iterable)
        if len(self._wrapped) != original_len:
            self.save()

# 自定义对象包装器
class _StoredObject(_BaseWrapper):
    def __init__(self, wrapped_obj: Any, storage_id: str, manager: 'StorageEntry'):
        super().__init__(wrapped_obj, storage_id, manager)
        # 使用代理拦截属性访问
        self._setup_proxy()
    
    def _setup_proxy(self):
        """设置属性访问代理"""
        # 使用__getattr__和__setattr__拦截属性访问
        pass
    
    def __getattr__(self, name):
        '''if name.startswith('_'):
            return getattr(self._wrapped, name)
        else:
            self.save()'''
        return object.__getattribute__(object.__getattribute__(self,'_wrapped'), name)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            setattr(self._wrapped, name, value)
            self.save()

# 不可变类型包装器
class _StoredImmutable(_BaseWrapper):
    def __init__(self, wrapped_obj: Any, storage_id: str, manager: 'StorageEntry'):
        super().__init__(wrapped_obj, storage_id, manager)
    
    @property
    def value(self):
        return self._wrapped
    
    @value.setter
    def value(self, new_value):
        self._wrapped = new_value
        self.save()

# 通用包装器（用于其他类型）
class _StoredGeneric(_BaseWrapper):
    pass

from module import *
from event import *
from message_utils import *
from pathlib import Path


class storage(Module):
    def __init__(self):
        self._bound_objects = {}

    def register(self, message_handler, event_handler, mod):
        pass

    def permanent(self, obj, module, storage_id):
        storage_path = Path(__file__).parent / 'storaged_data' / module.__class__.__name__

        if storage_path.exists() and storage_path.is_dir():
            pass
        else:
            storage_root = Path(__file__).parent / 'storaged_data'
            if not (storage_root.exists() and storage_root.is_dir()):
                os.mkdir(storage_root)
            os.mkdir(storage_path)


        manager = StorageEntry(str(storage_path), storage_id)

        #manager.bind(time.time(), storage_id + '_last_modified_time')

        self._bound_objects[storage_id] = manager
        return manager.bind(obj, storage_id)

    def unregister(self):
        for storage_id, manager in self._bound_objects.items():
            manager.save()