#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : hybrid_memory_fixed.py
@Time    : 2025年07月19日 14:30:00
@Author  : 宝总
@Version : 1.0
@Desc    : 宝总专属混合记忆系统 - 修复版
"""

import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib
import sqlite3
import numpy as np
from collections import deque


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
    
    融合多种记忆机制，突破传统LLM的记忆限制
    """
    
    def __init__(self, memory_dir: str = "./memory_storage"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        self._init_storage_systems()
        self._init_memory_components()
        
        self.current_project_context: Dict[str, Any] = {}
        self.user_preferences = self._load_user_preferences()
    
    def _init_storage_systems(self):
        """初始化存储系统"""
        self.db_path = self.memory_dir / "memory.db"
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        """创建记忆数据表"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                memory_type TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_contexts (
                project_name TEXT PRIMARY KEY,
                tech_stack TEXT,
                created_at REAL,
                updated_at REAL,
                context_data TEXT
            )
        """)
        
        self.conn.commit()
    
    def _init_memory_components(self):
        """初始化记忆组件"""
        self.working_memory: deque = deque(maxlen=50)
        self.semantic_memory: Dict[str, Any] = {}
        self.episodic_memory: List[MemoryEntry] = []
        self.procedural_memory: Dict[str, MemoryEntry] = {}
        self.project_memory: Dict[str, List[MemoryEntry]] = {}
    
    def _load_user_preferences(self) -> Dict[str, Any]:
        """加载宝总的用户偏好"""
        prefs_file = self.memory_dir / "user_preferences.json"
        if prefs_file.exists():
            with open(prefs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        default_prefs = {
            "name": "宝总",
            "role": "全栈开发者、独立开发者",
            "primary_language": "Python",
            "coding_style": "简洁、可维护、符合Python最佳实践"
        }
        
        with open(prefs_file, 'w', encoding='utf-8') as f:
            json.dump(default_prefs, f, indent=2, ensure_ascii=False)
        
        return default_prefs
    
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
        """添加新记忆"""
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
            self.episodic_memory.append(entry)
        elif memory_type == "procedural":
            skill_name = (metadata or {}).get("skill_name", "unknown")
            self.procedural_memory[skill_name] = entry
        elif memory_type == "project":
            project_name = (metadata or {}).get("project_name", "default")
            if project_name not in self.project_memory:
                self.project_memory[project_name] = []
            self.project_memory[project_name].append(entry)
        
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
            json.dumps(entry.tags or [], ensure_ascii=False),
            json.dumps(entry.metadata or {}, ensure_ascii=False)
        ))
        self.conn.commit()
    
    def smart_recall(
        self, 
        query: str, 
        memory_types: Optional[List[str]] = None,
        max_results: int = 10,
        min_importance: float = 0.0
    ) -> List[MemoryEntry]:
        """智能记忆召回"""
        if memory_types is None:
            memory_types = ["working", "semantic", "episodic", "procedural", "project"]
        
        all_results = []
        
        if "working" in memory_types:
            all_results.extend(self._search_working_memory(query))
        
        if "episodic" in memory_types:
            all_results.extend(self._search_episodic_memory(query))
        
        if "procedural" in memory_types:
            all_results.extend(self._search_procedural_memory(query))
        
        if "project" in memory_types:
            all_results.extend(self._search_project_memory(query))
        
        scored_results = self._score_and_rank_results(query, all_results)
        
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
            content_lower = entry.content.lower()
            
            match_score = 0.0
            if query_lower in content_lower:
                match_score += 1.0
                if content_lower.startswith(query_lower):
                    match_score += 0.5
            
            # 标签匹配 - 修复None检查
            if entry.tags:
                for tag in entry.tags:
                    if query_lower in tag.lower():
                        match_score += 0.3
            
            # 时间衰减
            time_diff = time.time() - entry.timestamp
            time_factor = max(0.1, 1.0 - time_diff / (7 * 24 * 3600))
            
            final_score = (match_score * 0.6 + 
                          entry.importance * 0.3 + 
                          time_factor * 0.1)
            
            scored_results.append((entry, final_score))
        
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results
    
    def update_project_context(
        self, 
        project_name: str,
        tech_stack: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ):
        """更新项目上下文信息"""
        self.current_project_context = {
            "project_name": project_name,
            "tech_stack": tech_stack or "Python",
            "updated_at": time.time(),
            "context_data": context_data or {}
        }
        
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
    
    def get_context_for_agent(self, query: Optional[str] = None) -> Dict[str, Any]:
        """为Agent获取当前上下文信息"""
        context = {
            "user_info": self.user_preferences,
            "current_project": self.current_project_context,
            "recent_memories": [],
            "relevant_skills": [],
            "conversation_history": []
        }
        
        if query:
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
        
        recent_working = list(self.working_memory)[-10:]
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
        cursor.execute("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type")
        memory_stats = dict(cursor.fetchall())
        
        report = f"""
# 宝总的记忆系统状态报告

## 记忆统计
- 工作记忆: {len(self.working_memory)} 条
- 情节记忆: {memory_stats.get('episodic', 0)} 条  
- 程序记忆: {memory_stats.get('procedural', 0)} 条
- 项目记忆: {memory_stats.get('project', 0)} 条

## 当前项目上下文
- 项目名称: {self.current_project_context.get('project_name', '未设置')}
- 技术栈: {self.current_project_context.get('tech_stack', 'Python')}

## 用户偏好
- 称呼: {self.user_preferences.get('name', '宝总')}
- 角色: {self.user_preferences.get('role', '全栈开发者')}
"""
        return report
    
    def close(self):
        """关闭记忆系统"""
        if self.conn:
            self.conn.close()


# 测试代码
if __name__ == "__main__":
    print("🧠 宝总的混合记忆系统测试开始！")
    
    # 创建记忆系统实例
    memory = HybridMemorySystem()
    
    # 添加测试记忆
    memory.add_memory(
        "宝总喜欢使用Python进行全栈开发",
        memory_type="semantic",
        importance=0.9,
        tags=["用户偏好", "技术栈"]
    )
    
    memory.add_memory(
        "完成了AI-agent研究报告，使用第一性原理框架",
        memory_type="episodic",
        importance=0.8,
        tags=["项目完成", "研究"]
    )
    
    # 更新项目上下文
    memory.update_project_context(
        "BaozongSuperAgent",
        "Python + LangChain + 混合记忆系统"
    )
    
    # 测试记忆召回
    print("\n🔍 测试记忆召回:")
    results = memory.smart_recall("Python 开发", max_results=3)
    for result in results:
        print(f"- {result.content} (重要性: {result.importance})")
    
    # 生成报告
    print(memory.generate_memory_report())
    
    memory.close()
    print("\n✅ 测试完成！")
