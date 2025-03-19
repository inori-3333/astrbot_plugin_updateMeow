import os
import re
from pathlib import Path
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import *
from astrbot.api.message_components import Plain, MessageChain

@register("updateMeow", "inori-3333", "将已安装插件的更新内容推送到指定的会话", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 设置接收更新消息的会话ID，可以根据需要修改
        self.target_conversation_id = "your_conversation_id_here"
        
        # 确保check.txt文件存在
        self.check_file_path = os.path.join(os.path.dirname(__file__), "check.txt")
        if not os.path.exists(self.check_file_path):
            with open(self.check_file_path, "w", encoding="utf-8") as f:
                f.write("# 插件版本记录\n")
        
        # 注册启动事件
        self.context.register_start_event(self.on_start)
    
    async def on_start(self):
        '''Bot启动时检查插件更新并推送'''
        await self.check_updates()
    
    async def check_updates(self):
        '''检查插件更新并推送到指定会话'''
        plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)))
        update_messages = []
        
        # 读取当前的版本记录
        check_data = {}
        if os.path.exists(self.check_file_path):
            with open(self.check_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                current_plugin = None
                for line in lines:
                    plugin_match = re.match(r"## (\S+)", line)
                    if plugin_match:
                        current_plugin = plugin_match.group(1)
                    version_match = re.match(r"version==(\d+\.\d+\.\d+)", line)
                    if current_plugin and version_match:
                        check_data[current_plugin] = version_match.group(1)
        
        # 遍历插件目录
        for plugin_dir in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, plugin_dir)
            if os.path.isdir(plugin_path):
                versions_file = os.path.join(plugin_path, "versions.txt")
                
                if os.path.exists(versions_file):
                    # 读取versions.txt
                    with open(versions_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # 查找最后一个版本号
                    version_matches = re.findall(r"version==(\d+\.\d+\.\d+)", content)
                    if version_matches:
                        latest_version = version_matches[-1]
                        
                        # 检查该插件是否有更新
                        if plugin_dir not in check_data or check_data[plugin_dir] != latest_version:
                            # 找到最后一个版本号下的更新内容
                            last_version_pos = content.rfind(f"version=={latest_version}")
                            update_content = ""
                            if last_version_pos != -1:
                                next_version_pos = content.find("version==", last_version_pos + 1)
                                if next_version_pos != -1:
                                    update_content = content[last_version_pos:next_version_pos].strip()
                                else:
                                    update_content = content[last_version_pos:].strip()
                            
                            update_messages.append(f"## {plugin_dir}\n版本更新: {check_data.get(plugin_dir, '无记录')} -> {latest_version}\n{update_content}")
                            
                            # 更新check.txt
                            self._update_check_file(plugin_dir, latest_version)
        
        # 如果有更新，发送消息
        if update_messages:
            message = "# 🎉 插件更新通知 🎉\n\n" + "\n\n".join(update_messages)
            await self.context.send_message(self.target_conversation_id, MessageChain([Plain(message)]))
    
    def _update_check_file(self, plugin_name, version):
        '''更新check.txt中的版本记录'''
        if os.path.exists(self.check_file_path):
            with open(self.check_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # 查找插件部分
            plugin_section_found = False
            new_lines = []
            i = 0
            while i < len(lines):
                if re.match(r"## " + re.escape(plugin_name) + r"(\s|$)", lines[i]):
                    plugin_section_found = True
                    new_lines.append(lines[i])
                    i += 1
                    # 更新或添加版本行
                    while i < len(lines) and not lines[i].startswith("## "):
                        if re.match(r"version==", lines[i]):
                            new_lines.append(f"version=={version}\n")
                            i += 1
                        else:
                            new_lines.append(lines[i])
                            i += 1
                else:
                    new_lines.append(lines[i])
                    i += 1
            
            # 如果没有找到插件部分，添加一个新的
            if not plugin_section_found:
                new_lines.append(f"\n## {plugin_name}\nversion=={version}\n")
            
            # 写回文件
            with open(self.check_file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        else:
            # 如果文件不存在，创建一个新的
            with open(self.check_file_path, "w", encoding="utf-8") as f:
                f.write(f"# 插件版本记录\n\n## {plugin_name}\nversion=={version}\n")
    
    @filter.command("checkupdates")
    async def check_updates_command(self, event: AstrMessageEvent):
        '''手动检查插件更新'''
        yield event.plain_result("正在检查插件更新...")
        await self.check_updates()
        yield event.plain_result("插件更新检查完成!")


# TODO：
# 1.在插件配置页面指定会话ID
# 2.为不同插件添加头部名称
# 3.修改读取的编码格式，以支持中文
# 4.设计versions.txt的内容格式