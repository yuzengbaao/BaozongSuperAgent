#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : vector_memory.py
@Time    : 2025年07月19日 15:00:00
@Author  : 宝总
@Version : 1.0
@Desc    : 向量化记忆系统 - 语义搜索增强
"""

import json
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import sqlite3
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_VECTOR_DEPS = True
except ImportError:
    SentenceTransformer = None
    faiss = None
    HAS_VECTOR_DEPS = False
import pickle

from .hybrid_memory_fixed import MemoryEntry, HybridMemorySystem


class VectorMemorySystem(HybridMemorySystem):
    """
    向量化增强的混合记忆系统
    
    在原有系统基础上，增加语义向量搜索能力
    """
    
    def __init__(self, memory_dir: str = "./memory_storage", model_name: str = "all-MiniLM-L6-v2"):
        super().__init__(memory_dir)
        
        self.model_name = model_name
        self.embedding_model: Optional[Any] = None
        self.vector_index: Optional[Any] = None
        self.id_to_index_map: Dict[str, int] = {}
        self.index_to_id_map: Dict[int, str] = {}
        self.has_vector_support = HAS_VECTOR_DEPS
        
        if self.has_vector_support:
            self._init_vector_components()
        else:
            print("⚠️ 向量搜索依赖未安装，使用传统搜索")
            print("💡 要启用语义搜索，请安装: pip install sentence-transformers faiss-cpu")
    
    def _init_vector_components(self):
        """初始化向量组件"""
        if not self.has_vector_support:
            return
            
        try:
            print("🔥 正在加载语义向量模型...")
            self.embedding_model = SentenceTransformer(self.model_name)
            
            # 初始化FAISS索引
            embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            self.vector_index = faiss.IndexFlatIP(embedding_dim)  # 使用内积作为相似度
            
            # 加载已有的向量索引
            self._load_existing_vectors()
            
            print(f"✅ 向量系统初始化完成，向量维度: {embedding_dim}")
            
        except Exception as e:
            print(f"⚠️ 向量系统初始化失败: {e}")
            print("💡 将使用基础搜索功能")
            self.embedding_model = None
            self.vector_index = None
    
    def _load_existing_vectors(self):
        """加载已有的向量索引"""
        vector_file = self.memory_dir / "vectors.index"
        mapping_file = self.memory_dir / "vector_mappings.pkl"
        
        if vector_file.exists() and mapping_file.exists():
            try:
                self.vector_index = faiss.read_index(str(vector_file))
                with open(mapping_file, 'rb') as f:
                    mappings = pickle.load(f)
                    self.id_to_index_map = mappings['id_to_index']
                    self.index_to_id_map = mappings['index_to_id']
                
                print(f"📚 已加载 {len(self.id_to_index_map)} 个向量索引")
            except Exception as e:
                print(f"⚠️ 加载向量索引失败: {e}")
    
    def _save_vector_index(self):
        """保存向量索引"""
        if self.embedding_model is None:
            return
            
        try:
            vector_file = self.memory_dir / "vectors.index"
            mapping_file = self.memory_dir / "vector_mappings.pkl"
            
            faiss.write_index(self.vector_index, str(vector_file))
            
            mappings = {
                'id_to_index': self.id_to_index_map,
                'index_to_id': self.index_to_id_map
            }
            with open(mapping_file, 'wb') as f:
                pickle.dump(mappings, f)
                
        except Exception as e:
            print(f"⚠️ 保存向量索引失败: {e}")
    
    def add_memory(
        self, 
        content: str, 
        memory_type: str = "working",
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """添加记忆并创建向量索引"""
        entry_id = super().add_memory(content, memory_type, importance, tags, metadata)
        
        # 为新记忆创建向量
        if self.embedding_model is not None:
            self._add_to_vector_index(entry_id, content)
        
        return entry_id
    
    def _add_to_vector_index(self, entry_id: str, content: str):
        """添加内容到向量索引"""
        try:
            embedding = self.embedding_model.encode([content])
            
            # 添加到FAISS索引
            current_index = self.vector_index.ntotal
            self.vector_index.add(embedding.astype(np.float32))
            
            # 更新映射
            self.id_to_index_map[entry_id] = current_index
            self.index_to_id_map[current_index] = entry_id
            
            # 定期保存索引
            if len(self.id_to_index_map) % 10 == 0:
                self._save_vector_index()
                
        except Exception as e:
            print(f"⚠️ 添加向量索引失败: {e}")
    
    def semantic_search(
        self, 
        query: str, 
        max_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[MemoryEntry, float]]:
        """语义搜索记忆"""
        if self.embedding_model is None:
            print("⚠️ 向量模型未加载，使用传统搜索")
            results = self.smart_recall(query, max_results=max_results)
            return [(entry, 1.0) for entry in results]
        
        try:
            # 编码查询
            query_embedding = self.embedding_model.encode([query]).astype(np.float32)
            
            # 搜索最相似的向量
            scores, indices = self.vector_index.search(query_embedding, max_results * 2)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # FAISS返回-1表示无效索引
                    continue
                    
                similarity = float(score)
                if similarity < similarity_threshold:
                    continue
                
                entry_id = self.index_to_id_map.get(idx)
                if entry_id:
                    entry = self._get_memory_by_id(entry_id)
                    if entry:
                        results.append((entry, similarity))
            
            # 按相似度排序
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:max_results]
            
        except Exception as e:
            print(f"⚠️ 语义搜索失败: {e}")
            return []
    
    def _get_memory_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        """根据ID获取记忆条目"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, content, timestamp, memory_type, importance, tags, metadata
            FROM memories WHERE id = ?
        """, (entry_id,))
        
        result = cursor.fetchone()
        if result:
            return MemoryEntry(
                id=result[0],
                content=result[1],
                timestamp=result[2],
                memory_type=result[3],
                importance=result[4],
                tags=json.loads(result[5]) if result[5] else [],
                metadata=json.loads(result[6]) if result[6] else {}
            )
        return None
    
    def hybrid_search(
        self, 
        query: str, 
        max_results: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Tuple[MemoryEntry, float]]:
        """混合搜索：结合语义搜索和关键词搜索"""
        
        # 语义搜索结果
        semantic_results = self.semantic_search(query, max_results * 2)
        semantic_dict = {entry.id: (entry, score) for entry, score in semantic_results}
        
        # 关键词搜索结果
        keyword_results = self.smart_recall(query, max_results=max_results * 2)
        keyword_dict = {entry.id: entry for entry in keyword_results}
        
        # 合并结果
        combined_results = {}
        all_ids = set(semantic_dict.keys()) | set(keyword_dict.keys())
        
        for entry_id in all_ids:
            semantic_score = semantic_dict.get(entry_id, (None, 0.0))[1]
            keyword_score = 1.0 if entry_id in keyword_dict else 0.0
            
            # 计算综合得分
            final_score = (semantic_score * semantic_weight + 
                          keyword_score * keyword_weight)
            
            entry = (semantic_dict.get(entry_id, (None, 0))[0] or 
                    keyword_dict.get(entry_id))
            
            if entry:
                combined_results[entry_id] = (entry, final_score)
        
        # 按得分排序并返回
        sorted_results = sorted(
            combined_results.values(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return sorted_results[:max_results]
    
    def analyze_memory_clusters(self) -> Dict[str, Any]:
        """分析记忆聚类，发现模式"""
        if self.embedding_model is None or self.vector_index.ntotal == 0:
            return {"error": "向量索引为空或未初始化"}
        
        try:
            # 获取所有向量
            all_vectors = self.vector_index.reconstruct_n(0, self.vector_index.ntotal)
            
            if len(all_vectors) < 2:
                return {"clusters": 0, "message": "记忆条目太少，无法聚类"}
            
            # 简单的k-means聚类
            from sklearn.cluster import KMeans
            import warnings
            warnings.filterwarnings("ignore")
            
            n_clusters = min(5, len(all_vectors) // 3)  # 动态确定聚类数量
            if n_clusters < 2:
                n_clusters = 2
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(all_vectors)
            
            # 分析每个聚类
            clusters = {}
            for i, label in enumerate(cluster_labels):
                entry_id = self.index_to_id_map.get(i)
                if entry_id:
                    entry = self._get_memory_by_id(entry_id)
                    if entry:
                        if label not in clusters:
                            clusters[label] = []
                        clusters[label].append({
                            "content": entry.content[:100] + "...",
                            "type": entry.memory_type,
                            "importance": entry.importance
                        })
            
            return {
                "clusters": len(clusters),
                "cluster_info": clusters,
                "total_memories": len(all_vectors)
            }
            
        except Exception as e:
            return {"error": f"聚类分析失败: {e}"}
    
    def close(self):
        """关闭系统时保存向量索引"""
        self._save_vector_index()
        super().close()


# 测试代码
if __name__ == "__main__":
    print("🚀 宝总的向量化记忆系统测试开始！")
    
    # 创建向量记忆系统
    vector_memory = VectorMemorySystem()
    
    # 添加测试数据
    test_memories = [
        ("Python是宝总最喜欢的编程语言", "semantic", 0.9, ["编程", "偏好"]),
        ("LangChain是构建AI应用的强大框架", "knowledge", 0.8, ["AI", "框架"]),
        ("今天完成了混合记忆系统的设计", "episodic", 0.8, ["项目", "完成"]),
        ("需要优化向量搜索的性能", "task", 0.6, ["优化", "性能"]),
        ("Agent需要具备长期记忆能力", "insight", 0.9, ["AI", "记忆"])
    ]
    
    for content, mem_type, importance, tags in test_memories:
        vector_memory.add_memory(content, mem_type, importance, tags)
    
    # 测试语义搜索
    print("\n🔍 语义搜索测试:")
    semantic_results = vector_memory.semantic_search("人工智能开发", max_results=3)
    for entry, score in semantic_results:
        print(f"  相似度 {score:.3f}: {entry.content}")
    
    # 测试混合搜索
    print("\n🎯 混合搜索测试:")
    hybrid_results = vector_memory.hybrid_search("Python开发", max_results=3)
    for entry, score in hybrid_results:
        print(f"  综合得分 {score:.3f}: {entry.content}")
    
    # 聚类分析
    print("\n📊 记忆聚类分析:")
    cluster_info = vector_memory.analyze_memory_clusters()
    print(json.dumps(cluster_info, indent=2, ensure_ascii=False))
    
    vector_memory.close()
    print("\n✅ 向量记忆系统测试完成！")
