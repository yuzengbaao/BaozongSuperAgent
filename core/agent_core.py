#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : agent_core.py
@Time    : 2025年07月19日 16:00:00
@Author  : 宝总
@Version : 1.0
@Desc    : 宝总专属SuperAgent核心引擎
"""

import json
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# 导入记忆系统
import sys
sys.path.append(str(Path(__file__).parent.parent))

from memory.memory_enhancer import MemoryEnhancer


class AgentState(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    LEARNING = "learning"
    ERROR = "error"


@dataclass
class Task:
    """任务数据结构"""
    id: str
    title: str
    description: str
    priority: int = 1  # 1-5，5最高
    status: str = "pending"
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentResponse:
    """Agent响应结构"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    next_actions: Optional[List[str]] = None


class BaozongSuperAgent:
    """
    宝总专属超级Agent
    
    集成混合记忆系统的智能Agent核心
    """
    
    def __init__(self, agent_name: str = "宝总的SuperAgent", workspace_dir: str = "./baozong_workspace"):
        self.agent_name = agent_name
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        
        # 初始化核心组件
        self.memory_system = MemoryEnhancer(str(self.workspace_dir / "memory"))
        self.state = AgentState.IDLE
        self.current_session_id = f"session_{int(time.time())}"
        
        # 初始化瞬间修复器
        try:
            sys.path.append(str(Path(__file__).parent.parent))
            from instant_agent_fix import InstantFix
            self.instant_fix = InstantFix()
            print(f"🚀 {agent_name} 已启用瞬间修复模式")
            print("📈 回答质量预期提升300%+")
        except ImportError as e:
            print(f"⚠️ 瞬间修复模块未找到: {e}")
            print("💡 请确保 instant_agent_fix.py 在正确位置")
            self.instant_fix = None
        
        # 任务管理
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.active_task: Optional[Task] = None
        
        # Agent配置
        self.config = self._load_config()
        self.tools: Dict[str, Callable] = {}
        
        # 性能监控
        self.performance_stats = {
            "tasks_completed": 0,
            "total_thinking_time": 0.0,
            "average_response_time": 0.0,
            "success_rate": 0.0,
            "start_time": time.time()
        }
        
        self._init_core_tools()
        self._log_startup()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载Agent配置"""
        config_file = self.workspace_dir / "agent_config.json"
        
        default_config = {
            "personality": {
                "name": "宝总的SuperAgent",
                "role": "全栈开发助手",
                "traits": ["专业", "高效", "学习能力强", "注重细节"],
                "communication_style": "简洁明了，技术导向"
            },
            "capabilities": {
                "max_thinking_steps": 10,
                "memory_context_size": 20,
                "task_priority_levels": 5,
                "auto_learning": True,
                "proactive_suggestions": True
            },
            "preferences": {
                "primary_language": "Python",
                "coding_standards": "PEP8",
                "project_structure": "模块化",
                "documentation_style": "详细注释"
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并配置
                    return {**default_config, **user_config}
            except Exception as e:
                print(f"⚠️ 加载配置失败: {e}，使用默认配置")
        
        # 保存默认配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        return default_config
    
    def _init_core_tools(self):
        """初始化核心工具集"""
        self.tools.update({
            "memory_search": self.memory_system.smart_recall,
            "add_memory": self.memory_system.add_memory_with_analysis,
            "get_context": self.memory_system.get_smart_context,
            "create_task": self.create_task,
            "complete_task": self.complete_task,
            "analyze_performance": self.get_performance_report
        })
    
    def _log_startup(self):
        """记录启动日志"""
        startup_info = f"Agent '{self.agent_name}' 启动成功"
        self.memory_system.add_memory_with_analysis(
            startup_info,
            memory_type="system",
            importance=0.7,
            tags=["启动", "系统"],
            metadata={
                "action": "startup",
                "session_id": self.current_session_id,
                "agent_version": "1.0"
            }
        )
        print(f"🤖 {startup_info}")
    
    def think(self, query: str, max_steps: Optional[int] = None) -> Dict[str, Any]:
        """思考过程 - Agent的核心推理能力"""
        if max_steps is None:
            max_steps = self.config["capabilities"]["max_thinking_steps"]
        
        self.state = AgentState.THINKING
        thinking_start = time.time()
        
        thinking_log = {
            "query": query,
            "steps": [],
            "context": {},
            "conclusion": "",
            "confidence": 0.0
        }
        
        # 步骤1: 获取相关上下文
        thinking_log["steps"].append("🔍 检索相关记忆和上下文")
        context = self.memory_system.get_smart_context(query)
        thinking_log["context"] = {
            "relevant_memories": len(context.get("recent_memories", [])),
            "session_memories": context.get("session_memories_count", 0),
            "knowledge_concepts": len(context.get("knowledge_insights", {}).get("relevant_concepts", {}))
        }
        
        # 步骤2: 分析查询类型和意图
        thinking_log["steps"].append("🎯 分析查询意图和类型")
        query_analysis = self._analyze_query(query)
        thinking_log["query_type"] = query_analysis["type"]
        thinking_log["intent"] = query_analysis["intent"]
        
        # 步骤3: 制定响应策略
        thinking_log["steps"].append("📋 制定响应策略")
        strategy = self._plan_response_strategy(query, query_analysis, context)
        thinking_log["strategy"] = strategy
        
        # 步骤4: 生成响应
        thinking_log["steps"].append("💡 生成响应")
        response = self._generate_response(query, strategy, context)
        thinking_log["conclusion"] = response["message"]
        thinking_log["confidence"] = response.get("confidence", 0.8)
        
        # 记录思考过程
        thinking_time = time.time() - thinking_start
        self.performance_stats["total_thinking_time"] += thinking_time
        
        self.memory_system.add_memory_with_analysis(
            f"思考查询: {query[:50]}... (耗时: {thinking_time:.2f}秒)",
            memory_type="procedural",
            importance=0.6,
            tags=["思考", "推理"],
            metadata={
                "thinking_time": thinking_time,
                "steps_count": len(thinking_log["steps"]),
                "confidence": thinking_log["confidence"]
            }
        )
        
        self.state = AgentState.IDLE
        return thinking_log
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """分析查询类型和意图"""
        query_lower = query.lower()
        
        # 查询类型分类
        query_type = "general"
        if any(word in query_lower for word in ["如何", "怎么", "方法", "how", "way"]):
            query_type = "how_to"
        elif any(word in query_lower for word in ["什么", "是什么", "what", "define"]):
            query_type = "definition"
        elif any(word in query_lower for word in ["为什么", "原因", "why", "reason"]):
            query_type = "explanation"
        elif any(word in query_lower for word in ["帮我", "请", "能否", "可以", "help", "please"]):
            query_type = "request"
        elif any(word in query_lower for word in ["创建", "生成", "制作", "create", "generate"]):
            query_type = "creation"
        
        # 意图识别
        intent = "unknown"
        if any(word in query_lower for word in ["代码", "编程", "开发", "code", "program"]):
            intent = "coding"
        elif any(word in query_lower for word in ["项目", "任务", "工作", "project", "task"]):
            intent = "project_management"
        elif any(word in query_lower for word in ["学习", "了解", "研究", "learn", "study"]):
            intent = "learning"
        elif any(word in query_lower for word in ["优化", "改进", "提升", "optimize", "improve"]):
            intent = "optimization"
        
        return {
            "type": query_type,
            "intent": intent,
            "complexity": len(query.split()),  # 简单的复杂度评估
            "technical_terms": self._extract_technical_terms(query)
        }
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """提取技术术语"""
        tech_terms = []
        tech_keywords = [
            "python", "javascript", "react", "vue", "django", "flask", "fastapi",
            "ai", "machine learning", "deep learning", "neural network",
            "langchain", "openai", "gpt", "llm", "agent", "chatbot",
            "database", "sql", "mongodb", "redis", "docker", "kubernetes",
            "api", "rest", "graphql", "websocket", "http", "json",
            "github", "git", "cicd", "devops", "aws", "azure", "gcp"
        ]
        
        text_lower = text.lower()
        for term in tech_keywords:
            if term in text_lower:
                tech_terms.append(term)
        
        return tech_terms
    
    def _plan_response_strategy(self, query: str, analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """制定响应策略"""
        strategy = {
            "approach": "direct_response",
            "use_memory": True,
            "create_task": False,
            "suggest_actions": True,
            "learning_opportunity": False
        }
          # 根据查询类型调整策略
        if analysis["type"] == "request":
            strategy["approach"] = "task_oriented"
            strategy["create_task"] = True
        elif analysis["type"] == "how_to" or analysis["intent"] == "learning":
            strategy["approach"] = "educational"
            strategy["learning_opportunity"] = True
        elif analysis["intent"] == "coding":
            strategy["approach"] = "technical_solution"
            strategy["suggest_actions"] = True
        
        # 根据上下文调整策略
        if context.get("session_memories_count", 0) > 10:
            strategy["use_session_context"] = True
        
        return strategy
    
    def _generate_response(self, query: str, strategy: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """使用瞬间修复器生成高质量响应"""
        
        # 如果瞬间修复器可用，使用增强响应
        if hasattr(self, 'instant_fix') and self.instant_fix is not None:
            try:
                enhanced_response = self.instant_fix.generate_smart_response(query, context)
                
                # 转换为原有格式
                return {
                    "message": enhanced_response["message"],
                    "confidence": enhanced_response["confidence"],
                    "suggestions": enhanced_response["suggestions"],
                    "next_actions": enhanced_response["next_actions"]
                }
                
            except Exception as e:
                print(f"⚠️ 瞬间修复器调用失败，使用备用方案: {e}")
        
        # 降级到原有逻辑（备用方案）
        response = {
            "message": "",
            "confidence": 0.8,
            "suggestions": [],
            "next_actions": []
        }
        
        # 特殊查询处理
        query_lower = query.lower()
        
        # 能力介绍查询
        if any(word in query_lower for word in ["能力", "介绍", "你是", "你好", "功能", "what can you"]):
            response["message"] = self._get_capability_introduction()
            response["suggestions"] = [
                "尝试: 'task create \"学习新技术\" \"研究FastAPI框架\" 3'",
                "尝试: 'memory search Python'",
                "尝试: '帮我分析代码架构设计'"
            ]
            response["next_actions"] = ["体验任务管理功能", "测试记忆搜索", "进行技术讨论"]
            response["confidence"] = 0.95
            return response
        
        # 上下文建议查询
        if "上下文" in query_lower or "建议" in query_lower:
            response["message"] = self._get_context_based_suggestions(context)
            response["suggestions"] = self._generate_smart_suggestions(context)
            response["next_actions"] = ["查看记忆模式", "分析知识图谱", "创建相关任务"]
            response["confidence"] = 0.9
            return response
        
        # 基于策略生成响应
        if strategy["approach"] == "task_oriented":
            response["message"] = f"我理解您的请求：{query}。让我为您创建相应的任务。"
            response["next_actions"].append("创建任务")
            response["suggestions"].append("将复杂请求分解为具体步骤")
            
        elif strategy["approach"] == "educational":
            response["message"] = f"关于您的问题：{query}，我将从以下几个方面来解答..."
            response["next_actions"].append("提供详细解释")
            response["suggestions"].append("推荐相关学习资源")
            
        elif strategy["approach"] == "technical_solution":
            response["message"] = f"针对技术问题：{query}，我建议采用以下方案..."
            response["next_actions"].append("提供代码示例")
            response["suggestions"].append("考虑最佳实践")
            
        else:
            response["message"] = f"我已理解您的问题：{query}。让我为您提供相关信息。"
        
        # 添加基于记忆的上下文
        if strategy.get("use_memory") and context.get("recent_memories"):
            response["message"] += f"\\n\\n基于您之前的{len(context['recent_memories'])}条相关记忆，"
        
        return response
    
    def create_task(self, title: str, description: str = "", priority: int = 1) -> str:
        """创建新任务"""
        task = Task(
            id=f"task_{int(time.time())}_{len(self.task_queue)}",
            title=title,
            description=description,
            priority=priority
        )
        
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)  # 按优先级排序
        
        # 记录任务创建
        self.memory_system.add_memory_with_analysis(
            f"创建任务: {title}",
            memory_type="task",
            importance=0.7,
            tags=["任务", "创建"],
            metadata={
                "task_id": task.id,                "priority": priority,
                "action": "task_created"
            }
        )
        
        return task.id
    
    def complete_task(self, task_id: str, result: str = "") -> bool:
        """完成任务"""
        task = None
        for i, t in enumerate(self.task_queue):
            if t.id == task_id:
                task = self.task_queue.pop(i)
                break
        
        if not task:
            return False
        
        task.status = "completed"
        task.updated_at = time.time()
        if task.metadata is None:
            task.metadata = {}
        task.metadata["completion_result"] = result
        
        self.completed_tasks.append(task)
        self.performance_stats["tasks_completed"] += 1
        
        # 记录任务完成
        completion_time = (task.updated_at or time.time()) - (task.created_at or time.time())
        self.memory_system.add_memory_with_analysis(
            f"完成任务: {task.title} - {result}",
            memory_type="achievement",
            importance=0.8,
            tags=["任务", "完成"],
            metadata={
                "task_id": task.id,
                "completion_time": completion_time,
                "action": "task_completed"
            }
        )
        
        return True
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        uptime = time.time() - self.performance_stats["start_time"]
        total_tasks = len(self.completed_tasks) + len(self.task_queue)
        
        return {
            "agent_name": self.agent_name,
            "session_id": self.current_session_id,
            "uptime_hours": uptime / 3600,
            "tasks": {
                "completed": len(self.completed_tasks),
                "pending": len(self.task_queue),
                "total": total_tasks
            },
            "performance": {
                "success_rate": self.performance_stats["tasks_completed"] / max(total_tasks, 1),
                "avg_thinking_time": self.performance_stats["total_thinking_time"] / max(1, self.performance_stats["tasks_completed"]),
                "productivity_score": self.performance_stats["tasks_completed"] / (uptime / 3600)
            },
            "memory_stats": {
                "total_memories": "从记忆系统获取",
                "session_memories": len(self.memory_system.session_memories),
                "knowledge_concepts": len(self.memory_system.knowledge_graph)
            }
        }
    
    def _get_capability_introduction(self) -> str:
        """获取能力介绍"""
        return f"""🤖 您好，我是{self.agent_name}！

🧠 **核心能力**:
• 混合记忆系统 - 具备工作记忆、语义记忆、情节记忆、程序记忆、项目记忆五层架构
• 智能对话交互 - 基于上下文感知的自然语言理解和响应
• 任务管理专家 - 创建、跟踪、优化任务执行流程
• 知识图谱构建 - 自动学习和关联您的技术知识与项目经验

🎯 **专业定位**:
• 专为Python全栈开发者定制
• 深度理解开发流程和技术栈
• 遵循第一性原理思维框架
• 持续学习和个性化适应

⚡ **即刻体验**:
• 与我自由对话，我会记住我们的交流内容
• 创建和管理您的开发任务
• 搜索和管理技术知识记忆
• 查看我的思考过程和分析结果

我的记忆系统已存储{len(self.memory_system.session_memories)}条会话记忆，知识图谱包含{len(self.memory_system.knowledge_graph)}个概念节点。

准备好开始我们的技术协作之旅吗？ 🚀"""
    
    def _get_context_based_suggestions(self, context: Dict[str, Any]) -> str:
        """基于上下文生成建议"""
        suggestions_text = "📊 **基于当前上下文的智能建议**:\n\n"
        
        # 基于记忆模式的建议
        memory_patterns = context.get("memory_patterns", {})
        if memory_patterns and memory_patterns != {"pattern": "no_data"}:
            memory_types = memory_patterns.get("memory_types", {})
            if memory_types:
                dominant_type = max(memory_types.items(), key=lambda x: x[1])
                suggestions_text += f"🎯 **记忆模式分析**: 您当前主要关注{dominant_type[0]}类记忆({dominant_type[1]}条)\n"
                
                if dominant_type[0] == "task":
                    suggestions_text += "   建议: 考虑将大任务分解为小任务，提升执行效率\n"
                elif dominant_type[0] == "episodic":
                    suggestions_text += "   建议: 可以总结这些经历，提炼出可复用的经验\n"
                elif dominant_type[0] == "procedural":
                    suggestions_text += "   建议: 考虑将这些技能整理成知识库\n"
        
        # 基于知识洞察的建议
        knowledge_insights = context.get("knowledge_insights", {})
        relevant_concepts = knowledge_insights.get("relevant_concepts", {})
        if relevant_concepts:
            suggestions_text += f"\n🧠 **知识图谱洞察**: 发现{len(relevant_concepts)}个相关概念\n"
            for concept, info in list(relevant_concepts.items())[:3]:
                suggestions_text += f"   • {concept}: 频次{info['frequency']}, 重要性{info['importance']:.2f}\n"
                if info['related_concepts']:
                    suggestions_text += f"     相关概念: {', '.join(info['related_concepts'])}\n"
        
        # 基于会话状态的建议
        session_count = context.get("session_memories_count", 0)
        if session_count > 10:
            suggestions_text += f"\n📈 **会话深度**: 已进行{session_count}轮交互，建议适时总结要点\n"
        elif session_count < 3:
            suggestions_text += f"\n🌟 **探索建议**: 可以尝试不同类型的交互，让我更好地了解您的需求\n"
        
        return suggestions_text
    
    def _generate_smart_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """生成智能建议列表"""
        suggestions = []
        
        # 基于记忆模式生成建议
        memory_patterns = context.get("memory_patterns", {})
        if memory_patterns and memory_patterns != {"pattern": "no_data"}:
            importance_dist = memory_patterns.get("importance_distribution", {})
            
            if importance_dist.get("高", 0) > importance_dist.get("中", 0):
                suggestions.append("继续关注高价值内容，保持学习深度")
            elif importance_dist.get("低", 0) > importance_dist.get("高", 0):
                suggestions.append("建议提升内容质量，聚焦核心技术问题")
        
        # 基于知识图谱生成建议
        knowledge_insights = context.get("knowledge_insights", {})
        total_concepts = knowledge_insights.get("total_concepts", 0)
        
        if total_concepts < 5:
            suggestions.append("探索更多技术领域，扩展知识图谱")
        elif total_concepts > 20:
            suggestions.append("知识图谱丰富，可以开始深度关联分析")
        
        # 基于建议标签生成建议
        suggested_tags = context.get("suggested_tags", [])
        if suggested_tags:
            suggestions.append(f"探索相关概念: {', '.join(suggested_tags[:3])}")
        
        # 默认建议
        if not suggestions:
            suggestions = [
                "尝试创建一个技术学习任务",
                "搜索相关的历史记忆",
                "查看系统性能和记忆统计"
            ]
        
        return suggestions
    
    async def process_query(self, query: str) -> AgentResponse:
        """处理查询的主要入口点"""
        print(f"🤖 [{self.agent_name}] 收到查询: {query}")
        
        try:
            # 思考过程
            thinking_result = self.think(query)
            
            # 根据思考结果执行操作
            success = True
            message = thinking_result["conclusion"]
            
            # 如果需要创建任务
            if "创建任务" in thinking_result.get("strategy", {}).get("next_actions", []):
                task_id = self.create_task(f"处理查询: {query[:30]}...", query)
                message += f"\\n已创建任务 {task_id}"
            
            # 构建响应
            response = AgentResponse(
                success=success,
                message=message,
                data={
                    "thinking_process": thinking_result["steps"],
                    "confidence": thinking_result["confidence"],
                    "session_id": self.current_session_id
                },
                suggestions=["基于上下文的建议1", "基于记忆的建议2"],
                next_actions=thinking_result.get("strategy", {}).get("next_actions", [])
            )
            
            # 记录查询处理
            self.memory_system.add_memory_with_analysis(
                f"处理查询: {query} -> {message[:100]}...",
                memory_type="interaction",
                importance=0.7,
                tags=["查询", "响应"],
                metadata={
                    "query": query,
                    "confidence": thinking_result["confidence"],
                    "thinking_steps": len(thinking_result["steps"])
                }
            )
            
            return response
            
        except Exception as e:
            self.state = AgentState.ERROR
            error_msg = f"处理查询时出错: {str(e)}"
            print(f"❌ {error_msg}")
            
            # 记录错误
            self.memory_system.add_memory_with_analysis(
                error_msg,
                memory_type="error",
                importance=0.9,
                tags=["错误", "异常"],
                metadata={"error": str(e), "query": query}
            )
            
            return AgentResponse(
                success=False,
                message=error_msg,
                suggestions=["检查输入格式", "重新尝试"]
            )
    
    def shutdown(self):
        """优雅关闭Agent"""
        print(f"🔄 {self.agent_name} 正在关闭...")
        
        # 保存性能统计
        performance_file = self.workspace_dir / "performance_history.json"
        try:
            history = []
            if performance_file.exists():
                with open(performance_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            history.append({
                "session_id": self.current_session_id,
                "timestamp": time.time(),
                "performance": self.get_performance_report()
            })
            
            with open(performance_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 保存性能统计失败: {e}")
        
        # 关闭记忆系统
        self.memory_system.close()
        
        print(f"✅ {self.agent_name} 已安全关闭")


# 测试代码
async def test_baozong_agent():
    """测试宝总的SuperAgent"""
    print("🚀 宝总的SuperAgent测试开始！")
    
    # 创建Agent实例
    agent = BaozongSuperAgent("宝总的测试Agent")
    
    # 测试查询
    test_queries = [
        "帮我分析一下Python项目的最佳实践",
        "如何优化AI Agent的性能",
        "创建一个代码审查的任务",
        "什么是混合记忆系统",
        "我需要学习LangChain框架"
    ]
    
    print(f"\\n📝 处理 {len(test_queries)} 个测试查询...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\\n--- 查询 {i}/{len(test_queries)} ---")
        response = await agent.process_query(query)
        
        print(f"成功: {response.success}")
        print(f"响应: {response.message}")
        if response.suggestions:
            print(f"建议: {', '.join(response.suggestions)}")
        
        # 短暂延迟
        await asyncio.sleep(1)
    
    # 生成报告
    print("\\n📊 性能报告:")
    report = agent.get_performance_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # 关闭Agent
    agent.shutdown()
    print("\\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_baozong_agent())
