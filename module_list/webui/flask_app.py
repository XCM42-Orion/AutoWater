"""
Flask配置管理应用主文件
提供Web界面和API来管理应用配置
"""
from flask import Flask, render_template, request, jsonify
import json
import os



class FlaskApp:
    def __init__(self, config_manager):
        
        module_dir = os.path.dirname(os.path.abspath(__file__))
        self.app = Flask(
        'autowater',
        template_folder=os.path.join(module_dir, 'templates'),
        static_folder=os.path.join(module_dir, 'static'),
        instance_path=module_dir
        )

        # 初始化配置管理器
        self.config_manager = config_manager

        self.register_routes()
        self.run()


    def register_routes(self):
        @self.app.route('/')
        def index():
            """显示配置管理页面"""
            return render_template('index.html', 
                                app_config=self.config_manager.get_config(),
                                config_json=json.dumps(self.config_manager.get_config(), indent=2))

        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """API: 获取当前配置"""
            return jsonify({
                'success': True,
                'config': self.config_manager.get_config()
            })

        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """API: 更新配置"""
            try:
                data = request.json
                
                if not data:
                    return jsonify({
                        'success': False,
                        'message': '未提供配置数据'
                    }), 400
                
                # 更新配置
                success = self.config_manager.update_config(data)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': '配置更新成功',
                        'config': self.config_manager.get_config()
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': '配置保存失败'
                    }), 500
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'更新配置时出错: {str(e)}'
                }), 500

        @self.app.route('/api/config/value', methods=['POST'])
        def update_config_value():
            """API: 更新单个配置值"""
            try:
                data = request.json
                
                if not data or 'key' not in data or 'value' not in data:
                    return jsonify({
                        'success': False,
                        'message': '需要key和value参数'
                    }), 400
                
                key = data['key']
                value = data['value']
                
                # 更新单个值
                success = self.config_manager.update_value(key, value)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'配置项 {key} 更新成功',
                        'key': key,
                        'value': value
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': '配置保存失败'
                    }), 500
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'更新配置项时出错: {str(e)}'
                }), 500

        @self.app.route('/api/config/<module_name>')
        def get_module_configs(module_name):
            """获取指定模块的配置项"""
            try:
                configs = self.config_manager.get_registered_configs()
                
                if module_name not in configs:
                    return jsonify({
                        'success': False,
                        'message': f'模块 {module_name} 不存在'
                    }), 404
                
                return jsonify({
                    'success': True,
                    'module': module_name,
                    'configs': configs[module_name]
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'获取配置项失败: {str(e)}'
                }), 500
            
        @self.app.route('/api/modules')
        def get_modules():
            """获取所有模块的配置信息"""
            try:
                configs = self.config_manager.get_registered_configs()
                
                # 获取模块列表
                modules = []
                for module_name in configs.keys():
                    # 统计该模块的配置项数量
                    item_count = len(configs[module_name])
                    modules.append({
                        'name': module_name,
                        'display_name': module_name,
                        'item_count': item_count
                    })
                
                return jsonify({
                    'success': True,
                    'modules': modules
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'获取模块列表失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/config/batch', methods=['POST'])
        def update_config_batch():
            """批量更新配置值"""
            try:
                data = request.json
                
                if not data or 'updates' not in data:
                    return jsonify({
                        'success': False,
                        'message': '需要updates参数'
                    }), 400
                
                updates = data['updates']
                results = []
                
                for update in updates:
                    name = update.get('name')
                    value = update.get('value')
                    
                    if name is None or value is None:
                        continue
                    
                    success = self.config_manager.config.update_config_value(name, value)
                    results.append({
                        'name': name,
                        'success': success
                    })
                
                # 获取所有配置的当前状态
                configs = self.config_manager.get_registered_configs()
                
                return jsonify({
                    'success': True,
                    'message': f'批量更新完成，成功 {sum(1 for r in results if r["success"])} 项',
                    'results': results,
                    'configs': configs
                })
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'批量更新配置时出错: {str(e)}'
                }), 500
        
        @self.app.route('/api/config/all')
        def get_all_configs():
            """获取所有配置项"""
            try:
                configs = self.config_manager.get_registered_configs()
                return jsonify({
                    'success': True,
                    'configs': configs
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'获取配置失败: {str(e)}'
                }), 500

        @self.app.route('/health')
        def health_check():
            """健康检查端点"""
            return jsonify({
                'status': 'healthy',
                'self.app_name': 'autowater',
                'debug_mode': False
            })

    def run(self):
        # 从配置中读取主机和端口
        host = '127.0.0.1'#self.config_manager.get_value('host', '127.0.0.1')
        port = 5000#self.config_manager.get_value('port', 5000)
        debug = False#self.config_manager.get_value('debug_mode', False)
        
        #print(f"启动应用: {self.config_manager.get_value('self.app_name')}")
        #print(f"访问地址: http://{host}:{port}")
        #print(f"调试模式: {debug}")
        
        self.app.run(host=host, port=port, debug=debug)