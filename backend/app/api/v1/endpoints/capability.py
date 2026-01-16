"""团队能力洞察API端点"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
from decimal import Decimal

from app.api.deps import get_db
from app.core.permissions import get_current_development_lead
from app.models.user import User
from app.models.skill import Skill, Proficiency
from app.models.user_sequence import UserSequence
from app.models.workload_statistic import WorkloadStatistic

router = APIRouter()


@router.get("/skill-matrix", response_model=dict)
async def get_skill_matrix(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_development_lead)
):
    """
    获取团队技能矩阵
    
    返回所有开发人员的技能分布情况
    """
    
    # 获取所有开发人员
    developers = db.query(User).filter(
        User.role == "developer",
        User.is_active == True
    ).all()
    
    # 获取所有技能
    all_skills = db.query(Skill.name).distinct().all()
    skill_names = [skill[0] for skill in all_skills]
    
    # 构建技能矩阵数据
    skill_matrix = []
    
    for developer in developers:
        # 获取开发人员的技能
        developer_skills = db.query(Skill).filter(
            Skill.user_id == developer.id
        ).all()
        
        # 构建技能字典
        skill_dict = {skill.name: skill.proficiency for skill in developer_skills}
        
        # 获取序列信息
        sequence = db.query(UserSequence).filter(
            UserSequence.user_id == developer.id
        ).order_by(UserSequence.created_at.desc()).first()
        
        sequence_level = sequence.level if sequence else None
        
        skill_matrix.append({
            "user_id": developer.id,
            "username": developer.username,
            "full_name": developer.full_name,
            "sequence_level": sequence_level,
            "skills": skill_dict
        })
    
    return {
        "skill_names": skill_names,
        "developers": skill_matrix
    }


@router.get("/talent-ladder", response_model=dict)
async def get_talent_ladder(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_development_lead)
):
    """
    获取人才梯队分析
    
    基于序列等级和技能水平分析人才梯队
    """
    
    # 获取所有开发人员
    developers = db.query(User).filter(
        User.role == "developer",
        User.is_active == True
    ).all()
    
    # 按序列等级分组
    ladder_data: Dict[str, List[Dict]] = {}
    
    for developer in developers:
        # 获取序列信息
        sequence = db.query(UserSequence).filter(
            UserSequence.user_id == developer.id
        ).order_by(UserSequence.created_at.desc()).first()
        
        sequence_level = sequence.level if sequence else "未设置"
        
        # 获取技能统计
        skills = db.query(Skill).filter(Skill.user_id == developer.id).all()
        total_skills = len(skills)
        expert_skills = len([s for s in skills if s.proficiency == Proficiency.EXPERT.value])
        proficient_skills = len([s for s in skills if s.proficiency == Proficiency.PROFICIENT.value])
        familiar_skills = len([s for s in skills if s.proficiency == Proficiency.FAMILIAR.value])
        
        # 获取工作量统计（最近6个月）
        from datetime import date, timedelta
        today = date.today()
        period_start = date(today.year, today.month - 5, 1) if today.month > 5 else date(today.year - 1, today.month + 7, 1)
        period_end = date(today.year, today.month, 1) - timedelta(days=1)
        
        workload_stats = db.query(WorkloadStatistic).filter(
            WorkloadStatistic.user_id == developer.id,
            WorkloadStatistic.period_start >= period_start,
            WorkloadStatistic.period_end <= period_end
        ).all()
        
        total_man_days = sum(float(stat.total_man_days) for stat in workload_stats)
        
        member_info = {
            "user_id": developer.id,
            "username": developer.username,
            "full_name": developer.full_name,
            "sequence_level": sequence_level,
            "total_skills": total_skills,
            "expert_skills": expert_skills,
            "proficient_skills": proficient_skills,
            "familiar_skills": familiar_skills,
            "total_man_days": float(total_man_days),
        }
        
        if sequence_level not in ladder_data:
            ladder_data[sequence_level] = []
        ladder_data[sequence_level].append(member_info)
    
    # 统计各梯队人数
    ladder_summary = []
    for level, members in ladder_data.items():
        ladder_summary.append({
            "level": level,
            "count": len(members),
            "avg_skills": sum(m["total_skills"] for m in members) / len(members) if members else 0,
            "avg_man_days": sum(m["total_man_days"] for m in members) / len(members) if members else 0,
        })
    
    return {
        "ladder_summary": ladder_summary,
        "ladder_data": ladder_data
    }


@router.get("/capability-distribution", response_model=dict)
async def get_capability_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_development_lead)
):
    """
    获取团队能力分布
    
    统计技能熟练度分布、序列等级分布等
    """
    
    # 获取所有开发人员
    developers = db.query(User).filter(
        User.role == "developer",
        User.is_active == True
    ).all()
    
    # 技能熟练度分布
    proficiency_distribution = {
        "expert": 0,
        "proficient": 0,
        "familiar": 0
    }
    
    # 序列等级分布
    sequence_distribution: Dict[str, int] = {}
    
    # 技能数量分布
    skill_count_distribution = {
        "0-5": 0,
        "6-10": 0,
        "11-15": 0,
        "16+": 0
    }
    
    for developer in developers:
        # 获取技能
        skills = db.query(Skill).filter(Skill.user_id == developer.id).all()
        
        # 统计熟练度
        for skill in skills:
            proficiency_distribution[skill.proficiency] = proficiency_distribution.get(skill.proficiency, 0) + 1
        
        # 统计技能数量
        skill_count = len(skills)
        if skill_count <= 5:
            skill_count_distribution["0-5"] += 1
        elif skill_count <= 10:
            skill_count_distribution["6-10"] += 1
        elif skill_count <= 15:
            skill_count_distribution["11-15"] += 1
        else:
            skill_count_distribution["16+"] += 1
        
        # 获取序列等级
        sequence = db.query(UserSequence).filter(
            UserSequence.user_id == developer.id
        ).order_by(UserSequence.created_at.desc()).first()
        
        sequence_level = sequence.level if sequence else "未设置"
        sequence_distribution[sequence_level] = sequence_distribution.get(sequence_level, 0) + 1
    
    return {
        "proficiency_distribution": proficiency_distribution,
        "sequence_distribution": sequence_distribution,
        "skill_count_distribution": skill_count_distribution,
        "total_members": len(developers)
    }
