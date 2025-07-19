#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : memory_enhancer.py
@Time    : 2025年07月19日 15:30:00
@Author  : 宝总
@Version : 1.0
@Desc    : 记忆系统增强器 - 智能分析和上下文管理
"""

import json
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict
from pathlib import Path

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from hybrid_memory_fixed import HybridMemorySystem, MemoryEntry


class MemoryEnhancer(HybridMemorySystem):
    """
    记忆系统增强器
    
    在基础混合记忆系统上添加智能分析和上下文管理功能
    """
    
    def __init__(self, memory_dir: str = "./memory_storage"):
        super().__init__(memory_dir)
        
        self.conversation_session_id: str = ""
        self.session_memories: List[MemoryEntry] = []
        self.knowledge_graph: Dict[str, Dict[str, Any]] = {}
        
        self._init_enhancer()
    
    def _init_enhancer(self):
        """初始化增强器组件"""
        self._load_knowledge_graph()
        self.conversation_session_id = f"session_{int(time.time())}"
        print(f"🚀 记忆增强器启动，会话ID: {self.conversation_session_id}")
    
    def _load_knowledge_graph(self):
        """加载知识图谱"""
        kg_file = self.memory_dir / "knowledge_graph.json"
        if kg_file.exists():
            try:
                with open(kg_file, 'r', encoding='utf-8') as f:
                    self.knowledge_graph = json.load(f)
                print(f"📊 已加载 {len(self.knowledge_graph)} 个知识节点")
            except Exception as e:
                print(f"⚠️ 加载知识图谱失败: {e}")
                self.knowledge_graph = {}
        else:
            self.knowledge_graph = {}
    
    def _save_knowledge_graph(self):
        """保存知识图谱"""
        kg_file = self.memory_dir / "knowledge_graph.json"
        try:
            with open(kg_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_graph, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 保存知识图谱失败: {e}")
    
    def add_memory_with_analysis(
        self,
        content: str,
        memory_type: str = "working",
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_analyze: bool = True
    ) -> str:
        """添加记忆并进行智能分析"""
        
        # 自动分析内容
        if auto_analyze:
            analyzed_tags, analyzed_importance, analyzed_metadata = self._analyze_content(content)
            
            # 合并分析结果
            final_tags = list(set((tags or []) + analyzed_tags))
            final_importance = max(importance, analyzed_importance)
            final_metadata = {**(metadata or {}), **analyzed_metadata}
        else:
            final_tags = tags
            final_importance = importance
            final_metadata = metadata
        
        # 添加会话信息
        if final_metadata is None:
            final_metadata = {}
        final_metadata["session_id"] = self.conversation_session_id
        
        # 调用父类方法添加记忆
        entry_id = super().add_memory(
            content, memory_type, final_importance, final_tags, final_metadata
        )
          # 更新知识图谱
        if final_tags:
            self._update_knowledge_graph(content, final_tags)
        
        # 添加到会话记忆
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            timestamp=time.time(),
            memory_type=memory_type,
            importance=final_importance,
            tags=final_tags,
            metadata=final_metadata
        )
        self.session_memories.append(entry)
        
        return entry_id
    
    def _analyze_content(self, content: str) -> Tuple[List[str], float, Dict[str, Any]]:
        """分析内容，提取标签、评估重要性和元数据"""
        tags = []
        importance = 0.5
        metadata = {}
        
        content_lower = content.lower()
        
        # 技术标签识别
        tech_patterns = {
            "python": r"\bpython\b",
            "ai": r"\b(ai|artificial intelligence|人工智能|机器学习|深度学习)\b",
            "langchain": r"\blangchain\b",
            "agent": r"\bagent\b",
            "记忆": r"\b(记忆|memory|记住)\b",
            "项目": r"\b(项目|project|任务|task)\b",
            "开发": r"\b(开发|development|编程|coding)\b",
            "框架": r"\b(框架|framework|库|library)\b"
        }
        
        for tag, pattern in tech_patterns.items():
            if re.search(pattern, content_lower):
                tags.append(tag)
        
        # 重要性评估
        importance_indicators = {
            r"\b(重要|关键|核心|critical|important)\b": 0.3,
            r"\b(完成|成功|success|完毕)\b": 0.2,
            r"\b(错误|失败|问题|error|bug)\b": 0.2,
            r"\b(优化|改进|提升|optimize)\b": 0.1,
            r"\b(学习|研究|分析|study)\b": 0.1
        }
        
        for pattern, weight in importance_indicators.items():
            if re.search(pattern, content_lower):
                importance += weight
        
        importance = min(importance, 1.0)
        
        # 情感分析 (简单版本)
        positive_words = ["好", "棒", "成功", "完成", "优秀", "满意", "great", "good", "success"]
        negative_words = ["问题", "错误", "失败", "困难", "bug", "error", "fail", "difficult"]
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            metadata["sentiment"] = "positive"
        elif negative_count > positive_count:
            metadata["sentiment"] = "negative"
        else:
            metadata["sentiment"] = "neutral"
        
        # 内容类型识别
        if any(word in content_lower for word in ["完成", "实现", "做了", "创建"]):
            metadata["action_type"] = "achievement"
        elif any(word in content_lower for word in ["需要", "要", "计划", "打算"]):
            metadata["action_type"] = "plan"
        elif any(word in content_lower for word in ["学到", "发现", "了解", "知道"]):
            metadata["action_type"] = "learning"
        
        return tags, importance, metadata
    
    def _update_knowledge_graph(self, content: str, tags: List[str]):
        """更新知识图谱"""
        if not tags:
            return
        
        # 为每个标签创建或更新节点
        for tag in tags:
            if tag not in self.knowledge_graph:
                self.knowledge_graph[tag] = {
                    "count": 0,
                    "related_tags": {},
                    "first_seen": time.time(),
                    "last_seen": time.time(),
                    "importance": 0.0
                }
            
            # 更新节点信息
            node = self.knowledge_graph[tag]
            node["count"] += 1
            node["last_seen"] = time.time()
            node["importance"] = min(1.0, node["importance"] + 0.1)
            
            # 更新关联关系
            for other_tag in tags:
                if other_tag != tag:
                    if other_tag not in node["related_tags"]:
                        node["related_tags"][other_tag] = 0
                    node["related_tags"][other_tag] += 1
        
        # 定期保存知识图谱
        if len(self.session_memories) % 5 == 0:
            self._save_knowledge_graph()
    
    def get_smart_context(self, query: str, max_context_items: int = 8) -> Dict[str, Any]:
        """获取智能上下文信息"""
        context = super().get_context_for_agent(query)
        
        # 添加增强信息
        context.update({
            "session_id": self.conversation_session_id,
            "session_memories_count": len(self.session_memories),
            "knowledge_insights": self._get_knowledge_insights(query),
            "memory_patterns": self._analyze_memory_patterns(),
            "suggested_tags": self._suggest_tags_for_query(query)
        })
        
        return context
    
    def _get_knowledge_insights(self, query: str) -> Dict[str, Any]:
        """根据查询获取知识洞察"""
        query_lower = query.lower()
        relevant_nodes = {}
        
        for tag, node_info in self.knowledge_graph.items():
            if tag.lower() in query_lower:
                relevant_nodes[tag] = {
                    "frequency": node_info["count"],
                    "importance": node_info["importance"],
                    "related_concepts": list(node_info["related_tags"].keys())[:3]
                }
        
        return {
            "relevant_concepts": relevant_nodes,
            "total_concepts": len(self.knowledge_graph)
        }
    
    def _analyze_memory_patterns(self) -> Dict[str, Any]:
        """分析记忆模式"""
        if not self.session_memories:
            return {"pattern": "no_data"}
        
        # 分析记忆类型分布
        type_distribution = Counter([mem.memory_type for mem in self.session_memories])
        
        # 分析时间模式
        recent_hours = [
            datetime.fromtimestamp(mem.timestamp).hour 
            for mem in self.session_memories
            if time.time() - mem.timestamp < 24 * 3600
        ]
        active_hours = Counter(recent_hours).most_common(3)
        
        # 分析重要性分布
        importance_levels = ["低", "中", "高"]
        importance_dist = {
            "低": len([m for m in self.session_memories if m.importance < 0.4]),
            "中": len([m for m in self.session_memories if 0.4 <= m.importance < 0.7]),
            "高": len([m for m in self.session_memories if m.importance >= 0.7])
        }
        
        return {
            "memory_types": dict(type_distribution),
            "active_hours": [{"hour": h, "count": c} for h, c in active_hours],
            "importance_distribution": importance_dist,
            "session_length": len(self.session_memories)
        }
    
    def _suggest_tags_for_query(self, query: str) -> List[str]:
        """为查询建议相关标签"""
        query_lower = query.lower()
        suggestions = []
        
        # 基于知识图谱建议
        for tag, node_info in self.knowledge_graph.items():
            if tag.lower() in query_lower:
                # 添加相关标签
                related = sorted(
                    node_info["related_tags"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                suggestions.extend([tag for tag, _ in related])
        
        return list(set(suggestions))
    
    def generate_session_summary(self) -> str:
        """生成会话总结"""
        if not self.session_memories:
            return "本次会话暂无记忆记录。"
        
        total_memories = len(self.session_memories)
        high_importance = len([m for m in self.session_memories if m.importance >= 0.7])
        
        # 最常见的标签
        all_tags = []
        for mem in self.session_memories:
            if mem.tags:
                all_tags.extend(mem.tags)
        
        common_tags = Counter(all_tags).most_common(5)
        
        # 最新的几条重要记忆
        important_memories = sorted(
            [m for m in self.session_memories if m.importance >= 0.6],
            key=lambda x: x.timestamp,
            reverse=True
        )[:3]
        
        summary = f"""
# 会话总结 ({self.conversation_session_id})

## 基本统计
- 总记忆数: {total_memories}
- 重要记忆数: {high_importance}
- 会话时长: {self._format_duration(time.time() - self.session_memories[0].timestamp if self.session_memories else 0)}

## 主要话题
{', '.join([f"{tag}({count})" for tag, count in common_tags])}

## 重要记忆片段
"""
        
        for i, mem in enumerate(important_memories, 1):
            summary += f"{i}. {mem.content[:100]}...\n"
        
        return summary
    
    def _format_duration(self, seconds: float) -> str:
        """格式化时间长度"""
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            return f"{int(seconds//60)}分钟"
        else:
            return f"{int(seconds//3600)}小时{int((seconds%3600)//60)}分钟"
    
    def close(self):
        """关闭时保存数据"""
        self._save_knowledge_graph()
        
        # 保存会话总结
        if self.session_memories:
            summary_file = self.memory_dir / f"session_summary_{self.conversation_session_id}.md"
            try:
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write(self.generate_session_summary())
            except Exception as e:
                print(f"⚠️ 保存会话总结失败: {e}")
        
        super().close()


# 测试代码
if __name__ == "__main__":
    print("🎯 宝总的记忆增强器测试开始！")
    
    # 创建记忆增强器
    enhancer = MemoryEnhancer()
    
    # 添加测试记忆并分析
    test_memories = [
        "今天完成了Python项目的核心功能开发，感觉很棒！",
        "需要优化AI Agent的记忆系统性能，这是个重要任务",
        "学习了LangChain框架的使用方法，很有用",
        "发现了一个关键bug，需要紧急修复",
        "成功实现了混合记忆系统，宝总很满意"
    ]
    
    for i, content in enumerate(test_memories):
        memory_id = enhancer.add_memory_with_analysis(
            content,
            memory_type="episodic" if i % 2 == 0 else "task",
            auto_analyze=True
        )
        print(f"添加记忆: {memory_id}")
    
    # 测试智能上下文
    print("\n🧠 智能上下文测试:")
    context = enhancer.get_smart_context("Python开发项目")
    print(f"知识洞察: {context['knowledge_insights']}")
    print(f"记忆模式: {context['memory_patterns']}")
    print(f"建议标签: {context['suggested_tags']}")
    
    # 生成会话总结
    print("\n📋 会话总结:")
    print(enhancer.generate_session_summary())
    
    enhancer.close()
    print("\n✅ 记忆增强器测试完成！")
