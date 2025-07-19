#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : hybrid_memory.py
@Time    : 2025年07月19日 14:20:00
@Author  : 宝总
@Version : 1.0
@Desc    : 宝总专属混合记忆系统 - 超越传统LLM记忆限制
"""

import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import sqlite3
import numpy as np
from collections import deque
import threading


@dataclass
class MemoryEntry:
    """记忆条目基础结构"""
    
    id: str
    content: str
    timestamp: float
    memory_type: str
    importance: float = 0.5
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


class HybridMemorySystem:
    """
    宝总专属混合记忆系统
    
    融合多种记忆机制，突破传统LLM的记忆限制：
    1. 工作记忆 - 短期对话缓存
    2. 语义记忆 - 向量化知识存储  
    3. 情节记忆 - 时间序列事件记录
    4. 程序记忆 - 技能和方法存储
    5. 项目记忆 - 宝总项目特定上下文
    """
    
    def __init__(self, memory_dir: str = "./memory_storage"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        # 第一性原理：记忆的本质是信息的存储、关联和检索
        self._init_storage_systems()
        self._init_memory_components()
        
        # 宝总特色：项目上下文感知
        self.current_project_context = {}
        self.user_preferences = self._load_user_preferences()
        
    def _init_storage_systems(self):
        """初始化存储系统"""
        # SQLite用于结构化数据存储
        self.db_path = self.memory_dir / "memory.db"
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._create_tables()
        
        # 向量存储路径（后续可集成ChromaDB或Pinecone）
        self.vector_storage_path = self.memory_dir / "vectors"
        self.vector_storage_path.mkdir(exist_ok=True)
        
    def _create_tables(self):
        """创建记忆数据表"""
        cursor = self.conn.cursor()
        
        # 通用记忆表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                memory_type TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                tags TEXT,  -- JSON格式存储
                metadata TEXT,  -- JSON格式存储
                vector_id TEXT
            )
        """)
        
        # 项目上下文表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_contexts (
                project_name TEXT PRIMARY KEY,
                tech_stack TEXT,
                created_at REAL,
                updated_at REAL,
                context_data TEXT  -- JSON格式存储
            )
        """)
        
        # 技能记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                skill_id TEXT PRIMARY KEY,
                skill_name TEXT NOT NULL,
                skill_category TEXT,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 1.0,
                last_used REAL,
                skill_data TEXT  -- JSON格式存储
            )
        """)
        
        self.conn.commit()
    
    def _init_memory_components(self):
        """初始化记忆组件"""
        # 1. 工作记忆 - 双端队列实现的短期缓存
        self.working_memory = deque(maxlen=50)
        
        # 2. 语义记忆 - 简化的向量相似度检索
        self.semantic_memory = {}  # 后续可升级为专业向量数据库
        
        # 3. 情节记忆 - 按时间排序的事件序列
        self.episodic_memory = []
        
        # 4. 程序记忆 - 技能和方法的索引
        self.procedural_memory = {}
        
        # 5. 项目记忆 - 宝总的项目特定信息
        self.project_memory = {}
        
        # 加载已有记忆
        self._load_existing_memories()
    
    def _load_user_preferences(self) -> Dict[str, Any]:
        """加载宝总的用户偏好"""
        prefs_file = self.memory_dir / "user_preferences.json"
        if prefs_file.exists():
            with open(prefs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 默认偏好设置
        default_prefs = {
            "name": "宝总",
            "role": "全栈开发者、独立开发者",
            "primary_language": "Python",
            "coding_style": "简洁、可维护、符合Python最佳实践",
            "preferred_tools": ["VS Code", "Git", "Docker"],
            "work_pattern": "快速迭代、持续优化"
        }
        
        # 保存默认偏好
        with open(prefs_file, 'w', encoding='utf-8') as f:
            json.dump(default_prefs, f, indent=2, ensure_ascii=False)
        
        return default_prefs
    
    def _load_existing_memories(self):
        """从存储中加载已有记忆"""
        cursor = self.conn.cursor()
        
        # 加载最近的工作记忆
        cursor.execute("""
            SELECT content, timestamp, memory_type, importance 
            FROM memories 
            WHERE memory_type = 'working'
            ORDER BY timestamp DESC 
            LIMIT 20
        """)
        
        for content, timestamp, mem_type, importance in cursor.fetchall():
            entry = MemoryEntry(
                id=self._generate_id(content),
                content=content,
                timestamp=timestamp,
                memory_type=mem_type,
                importance=importance
            )
            self.working_memory.appendleft(entry)
    
    def _generate_id(self, content: str) -> str:
        """生成内容的唯一ID"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
      def add_memory(
        self, 
        content: str, 
        memory_type: str = "working",
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        添加新记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型 (working/semantic/episodic/procedural/project)
            importance: 重要性评分 (0.0-1.0)
            tags: 标签列表
            metadata: 元数据
        
        Returns:
            记忆ID
        """
        entry = MemoryEntry(
            id=self._generate_id(content + str(time.time())),
            content=content,
            timestamp=time.time(),
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # 添加到对应的记忆系统
        if memory_type == "working":
            self.working_memory.append(entry)
        elif memory_type == "episodic":
            self.episodic_memory.append(entry)        elif memory_type == "procedural":
            skill_name = (metadata or {}).get("skill_name", "unknown")
            self.procedural_memory[skill_name] = entry
        elif memory_type == "project":
            project_name = (metadata or {}).get("project_name", "default")
            if project_name not in self.project_memory:
                self.project_memory[project_name] = []
            self.project_memory[project_name].append(entry)
        
        # 持久化存储
        self._save_memory_to_db(entry)
        
        return entry.id
    
    def _save_memory_to_db(self, entry: MemoryEntry):
        """保存记忆到数据库"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO memories 
            (id, content, timestamp, memory_type, importance, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id,
            entry.content,
            entry.timestamp,
            entry.memory_type,
            entry.importance,
            json.dumps(entry.tags, ensure_ascii=False),
            json.dumps(entry.metadata, ensure_ascii=False)
        ))
        self.conn.commit()
    
    def smart_recall(
        self, 
        query: str, 
        memory_types: List[str] = None,
        max_results: int = 10,
        min_importance: float = 0.0
    ) -> List[MemoryEntry]:
        """
        智能记忆召回
        
        基于查询内容，从多个记忆系统中召回相关信息
        """
        if memory_types is None:
            memory_types = ["working", "semantic", "episodic", "procedural", "project"]
        
        all_results = []
        
        # 1. 从工作记忆召回
        if "working" in memory_types:
            working_results = self._search_working_memory(query)
            all_results.extend(working_results)
        
        # 2. 从情节记忆召回
        if "episodic" in memory_types:
            episodic_results = self._search_episodic_memory(query)
            all_results.extend(episodic_results)
        
        # 3. 从程序记忆召回
        if "procedural" in memory_types:
            procedural_results = self._search_procedural_memory(query)
            all_results.extend(procedural_results)
        
        # 4. 从项目记忆召回
        if "project" in memory_types:
            project_results = self._search_project_memory(query)
            all_results.extend(project_results)
        
        # 按重要性和相关性排序
        scored_results = self._score_and_rank_results(query, all_results)
        
        # 过滤和返回结果
        filtered_results = [
            entry for entry, score in scored_results 
            if entry.importance >= min_importance
        ]
        
        return filtered_results[:max_results]
    
    def _search_working_memory(self, query: str) -> List[MemoryEntry]:
        """搜索工作记忆"""
        results = []
        query_lower = query.lower()
        
        for entry in self.working_memory:
            if query_lower in entry.content.lower():
                results.append(entry)
        
        return results
    
    def _search_episodic_memory(self, query: str) -> List[MemoryEntry]:
        """搜索情节记忆"""
        results = []
        query_lower = query.lower()
        
        for entry in self.episodic_memory:
            if query_lower in entry.content.lower():
                results.append(entry)
        
        return results
    
    def _search_procedural_memory(self, query: str) -> List[MemoryEntry]:
        """搜索程序记忆（技能）"""
        results = []
        query_lower = query.lower()
        
        for skill_name, entry in self.procedural_memory.items():
            if (query_lower in skill_name.lower() or 
                query_lower in entry.content.lower()):
                results.append(entry)
        
        return results
    
    def _search_project_memory(self, query: str) -> List[MemoryEntry]:
        """搜索项目记忆"""
        results = []
        query_lower = query.lower()
        
        for project_name, entries in self.project_memory.items():
            if query_lower in project_name.lower():
                results.extend(entries)
            else:
                for entry in entries:
                    if query_lower in entry.content.lower():
                        results.append(entry)
        
        return results
    
    def _score_and_rank_results(
        self, 
        query: str, 
        results: List[MemoryEntry]
    ) -> List[Tuple[MemoryEntry, float]]:
        """为搜索结果打分并排序"""
        scored_results = []
        query_lower = query.lower()
        
        for entry in results:
            # 基础相关性评分（简单的文本匹配）
            content_lower = entry.content.lower()
            
            # 计算匹配度
            match_score = 0.0
            if query_lower in content_lower:
                # 完全匹配
                match_score += 1.0
                # 匹配位置加权（开头匹配权重更高）
                if content_lower.startswith(query_lower):
                    match_score += 0.5
            
            # 标签匹配
            for tag in entry.tags:
                if query_lower in tag.lower():
                    match_score += 0.3
            
            # 时间衰减（最近的记忆权重更高）
            time_diff = time.time() - entry.timestamp
            time_factor = max(0.1, 1.0 - time_diff / (7 * 24 * 3600))  # 一周内权重较高
            
            # 综合评分
            final_score = (match_score * 0.6 + 
                          entry.importance * 0.3 + 
                          time_factor * 0.1)
            
            scored_results.append((entry, final_score))
        
        # 按评分排序
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results
    
    def update_project_context(
        self, 
        project_name: str,
        tech_stack: str = None,
        context_data: Dict[str, Any] = None
    ):
        """更新项目上下文信息"""
        self.current_project_context = {
            "project_name": project_name,
            "tech_stack": tech_stack or "Python",
            "updated_at": time.time(),
            "context_data": context_data or {}
        }
        
        # 保存到数据库
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO project_contexts
            (project_name, tech_stack, created_at, updated_at, context_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            project_name,
            tech_stack,
            time.time(),
            time.time(),
            json.dumps(context_data or {}, ensure_ascii=False)
        ))
        self.conn.commit()
        
        # 添加到项目记忆
        context_summary = f"项目 {project_name} 更新: {tech_stack}"
        self.add_memory(
            content=context_summary,
            memory_type="project",
            importance=0.8,
            metadata={
                "project_name": project_name,
                "action": "context_update"
            }
        )
    
    def get_context_for_agent(self, query: str = None) -> Dict[str, Any]:
        """
        为Agent获取当前上下文信息
        
        这是Agent调用的主要接口，返回格式化的上下文
        """
        context = {
            "user_info": self.user_preferences,
            "current_project": self.current_project_context,
            "recent_memories": [],
            "relevant_skills": [],
            "conversation_history": []
        }
        
        if query:
            # 基于查询召回相关记忆
            relevant_memories = self.smart_recall(query, max_results=5)
            context["recent_memories"] = [
                {
                    "content": mem.content,
                    "type": mem.memory_type,
                    "importance": mem.importance,
                    "timestamp": mem.timestamp
                }
                for mem in relevant_memories
            ]
        
        # 获取最近的对话历史
        recent_working = list(self.working_memory)[-10:]  # 最近10条
        context["conversation_history"] = [
            {
                "content": mem.content,
                "timestamp": mem.timestamp
            }
            for mem in recent_working
        ]
        
        return context
    
    def generate_memory_report(self) -> str:
        """生成记忆系统状态报告"""
        cursor = self.conn.cursor()
        
        # 统计各类记忆数量
        cursor.execute("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type")
        memory_stats = dict(cursor.fetchall())
        
        report = f"""
# 宝总的记忆系统状态报告

## 记忆统计
- 工作记忆: {len(self.working_memory)} 条
- 情节记忆: {memory_stats.get('episodic', 0)} 条  
- 程序记忆: {memory_stats.get('procedural', 0)} 条
- 项目记忆: {memory_stats.get('project', 0)} 条
- 语义记忆: {memory_stats.get('semantic', 0)} 条

## 当前项目上下文
- 项目名称: {self.current_project_context.get('project_name', '未设置')}
- 技术栈: {self.current_project_context.get('tech_stack', 'Python')}

## 用户偏好
- 称呼: {self.user_preferences.get('name', '宝总')}
- 角色: {self.user_preferences.get('role', '全栈开发者')}
- 主要语言: {self.user_preferences.get('primary_language', 'Python')}

## 记忆健康度
- 数据库连接: {'正常' if self.conn else '异常'}
- 存储路径: {self.memory_dir}
- 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return report
    
    def cleanup_old_memories(self, days_old: int = 30):
        """清理旧记忆（保持系统性能）"""
        cutoff_time = time.time() - (days_old * 24 * 3600)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM memories 
            WHERE timestamp < ? AND importance < 0.7
        """, (cutoff_time,))
        
        deleted_count = cursor.rowcount
        self.conn.commit()
        
        return f"清理了 {deleted_count} 条低重要性的旧记忆"
    
    def close(self):
        """关闭记忆系统"""
        if self.conn:
            self.conn.close()


# 测试和演示代码
if __name__ == "__main__":
    # 创建记忆系统实例
    memory_system = HybridMemorySystem()
    
    print("🧠 宝总的混合记忆系统启动成功！")
    print("=" * 50)
    
    # 添加一些测试记忆
    memory_system.add_memory(
        "宝总喜欢使用Python进行全栈开发",
        memory_type="semantic",
        importance=0.9,
        tags=["用户偏好", "技术栈"]
    )
    
    memory_system.add_memory(
        "完成了AI-agent研究报告，使用第一性原理框架",
        memory_type="episodic",
        importance=0.8,
        tags=["项目完成", "研究"]
    )
    
    memory_system.add_memory(
        "LangChain agent架构分析方法",
        memory_type="procedural",
        importance=0.7,
        metadata={"skill_name": "agent_architecture_analysis"}
    )
    
    # 更新项目上下文
    memory_system.update_project_context(
        "AI_Agent_Research",
        "Python + LangChain + 第一性原理框架",
        {"stage": "architecture_design", "priority": "high"}
    )
    
    # 测试记忆召回
    print("\n🔍 测试记忆召回:")
    results = memory_system.smart_recall("Python 开发")
    for result in results:
        print(f"- {result.content} (重要性: {result.importance})")
    
    # 获取Agent上下文
    print("\n📋 Agent上下文:")
    context = memory_system.get_context_for_agent("Python项目")
    print(f"当前项目: {context['current_project']['project_name']}")
    print(f"相关记忆数量: {len(context['recent_memories'])}")
    
    # 生成报告
    print("\n📊 记忆系统报告:")
    report = memory_system.generate_memory_report()
    print(report)
    
    # 清理
    memory_system.close()
    print("\n✅ 测试完成！")
