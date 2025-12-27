/**
 * AutoWater配置管理应用 - 前端脚本
 * 动态加载模块和配置项，支持按类型渲染表单
 */

document.addEventListener('DOMContentLoaded', function() {
    // 全局状态
    const state = {
        currentModule: null,
        modules: [],
        configs: {},
        unsavedChanges: new Map(),
        searchQuery: ''
    };
    
    // DOM元素
    const moduleList = document.getElementById('module-list');
    const configContainer = document.getElementById('config-container');
    const currentModuleTitle = document.getElementById('current-module-title');
    const currentModuleDescription = document.getElementById('current-module-description');
    const configActions = document.getElementById('config-actions');
    const unsavedCount = document.getElementById('unsaved-count');
    const configSearch = document.getElementById('config-search');
    const jsonEditor = document.getElementById('json-editor');
    
    // 初始化
    loadModules();
    setupEventListeners();
    setupHealthCheck();
    
    /**
     * 设置事件监听器
     */
    function setupEventListeners() {
        // 搜索框
        /*configSearch.addEventListener('input', function(e) {
            state.searchQuery = e.target.value.toLowerCase();
            if (state.currentModule) {
                renderModuleConfigs(state.currentModule);
            }
        });*/
        
        // 刷新所有
        document.getElementById('refresh-all-btn').addEventListener('click', loadModules);
        
        // 保存全部
        document.getElementById('save-all-btn').addEventListener('click', saveAllChanges);
        
        // 重置模块
        document.getElementById('reset-module-btn').addEventListener('click', resetCurrentModule);
        
        // 应用更改
        document.getElementById('apply-changes-btn').addEventListener('click', applyChanges);
        
        // 取消更改
        document.getElementById('cancel-changes-btn').addEventListener('click', cancelChanges);
        
        // JSON相关
        document.getElementById('validate-json-btn').addEventListener('click', validateJson);
        document.getElementById('apply-json-btn').addEventListener('click', applyJson);
        document.getElementById('export-json-btn').addEventListener('click', exportJson);
        
        // 日志相关
        document.getElementById('clear-log-btn').addEventListener('click', clearLog);
        
        // 模态框
        document.getElementById('close-json-modal').addEventListener('click', closeJsonModal);
        document.getElementById('copy-json-btn').addEventListener('click', copyJsonToClipboard);
        document.getElementById('download-json-btn').addEventListener('click', downloadJson);
        
        // 点击外部关闭模态框
        /*document.getElementById('json-modal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeJsonModal();
            }
        });*/
    }
    
    /**
     * 设置健康检查
     */
    function setupHealthCheck() {
        setInterval(() => {
            fetch('/health')
                .then(response => response.json())
                .then(data => {
                    const statusEl = document.getElementById('system-status');
                    if (data.status === 'healthy') {
                        statusEl.textContent = '运行中';
                        statusEl.className = 'status-indicator healthy';
                    } else {
                        statusEl.textContent = '异常';
                        statusEl.className = 'status-indicator error';
                    }
                })
                .catch(() => {
                    const statusEl = document.getElementById('system-status');
                    statusEl.textContent = '连接失败';
                    statusEl.className = 'status-indicator error';
                });
        }, 30000);
    }
    
    /**
     * 加载所有模块
     */
    function loadModules() {
        moduleList.innerHTML = '<div class="loading-modules"><i class="fas fa-spinner fa-spin"></i> 加载模块中...</div>';
        
        fetch('/api/modules_module')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    state.modules = data.modules;
                    renderModuleList();
                    
                    // 更新统计信息
                    document.getElementById('module-count').textContent = state.modules.length;
                    
                    addLog('模块列表加载成功', 'success');
                } else {
                    addLog(`加载模块失败: ${data.message}`, 'error');
                    showToast('加载模块失败', 'error');
                }
            })
            .catch(error => {
                addLog(`加载模块时发生错误: ${error.message}`, 'error');
                showToast('网络错误，请检查连接', 'error');
            });
    }
    
    /**
     * 渲染模块列表
     */
    function renderModuleList() {
        if (state.modules.length === 0) {
            moduleList.innerHTML = '<div class="empty-state">暂无模块</div>';
            return;
        }
        
        moduleList.innerHTML = '';
        
        state.modules.forEach(module => {
            const moduleEl = document.createElement('div');
            moduleEl.className = `module-item ${state.currentModule === module.name ? 'active' : ''}`;
            moduleEl.innerHTML = `
                <span class="module-name">${module.display_name}</span>
                <span class="module-count">${module.item_count}</span>
            `;
            
            moduleEl.addEventListener('click', () => {
                selectModule(module.name);
            });
            
            moduleList.appendChild(moduleEl);
        });
    }
    
    /**
     * 选择模块
     */
    function selectModule(moduleName) {
        if (state.currentModule === moduleName) return;

        // 检查是否有未保存的更改
        if (state.unsavedChanges.size > 0 && state.currentModule) {
            if (!confirm(`当前模块有 ${state.unsavedChanges.size} 项未保存的更改，切换模块将丢失这些更改。确定要切换吗？`)) {
                return;
            }
            state.unsavedChanges.clear();
            updateUnsavedCount();
        }
        
        state.currentModule = moduleName;
        
        // 更新UI
        document.querySelectorAll('.module-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const selectedItem = Array.from(document.querySelectorAll('.module-item'))
            .find(item => item.querySelector('.module-name').textContent === 
                  moduleName);

        if (selectedItem) {
            selectedItem.classList.add('active');
        }
        
        // 加载模块配置
        loadModuleConfigs(moduleName);
        renderModuleConfigs(moduleName);
    }
    
    /**
     * 加载模块配置
     */
    function loadModuleConfigs(moduleName) {
        currentModuleTitle.textContent = moduleName;
        currentModuleDescription.textContent = `配置项: ${state.modules.find(m => m.name === moduleName)?.item_count || 0} 个`;
        
        configContainer.innerHTML = '<div class="loading-modules"><i class="fas fa-spinner fa-spin"></i> 加载配置中...</div>';
        configActions.style.display = 'none';
        
        fetch(`/api/config/${moduleName}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    state.configs[moduleName] = data.configs;
                    renderModuleConfigs(moduleName);
                    addLog(`已加载模块 "${moduleName}" 的配置`, 'success');
                } else {
                    configContainer.innerHTML = `<div class="empty-state">
                        <i class="fas fa-exclamation-triangle fa-3x"></i>
                        <h3>加载失败</h3>
                        <p>${data.message}</p>
                    </div>`;
                    addLog(`加载配置失败: ${data.message}`, 'error');
                }
            })
            .catch(error => {
                configContainer.innerHTML = `<div class="empty-state">
                    <i class="fas fa-exclamation-triangle fa-3x"></i>
                    <h3>加载失败</h3>
                    <p>${error.message}</p>
                </div>`;
                addLog(`加载配置时发生错误: ${error.message}`, 'error');
            });
    }
    
    /**
     * 渲染模块配置
     */
    function renderModuleConfigs(moduleName) {
        const configs = state.configs[moduleName];
        if (!configs || configs.length === 0) {
            configContainer.innerHTML = '<div class="empty-state">该模块暂无配置项</div>';
            return;
        }
        
        // 按路径分组
        const groupedConfigs = {};
        configs.forEach(config => {
            const path = config.path || config.name;
            const parts = path.split('.');
            const group = parts.length > 1 ? parts[0] : 'general';
            
            if (!groupedConfigs[group]) {
                groupedConfigs[group] = [];
            }
            
            // 过滤搜索结果
            if (state.searchQuery && 
                !config.name.toLowerCase().includes(state.searchQuery) &&
                !path.toLowerCase().includes(state.searchQuery)) {
                return;
            }
            
            groupedConfigs[group].push(config);
        });
        
        // 生成HTML
        let html = '<div class="config-form">';
        
        Object.keys(groupedConfigs).sort().forEach(group => {
            const groupConfigs = groupedConfigs[group];
            if (groupConfigs.length === 0) return;
            
            html += `
                <div class="config-group">
                    <div class="config-group-header">
                        <h3><i class="fas fa-folder"></i> ${group === 'general' ? '常规配置' : group}</h3>
                    </div>
                    <div class="config-items">
            `;
            
            groupConfigs.forEach(config => {
                html += renderConfigItem(config);
            });
            
            html += `
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        configContainer.innerHTML = html;
        
        // 绑定表单事件
        bindConfigEvents();
        
        // 更新JSON编辑器
        updateJsonEditor();
    }
    
    /**
     * 渲染单个配置项
     */
    function renderConfigItem(config) {
        const currentValue = state.unsavedChanges.has(config.name) 
            ? state.unsavedChanges.get(config.name) 
            : config.current;
        
        let inputField = '';
        const configType = config.type.toLowerCase();
        
        switch (configType) {
            case 'bool':
            case 'boolean':
                inputField = `
                    <input type="checkbox" 
                           class="config-control" 
                           id="config-${config.name}" 
                           ${currentValue ? 'checked' : ''}>
                `;
                break;
                
            case 'int':
            case 'integer':
            case 'float':
                inputField = `
                    <input type="number" 
                           class="config-control" 
                           id="config-${config.name}" 
                           value="${currentValue}" 
                           step="${configType === 'float' ? '0.1' : '1'}">
                `;
                break;
                
            case 'list':
            case 'array':
                const listValue = Array.isArray(currentValue) ? currentValue.join(', ') : String(currentValue);
                inputField = `
                    <textarea class="config-control" 
                              id="config-${config.name}" 
                              rows="3">${listValue}</textarea>
                    <div class="config-description">多个值用逗号分隔</div>
                `;
                break;
                
            case 'dict':
            case 'object':
                const dictValue = typeof currentValue === 'object' 
                    ? JSON.stringify(currentValue, null, 2) 
                    : String(currentValue);
                inputField = `
                    <textarea class="config-control" 
                              id="config-${config.name}" 
                              rows="4">${dictValue}</textarea>
                    <div class="config-description">JSON格式</div>
                `;
                break;
                
            case 'str':
            case 'string':
            default:
                const isLongText = String(currentValue).length > 50;
                if (isLongText) {
                    inputField = `
                        <textarea class="config-control" 
                                  id="config-${config.name}" 
                                  rows="3">${currentValue}</textarea>
                    `;
                } else {
                    inputField = `
                        <input type="text" 
                               class="config-control" 
                               id="config-${config.name}" 
                               value="${currentValue}">
                    `;
                }
                break;
        }
        
        return `
            <div class="config-item">
                <label for="config-${config.name}">
                    <span>${config.name}</span>
                    <span class="config-type">${config.type}</span>
                </label>
                ${inputField}
                <div class="config-value-info">
                    <span class="default-value">默认: ${JSON.stringify(config.default)}</span>
                    ${state.unsavedChanges.has(config.name) ? 
                        '<span class="current-value" style="color: var(--warning-color);">(已修改)</span>' : 
                        '<span class="current-value">当前: ' + JSON.stringify(config.current) + '</span>'}
                </div>
            </div>
        `;
    }
    
    /**
     * 绑定配置项事件
     */
    function bindConfigEvents() {
        document.querySelectorAll('.config-control').forEach(input => {
            const configName = input.id.replace('config-', '');
            
            input.addEventListener('input', function() {
                let value = this.value;
                
                // 根据输入类型处理值
                if (this.type === 'checkbox') {
                    value = this.checked;
                } else if (this.type === 'number') {
                    value = this.valueAsNumber;
                }
                
                // 保存到未更改列表
                state.unsavedChanges.set(configName, value);
                updateUnsavedCount();
                
                
                // 高亮显示已修改的项
                const configItem = this.closest('.config-item');
                const currentValueSpan = configItem.querySelector('.current-value');
                if (currentValueSpan) {
                    currentValueSpan.innerHTML = '<span style="color: var(--warning-color);">(已修改)</span>';
                }
            });
        });
    }
    
    /**
     * 更新未保存计数
     */
    function updateUnsavedCount() {
        const count = state.unsavedChanges.size;
        unsavedCount.textContent = `${count} 项未保存`;
        
        if (count > 0) {
            configActions.style.display = 'flex';
        } else {
            configActions.style.display = 'none';
        }
    }
    
    /**
     * 应用更改
     */
    function applyChanges() {
        if (state.unsavedChanges.size === 0) return;
        
        const updates = Array.from(state.unsavedChanges.entries()).map(([name, value]) => ({
            name, value
        }));
        
        fetch('/api/config/batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ updates })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 清空未保存列表
                state.unsavedChanges.clear();
                updateUnsavedCount();
                
                // 更新配置数据
                if (data.configs && state.currentModule) {
                    state.configs[state.currentModule] = data.configs[state.currentModule] || [];
                }
                
                // 重新渲染
                renderModuleConfigs(state.currentModule);
                
                addLog(`已保存 ${updates.length} 项配置更改`, 'success');
                showToast('配置保存成功', 'success');
            } else {
                addLog(`保存失败: ${data.message}`, 'error');
                showToast(`保存失败: ${data.message}`, 'error');
            }
        })
        .catch(error => {
            addLog(`保存时发生错误: ${error.message}`, 'error');
            showToast('网络错误，请检查连接', 'error');
        });
    }
    
    /**
     * 取消更改
     */
    function cancelChanges() {
        if (state.unsavedChanges.size === 0) return;
        
        if (confirm(`确定要取消 ${state.unsavedChanges.size} 项更改吗？`)) {
            state.unsavedChanges.clear();
            updateUnsavedCount();
            renderModuleConfigs(state.currentModule);
            addLog('已取消所有未保存的更改', 'warning');
        }
    }
    
    /**
     * 重置当前模块
     */
    function resetCurrentModule() {
        if (!state.currentModule) return;
        
        if (confirm('确定要重置该模块的所有配置为默认值吗？')) {
            // 这里可以调用重置API，如果没有API则只重置本地状态
            state.unsavedChanges.clear();
            loadModuleConfigs(state.currentModule);
            addLog(`已重置模块 "${state.currentModule}" 的配置`, 'warning');
            showToast('模块配置已重置', 'warning');
        }
    }
    
    /**
     * 保存所有更改
     */
    function saveAllChanges() {
        if (state.unsavedChanges.size === 0) {
            showToast('没有需要保存的更改', 'info');
            return;
        }
        
        applyChanges();
    }
    
    /**
     * 更新JSON编辑器
     */
    function updateJsonEditor() {
        if (!state.currentModule || !state.configs[state.currentModule]) {
            jsonEditor.value = '{}';
            return;
        }
        
        const configs = state.configs[state.currentModule];
        const configObj = {};
        
        configs.forEach(config => {
            const value = state.unsavedChanges.has(config.name) 
                ? state.unsavedChanges.get(config.name) 
                : config.current;
            
            // 构建嵌套对象
            const path = config.path || config.name;
            const parts = path.split('.');
            let obj = configObj;
            
            for (let i = 0; i < parts.length - 1; i++) {
                if (!obj[parts[i]]) {
                    obj[parts[i]] = {};
                }
                obj = obj[parts[i]];
            }
            
            obj[parts[parts.length - 1]] = value;
        });
        
        jsonEditor.value = JSON.stringify(configObj, null, 2);
    }
    
    /**
     * 验证JSON
     */
    function validateJson() {
        try {
            JSON.parse(jsonEditor.value);
            addLog('JSON格式验证通过', 'success');
            showToast('JSON格式正确', 'success');
            return true;
        } catch (error) {
            addLog(`JSON格式错误: ${error.message}`, 'error');
            showToast(`JSON格式错误: ${error.message}`, 'error');
            return false;
        }
    }
    
    /**
     * 应用JSON
     */
    function applyJson() {
        if (!validateJson()) return;
        
        try {
            const configObj = JSON.parse(jsonEditor.value);
            const updates = [];
            
            // 展平嵌套对象
            function flatten(obj, prefix = '') {
                for (const key in obj) {
                    const fullKey = prefix ? `${prefix}.${key}` : key;
                    if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
                        flatten(obj[key], fullKey);
                    } else {
                        updates.push({
                            name: fullKey,
                            value: obj[key]
                        });
                    }
                }
            }
            
            flatten(configObj);
            
            // 批量更新
            fetch('/api/config/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ updates })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 清空未保存列表
                    state.unsavedChanges.clear();
                    updateUnsavedCount();
                    
                    // 更新配置数据
                    if (data.configs && state.currentModule) {
                        state.configs[state.currentModule] = data.configs[state.currentModule] || [];
                    }
                    
                    // 重新渲染
                    renderModuleConfigs(state.currentModule);
                    
                    addLog(`通过JSON应用了 ${updates.length} 项配置更改`, 'success');
                    showToast('JSON配置应用成功', 'success');
                } else {
                    addLog(`应用JSON失败: ${data.message}`, 'error');
                    showToast(`应用JSON失败: ${data.message}`, 'error');
                }
            })
            .catch(error => {
                addLog(`应用JSON时发生错误: ${error.message}`, 'error');
                showToast('网络错误，请检查连接', 'error');
            });
        } catch (error) {
            addLog(`解析JSON时发生错误: ${error.message}`, 'error');
            showToast('JSON解析错误', 'error');
        }
    }
    
    /**
     * 导出JSON
     */
    function exportJson() {
        fetch('/api/config/all')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const jsonStr = JSON.stringify(data.configs, null, 2);
                    document.getElementById('json-preview').textContent = jsonStr;
                    document.getElementById('json-modal').classList.add('show');
                } else {
                    showToast('导出失败: ' + data.message, 'error');
                }
            })
            .catch(error => {
                showToast('导出失败: ' + error.message, 'error');
            });
    }
    
    /**
     * 关闭JSON模态框
     */
    function closeJsonModal() {
        document.getElementById('json-modal').classList.remove('show');
    }
    
    /**
     * 复制JSON到剪贴板
     */
    function copyJsonToClipboard() {
        const jsonText = document.getElementById('json-preview').textContent;
        navigator.clipboard.writeText(jsonText)
            .then(() => {
                showToast('已复制到剪贴板', 'success');
            })
            .catch(() => {
                showToast('复制失败', 'error');
            });
    }
    
    /**
     * 下载JSON文件
     */
    function downloadJson() {
        const jsonText = document.getElementById('json-preview').textContent;
        const blob = new Blob([jsonText], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `autowater-config-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('文件下载开始', 'success');
    }
    
    /**
     * 清空日志
     */
    function clearLog() {
        const logContainer = document.getElementById('log-container');
        logContainer.innerHTML = '<div class="log-entry info"><div class="log-time">[系统启动]</div><div class="log-message">配置管理面板已就绪</div></div>';
    }
    
    /**
     * 添加日志
     */
    function addLog(message, type = 'info') {
        const logContainer = document.getElementById('log-container');
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `
            <div class="log-time">[${timestamp}]</div>
            <div class="log-message">${message}</div>
        `;
        
        logContainer.prepend(logEntry);
        
        // 限制日志条目数量
        const entries = logContainer.querySelectorAll('.log-entry');
        if (entries.length > 50) {
            entries[entries.length - 1].remove();
        }
    }
    
    /**
     * 显示Toast消息
     */
    function showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = 'toast';
        toast.classList.add(type);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
});