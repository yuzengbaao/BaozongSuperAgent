#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : instant_validation_test.py  
@Time    : 2025年07月19日 19:35:00
@Author  : 宝总
@Version : 1.0
@Desc    : SuperAgent瞬间修复效果验证测试
"""

import asyncio
import sys
import time
import json
from typing import List, Dict
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from core.agent_core import BaozongSuperAgent


class AgentValidator:
    """Agent性能验证器"""
    
    def __init__(self):
        self.agent = None
        self.test_results = []
        
    async def setup(self):
        """初始化Agent"""
        print("🚀 初始化SuperAgent...")
        self.agent = BaozongSuperAgent("验证测试Agent")
        print("✅ Agent启动完成")
        
    async def run_comprehensive_test(self):
        """运行综合测试"""
        
        # 定义测试用例
        test_cases = [
            {
                "name": "能力介绍测试",
                "query": "你好，介绍一下你的能力",
                "expected_keywords": ["能力", "记忆", "任务", "技术"],
                "min_length": 200,
                "importance": "high"
            },
            {
                "name": "技术问题测试", 
                "query": "如何优化Python异步编程的性能？",
                "expected_keywords": ["异步", "性能", "asyncio", "并发"],
                "min_length": 300,
                "importance": "high"
            },
            {
                "name": "API设计测试",
                "query": "设计高并发Web API的最佳实践是什么？",
                "expected_keywords": ["API", "并发", "最佳实践", "设计"],
                "min_length": 300,
                "importance": "high"  
            },
            {
                "name": "记忆系统测试",
                "query": "你的记忆系统是如何工作的？",
                "expected_keywords": ["记忆", "系统", "存储", "检索"],
                "min_length": 200,
                "importance": "medium"
            },
            {
                "name": "任务管理测试",
                "query": "帮我创建一个学习AI Agent开发的任务",
                "expected_keywords": ["任务", "创建", "AI Agent", "学习"],
                "min_length": 150,
                "importance": "medium"
            }
        ]
        
        print(f"\n📊 开始执行 {len(test_cases)} 个测试用例...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- 测试 {i}/{len(test_cases)}: {test_case['name']} ---")
            
            start_time = time.time()
            
            try:
                # 执行查询
                response = await self.agent.process_query(test_case["query"])
                
                # 记录响应时间
                response_time = time.time() - start_time
                
                # 分析结果
                result = self.analyze_response(test_case, response, response_time)
                self.test_results.append(result)
                
                # 显示结果摘要
                self.display_test_result(result)
                
            except Exception as e:
                print(f"❌ 测试失败: {str(e)}")
                self.test_results.append({
                    "test_name": test_case["name"],
                    "success": False,
                    "error": str(e),
                    "score": 0
                })
            
            # 短暂延迟避免过快请求
            await asyncio.sleep(0.5)
        
        # 生成综合报告
        await self.generate_final_report()
        
    def analyze_response(self, test_case: Dict, response, response_time: float) -> Dict:
        """分析响应质量"""
        
        result = {
            "test_name": test_case["name"],
            "query": test_case["query"], 
            "success": response.success,
            "response_time": response_time,
            "message_length": len(response.message),
            "suggestions_count": len(response.suggestions) if response.suggestions else 0,
            "next_actions_count": len(response.next_actions) if response.next_actions else 0,
            "confidence": response.data.get("confidence", 0) if response.data else 0,
            "score": 0,
            "quality_metrics": {}
        }
        
        if not response.success:
            return result
            
        score = 0
        quality_metrics = {}
        
        # 1. 长度检查 (30分)
        if result["message_length"] >= test_case["min_length"]:
            length_score = 30
            quality_metrics["length"] = "✅ 符合要求"
        else:
            length_score = max(0, int(30 * result["message_length"] / test_case["min_length"]))
            quality_metrics["length"] = f"⚠️ 长度不足 ({result['message_length']}/{test_case['min_length']})"
        score += length_score
        
        # 2. 关键词覆盖 (25分)
        message_lower = response.message.lower()
        matched_keywords = [kw for kw in test_case["expected_keywords"] if kw.lower() in message_lower]
        keyword_score = int(25 * len(matched_keywords) / len(test_case["expected_keywords"]))
        score += keyword_score
        quality_metrics["keywords"] = f"✅ {len(matched_keywords)}/{len(test_case['expected_keywords'])} 关键词匹配"
        
        # 3. 结构化程度 (20分)
        structure_indicators = ["**", "###", "•", "-", "1.", "2.", "3.", "```"]
        structure_count = sum(1 for indicator in structure_indicators if indicator in response.message)
        structure_score = min(20, structure_count * 4)  # 最多20分
        score += structure_score
        quality_metrics["structure"] = f"✅ 结构化元素: {structure_count}"
        
        # 4. 互动性 (15分)
        interactivity_score = 0
        if result["suggestions_count"] > 0:
            interactivity_score += 8
        if result["next_actions_count"] > 0:
            interactivity_score += 7
        score += interactivity_score
        quality_metrics["interactivity"] = f"✅ 建议:{result['suggestions_count']}, 行动:{result['next_actions_count']}"
        
        # 5. 响应速度 (10分)
        if response_time < 1.0:
            speed_score = 10
        elif response_time < 3.0:
            speed_score = 7
        elif response_time < 5.0:
            speed_score = 5
        else:
            speed_score = 2
        score += speed_score
        quality_metrics["speed"] = f"✅ 响应时间: {response_time:.2f}秒"
        
        result["score"] = score
        result["quality_metrics"] = quality_metrics
        
        return result
        
    def display_test_result(self, result: Dict):
        """显示测试结果"""
        score = result["score"]
        
        # 评级
        if score >= 90:
            grade = "🏆 优秀"
            emoji = "🎉"
        elif score >= 80:
            grade = "⭐ 良好"
            emoji = "👍"
        elif score >= 70:
            grade = "✅ 及格"
            emoji = "👌"
        else:
            grade = "❌ 需改进"
            emoji = "⚠️"
            
        print(f"{emoji} 测试结果: {grade} (得分: {score}/100)")
        print(f"⏱️ 响应时间: {result['response_time']:.2f}秒")
        print(f"📝 响应长度: {result['message_length']}字符")
        print(f"🎯 置信度: {result['confidence']}")
        
        # 显示质量指标
        for metric, description in result["quality_metrics"].items():
            print(f"   {description}")
    
    async def generate_final_report(self):
        """生成最终报告"""
        print("\n" + "="*60)
        print("🎯 SuperAgent瞬间修复效果验证报告")
        print("="*60)
        
        # 计算总体统计
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        total_score = sum(r["score"] for r in self.test_results)
        average_score = total_score / total_tests if total_tests > 0 else 0
        average_response_time = sum(r["response_time"] for r in self.test_results) / total_tests
        
        print(f"\n📊 整体统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   成功率: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"   平均得分: {average_score:.1f}/100")
        print(f"   平均响应时间: {average_response_time:.2f}秒")
        
        # 质量等级评估
        if average_score >= 90:
            quality_grade = "🏆 卓越级"
            assessment = "瞬间修复器效果显著，回答质量达到专业级别"
        elif average_score >= 80:
            quality_grade = "⭐ 优秀级"
            assessment = "修复效果良好，大部分响应达到高质量标准"
        elif average_score >= 70:
            quality_grade = "✅ 合格级"  
            assessment = "基本达到预期，仍有进一步优化空间"
        else:
            quality_grade = "❌ 需改进"
            assessment = "修复效果有限，需要进一步调优"
            
        print(f"\n🎖️ 质量评级: {quality_grade}")
        print(f"💡 评估结论: {assessment}")
        
        # 详细测试结果表格
        print(f"\n📋 详细测试结果:")
        print("-" * 80)
        print(f"{'测试名称':<20} {'得分':<8} {'时间':<8} {'长度':<8} {'状态'}")
        print("-" * 80)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{result['test_name']:<20} {result['score']:<8} {result['response_time']:.2f}s    {result['message_length']:<8} {status}")
        
        # 保存报告到文件
        report_data = {
            "timestamp": time.time(),
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": successful_tests/total_tests*100,
                "average_score": average_score,
                "average_response_time": average_response_time,
                "quality_grade": quality_grade,
                "assessment": assessment
            },
            "detailed_results": self.test_results
        }
        
        report_file = Path("SuperAgent_瞬间修复验证报告.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 详细报告已保存至: {report_file}")
        
        # 改进建议
        if average_score < 85:
            print(f"\n🔧 改进建议:")
            
            # 分析主要问题
            low_scores = [r for r in self.test_results if r["score"] < 80]
            if low_scores:
                print(f"   • {len(low_scores)} 个测试得分较低，建议针对性优化")
                
            slow_responses = [r for r in self.test_results if r["response_time"] > 2.0]
            if slow_responses:
                print(f"   • {len(slow_responses)} 个测试响应较慢，考虑性能优化")
                
            short_responses = [r for r in self.test_results if r["message_length"] < 200]
            if short_responses:
                print(f"   • {len(short_responses)} 个测试响应较短，可扩展内容深度")
        
        print(f"\n🎉 验证测试完成！Agent瞬间修复器运行{quality_grade}")


async def main():
    """主函数"""
    print("🔬 SuperAgent瞬间修复效果验证开始")
    print("=" * 50)
    
    validator = AgentValidator()
    
    try:
        await validator.setup()
        await validator.run_comprehensive_test()
        
    except Exception as e:
        print(f"❌ 验证过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 验证测试结束")


if __name__ == "__main__":
    asyncio.run(main())
