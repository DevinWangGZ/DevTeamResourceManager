#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工作量统计功能
验证任务确认后工作量统计是否自动更新
"""
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.task import Task, TaskStatus
from app.models.workload_statistic import WorkloadStatistic
from app.models.user import User
from app.services.task_service import TaskService
from app.services.workload_statistic_service import WorkloadStatisticService
from decimal import Decimal
from datetime import date

def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def test_workload_statistics():
    """测试工作量统计功能"""
    db: Session = SessionLocal()
    
    try:
        # 1. 查看当前已提交状态的任务
        print_section("1. 查看已提交状态的任务")
        submitted_tasks = db.query(Task).filter(
            Task.status == TaskStatus.SUBMITTED.value
        ).all()
        
        if not submitted_tasks:
            print("❌ 没有找到已提交状态的任务")
            print("\n提示：需要先有任务被提交（状态为submitted）才能测试确认功能")
            print("可以：")
            print("  1. 在系统中提交一个任务")
            print("  2. 或者使用以下SQL创建一个测试任务：")
            print("""
UPDATE tasks 
SET status = 'submitted', 
    actual_man_days = 5.0,
    assignee_id = (SELECT id FROM users WHERE username = 'dev001' LIMIT 1)
WHERE id = (SELECT id FROM tasks LIMIT 1);
            """)
            return
        
        print(f"✓ 找到 {len(submitted_tasks)} 个已提交的任务：")
        for task in submitted_tasks:
            print(f"  - 任务ID: {task.id}, 标题: {task.title}")
            print(f"    认领人ID: {task.assignee_id}, 实际投入人天: {task.actual_man_days}")
        
        # 选择第一个任务进行测试
        test_task = submitted_tasks[0]
        print(f"\n选择任务 {test_task.id} 进行测试")
        
        # 如果任务没有实际投入人天，设置一个测试值
        if not test_task.actual_man_days:
            print(f"⚠️  任务没有实际投入人天，设置为 5.0 进行测试")
            test_task.actual_man_days = Decimal("5.0")
            db.commit()
            db.refresh(test_task)
        
        # 2. 查看确认前的工作量统计
        print_section("2. 查看确认前的工作量统计")
        assignee_id = test_task.assignee_id
        project_id = test_task.project_id
        
        before_stats = db.query(WorkloadStatistic).filter(
            WorkloadStatistic.user_id == assignee_id,
            WorkloadStatistic.project_id == project_id
        ).all()
        
        print(f"用户ID {assignee_id} 在项目ID {project_id} 的统计记录数: {len(before_stats)}")
        total_before = sum(float(stat.total_man_days) for stat in before_stats)
        print(f"确认前的总投入人天: {total_before}")
        
        # 3. 获取项目经理用户
        print_section("3. 获取项目经理用户")
        pm_user = db.query(User).filter(User.role == "project_manager").first()
        if not pm_user:
            print("❌ 没有找到项目经理用户")
            return
        
        print(f"✓ 找到项目经理: {pm_user.username} (ID: {pm_user.id})")
        
        # 4. 确认任务
        print_section("4. 确认任务")
        print(f"正在确认任务 {test_task.id}...")
        
        try:
            confirmed_task = TaskService.confirm_task(
                db=db,
                task_id=test_task.id,
                current_user_id=pm_user.id,
                current_user_role=pm_user.role
            )
            print(f"✓ 任务确认成功！任务状态: {confirmed_task.status}")
        except Exception as e:
            print(f"❌ 任务确认失败: {e}")
            return
        
        # 5. 查看确认后的工作量统计
        print_section("5. 查看确认后的工作量统计")
        after_stats = db.query(WorkloadStatistic).filter(
            WorkloadStatistic.user_id == assignee_id,
            WorkloadStatistic.project_id == project_id
        ).all()
        
        print(f"用户ID {assignee_id} 在项目ID {project_id} 的统计记录数: {len(after_stats)}")
        total_after = sum(float(stat.total_man_days) for stat in after_stats)
        print(f"确认后的总投入人天: {total_after}")
        
        # 6. 验证结果
        print_section("6. 验证结果")
        expected_increase = float(test_task.actual_man_days) if test_task.actual_man_days else 0
        
        if abs(total_after - total_before - expected_increase) < 0.01:
            print("✅ 测试通过！工作量统计已正确更新")
            print(f"   增加的人天: {expected_increase}")
            print(f"   统计记录数变化: {len(before_stats)} -> {len(after_stats)}")
        else:
            print("❌ 测试失败！工作量统计更新不正确")
            print(f"   预期增加: {expected_increase}")
            print(f"   实际增加: {total_after - total_before}")
        
        # 7. 显示最新的统计记录
        if after_stats:
            print_section("7. 最新的统计记录")
            latest_stat = max(after_stats, key=lambda s: s.created_at)
            print(f"统计ID: {latest_stat.id}")
            print(f"用户ID: {latest_stat.user_id}")
            print(f"项目ID: {latest_stat.project_id}")
            print(f"总投入人天: {latest_stat.total_man_days}")
            print(f"统计周期: {latest_stat.period_start} ~ {latest_stat.period_end}")
            print(f"创建时间: {latest_stat.created_at}")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print(" 工作量统计功能测试")
    print("=" * 60)
    test_workload_statistics()
    print("\n" + "=" * 60)
    print(" 测试完成")
    print("=" * 60)
