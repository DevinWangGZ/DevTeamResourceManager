<template>
  <div class="profile-container">
    <Breadcrumb />
    <el-card>
      <template #header>
        <div class="profile-header">
          <h2>个人档案</h2>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="card">
        <!-- 个人信息 -->
        <el-tab-pane label="个人信息" name="info">
          <el-card shadow="never">
            <el-form :model="userInfo" label-width="100px" style="max-width: 600px">
              <el-form-item label="用户名">
                <el-input v-model="userInfo.username" disabled />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="userInfo.email" disabled />
              </el-form-item>
              <el-form-item label="姓名">
                <el-input v-model="userInfo.full_name" />
              </el-form-item>
              <el-form-item label="角色">
                <el-tag>{{ getRoleName(userInfo.role) }}</el-tag>
              </el-form-item>
              <el-form-item label="状态标签">
                <el-input
                  v-model="userInfo.status_tag"
                  placeholder="如：🚀火力全开、💻编码中"
                  maxlength="50"
                  show-word-limit
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="updateUserInfo">保存</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-tab-pane>

        <!-- 技能管理 -->
        <el-tab-pane label="技能管理" name="skills">
          <el-card shadow="never">
            <div class="section-header">
              <h3>我的技能</h3>
              <el-button type="primary" @click="showSkillDialog = true">
                <el-icon><Plus /></el-icon>
                添加技能
              </el-button>
            </div>

            <el-table :data="skillList" v-loading="skillLoading" stripe>
              <el-table-column prop="name" label="技能名称" />
              <el-table-column prop="proficiency" label="熟练度" width="120">
                <template #default="{ row }">
                  <el-tag :type="getProficiencyType(row.proficiency)">
                    {{ getProficiencyText(row.proficiency) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button link type="primary" size="small" @click="editSkill(row)">
                    编辑
                  </el-button>
                  <el-button link type="danger" size="small" @click="handleDeleteSkill(row.id)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <!-- 业务履历 -->
        <el-tab-pane label="业务履历" name="experiences">
          <el-card shadow="never">
            <div class="section-header">
              <h3>我的业务履历</h3>
              <el-button type="primary" @click="showExperienceDialog = true">
                <el-icon><Plus /></el-icon>
                添加履历
              </el-button>
            </div>

            <el-table :data="experienceList" v-loading="experienceLoading" stripe>
              <el-table-column prop="project" label="项目" />
              <el-table-column prop="module" label="模块" />
              <el-table-column prop="role" label="角色" />
              <el-table-column prop="man_days" label="投入人天" width="100" />
              <el-table-column prop="description" label="贡献描述" show-overflow-tooltip />
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button link type="primary" size="small" @click="editExperience(row)">
                    编辑
                  </el-button>
                  <el-button link type="danger" size="small" @click="handleDeleteExperience(row.id)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <!-- 序列管理 -->
        <el-tab-pane label="序列管理" name="sequences">
          <el-card shadow="never">
            <div class="section-header">
              <h3>我的序列等级</h3>
              <el-button type="primary" @click="showSequenceDialog = true">
                <el-icon><Plus /></el-icon>
                添加序列
              </el-button>
            </div>

            <el-table :data="sequenceList" v-loading="sequenceLoading" stripe>
              <el-table-column prop="level" label="序列等级" />
              <el-table-column prop="unit_price" label="单价（元/人天）" width="150">
                <template #default="{ row }">
                  ¥{{ row.unit_price }}
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button link type="primary" size="small" @click="editSequence(row)">
                    编辑
                  </el-button>
                  <el-button link type="danger" size="small" @click="handleDeleteSequence(row.id)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 技能对话框 -->
    <el-dialog
      v-model="showSkillDialog"
      :title="editingSkill ? '编辑技能' : '添加技能'"
      width="500px"
      @close="resetSkillForm"
    >
      <el-form ref="skillFormRef" :model="skillForm" :rules="skillRules" label-width="80px">
        <el-form-item label="技能名称" prop="name">
          <el-input v-model="skillForm.name" placeholder="请输入技能名称" />
        </el-form-item>
        <el-form-item label="熟练度" prop="proficiency">
          <el-select v-model="skillForm.proficiency" placeholder="请选择熟练度" style="width: 100%">
            <el-option label="熟悉" value="familiar" />
            <el-option label="熟练" value="proficient" />
            <el-option label="精通" value="expert" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSkillDialog = false">取消</el-button>
        <el-button type="primary" :loading="skillSaving" @click="saveSkill">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 履历对话框 -->
    <el-dialog
      v-model="showExperienceDialog"
      :title="editingExperience ? '编辑业务履历' : '添加业务履历'"
      width="600px"
      @close="resetExperienceForm"
    >
      <el-form ref="experienceFormRef" :model="experienceForm" :rules="experienceRules" label-width="100px">
        <el-form-item label="项目名称" prop="project">
          <el-input v-model="experienceForm.project" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="模块名称" prop="module">
          <el-input v-model="experienceForm.module" placeholder="请输入模块名称（可选）" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-input v-model="experienceForm.role" placeholder="请输入角色（可选）" />
        </el-form-item>
        <el-form-item label="投入人天" prop="man_days">
          <el-input-number
            v-model="experienceForm.man_days"
            :min="0"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="贡献描述" prop="description">
          <el-input
            v-model="experienceForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入贡献描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExperienceDialog = false">取消</el-button>
        <el-button type="primary" :loading="experienceSaving" @click="saveExperience">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 序列对话框 -->
    <el-dialog
      v-model="showSequenceDialog"
      :title="editingSequence ? '编辑序列' : '添加序列'"
      width="500px"
      @close="resetSequenceForm"
    >
      <el-form ref="sequenceFormRef" :model="sequenceForm" :rules="sequenceRules" label-width="100px">
        <el-form-item label="序列等级" prop="level">
          <el-input v-model="sequenceForm.level" placeholder="如：初级开发、中级开发、高级开发" />
        </el-form-item>
        <el-form-item label="单价" prop="unit_price">
          <el-input-number
            v-model="sequenceForm.unit_price"
            :min="0.01"
            :precision="2"
            style="width: 100%"
          />
          <div class="form-tip">单位：元/人天</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSequenceDialog = false">取消</el-button>
        <el-button type="primary" :loading="sequenceSaving" @click="saveSequence">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import Breadcrumb from '@/components/layout/Breadcrumb.vue'
import {
  getSkills,
  createSkill,
  updateSkill,
  deleteSkill as deleteSkillApi,
  type Skill,
  type SkillCreate,
} from '@/api/skill'
import {
  getExperiences,
  createExperience,
  updateExperience,
  deleteExperience as deleteExperienceApi,
  type Experience,
  type ExperienceCreate,
} from '@/api/experience'
import {
  getUserSequences,
  createUserSequence,
  updateUserSequence,
  deleteUserSequence as deleteUserSequenceApi,
  type UserSequence,
  type UserSequenceCreate,
} from '@/api/userSequence'
import { getCurrentUser, type UserInfo } from '@/api/auth'
import { updateUser } from '@/api/user'

const userStore = useUserStore()

const activeTab = ref('info')
const userInfo = reactive<UserInfo>({
  id: 0,
  username: '',
  email: '',
  full_name: null,
  role: '',
  status_tag: null,
  is_active: true,
})

// 技能相关
const skillLoading = ref(false)
const skillList = ref<Skill[]>([])
const showSkillDialog = ref(false)
const skillSaving = ref(false)
const skillFormRef = ref<FormInstance>()
const editingSkill = ref<Skill | null>(null)
const skillForm = reactive<SkillCreate>({
  name: '',
  proficiency: 'familiar',
})

// 履历相关
const experienceLoading = ref(false)
const experienceList = ref<Experience[]>([])
const showExperienceDialog = ref(false)
const experienceSaving = ref(false)
const experienceFormRef = ref<FormInstance>()
const editingExperience = ref<Experience | null>(null)
const experienceForm = reactive<ExperienceCreate>({
  project: '',
  module: '',
  role: '',
  description: '',
  man_days: 0,
})

// 序列相关
const sequenceLoading = ref(false)
const sequenceList = ref<UserSequence[]>([])
const showSequenceDialog = ref(false)
const sequenceSaving = ref(false)
const sequenceFormRef = ref<FormInstance>()
const editingSequence = ref<UserSequence | null>(null)
const sequenceForm = reactive<UserSequenceCreate>({
  level: '',
  unit_price: 0,
})

const skillRules: FormRules = {
  name: [{ required: true, message: '请输入技能名称', trigger: 'blur' }],
  proficiency: [{ required: true, message: '请选择熟练度', trigger: 'change' }],
}

const experienceRules: FormRules = {
  project: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  man_days: [{ required: true, message: '请输入投入人天', trigger: 'blur' }],
}

const sequenceRules: FormRules = {
  level: [{ required: true, message: '请输入序列等级', trigger: 'blur' }],
  unit_price: [{ required: true, message: '请输入单价', trigger: 'blur' }],
}

const getRoleName = (role: string) => {
  const roleMap: Record<string, string> = {
    developer: '开发人员',
    project_manager: '项目经理',
    development_lead: '开发组长',
    system_admin: '系统管理员',
  }
  return roleMap[role] || role
}

const getProficiencyText = (proficiency: string) => {
  const map: Record<string, string> = {
    familiar: '熟悉',
    proficient: '熟练',
    expert: '精通',
  }
  return map[proficiency] || proficiency
}

const getProficiencyType = (proficiency: string) => {
  const map: Record<string, string> = {
    familiar: 'info',
    proficient: 'warning',
    expert: 'success',
  }
  return map[proficiency] || ''
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadUserInfo = async () => {
  try {
    const info = await getCurrentUser()
    Object.assign(userInfo, info)
  } catch (error) {
    ElMessage.error('加载用户信息失败')
  }
}

const updateUserInfo = async () => {
  try {
    await updateUser({
      full_name: userInfo.full_name || undefined,
      status_tag: userInfo.status_tag || undefined,
    })
    ElMessage.success('保存成功')
    await loadUserInfo()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

const loadSkills = async () => {
  skillLoading.value = true
  try {
    const result = await getSkills()
    skillList.value = result.items
  } catch (error) {
    ElMessage.error('加载技能列表失败')
  } finally {
    skillLoading.value = false
  }
}

const editSkill = (skill: Skill) => {
  editingSkill.value = skill
  skillForm.name = skill.name
  skillForm.proficiency = skill.proficiency as 'familiar' | 'proficient' | 'expert'
  showSkillDialog.value = true
}

const saveSkill = async () => {
  if (!skillFormRef.value) return

  await skillFormRef.value.validate(async (valid) => {
    if (valid) {
      skillSaving.value = true
      try {
        if (editingSkill.value) {
          await updateSkill(editingSkill.value.id, skillForm)
          ElMessage.success('技能更新成功')
        } else {
          await createSkill(skillForm)
          ElMessage.success('技能添加成功')
        }
        showSkillDialog.value = false
        loadSkills()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        skillSaving.value = false
      }
    }
  })
}

const handleDeleteSkill = async (skillId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此技能吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteSkillApi(skillId)
    ElMessage.success('删除成功')
    loadSkills()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const resetSkillForm = () => {
  skillFormRef.value?.resetFields()
  editingSkill.value = null
  skillForm.name = ''
  skillForm.proficiency = 'familiar'
}

const loadExperiences = async () => {
  experienceLoading.value = true
  try {
    const result = await getExperiences()
    experienceList.value = result.items
  } catch (error) {
    ElMessage.error('加载业务履历列表失败')
  } finally {
    experienceLoading.value = false
  }
}

const editExperience = (experience: Experience) => {
  editingExperience.value = experience
  experienceForm.project = experience.project
  experienceForm.module = experience.module || ''
  experienceForm.role = experience.role || ''
  experienceForm.description = experience.description || ''
  experienceForm.man_days = experience.man_days
  showExperienceDialog.value = true
}

const saveExperience = async () => {
  if (!experienceFormRef.value) return

  await experienceFormRef.value.validate(async (valid) => {
    if (valid) {
      experienceSaving.value = true
      try {
        if (editingExperience.value) {
          await updateExperience(editingExperience.value.id, experienceForm)
          ElMessage.success('业务履历更新成功')
        } else {
          await createExperience(experienceForm)
          ElMessage.success('业务履历添加成功')
        }
        showExperienceDialog.value = false
        loadExperiences()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        experienceSaving.value = false
      }
    }
  })
}

const handleDeleteExperience = async (experienceId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此业务履历吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteExperienceApi(experienceId)
    ElMessage.success('删除成功')
    loadExperiences()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const resetExperienceForm = () => {
  experienceFormRef.value?.resetFields()
  editingExperience.value = null
  experienceForm.project = ''
  experienceForm.module = ''
  experienceForm.role = ''
  experienceForm.description = ''
  experienceForm.man_days = 0
}

const loadSequences = async () => {
  sequenceLoading.value = true
  try {
    const result = await getUserSequences()
    sequenceList.value = result.items
  } catch (error) {
    ElMessage.error('加载序列列表失败')
  } finally {
    sequenceLoading.value = false
  }
}

const editSequence = (sequence: UserSequence) => {
  editingSequence.value = sequence
  sequenceForm.level = sequence.level
  sequenceForm.unit_price = sequence.unit_price
  showSequenceDialog.value = true
}

const saveSequence = async () => {
  if (!sequenceFormRef.value) return

  await sequenceFormRef.value.validate(async (valid) => {
    if (valid) {
      sequenceSaving.value = true
      try {
        if (editingSequence.value) {
          await updateUserSequence(editingSequence.value.id, sequenceForm)
          ElMessage.success('序列更新成功')
        } else {
          await createUserSequence(sequenceForm)
          ElMessage.success('序列添加成功')
        }
        showSequenceDialog.value = false
        loadSequences()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        sequenceSaving.value = false
      }
    }
  })
}

const handleDeleteSequence = async (sequenceId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此序列吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteUserSequenceApi(sequenceId)
    ElMessage.success('删除成功')
    loadSequences()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const resetSequenceForm = () => {
  sequenceFormRef.value?.resetFields()
  editingSequence.value = null
  sequenceForm.level = ''
  sequenceForm.unit_price = 0
}

onMounted(() => {
  loadUserInfo()
  loadSkills()
  loadExperiences()
  loadSequences()
})
</script>

<style scoped>
.profile-container {
  padding: 20px;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.profile-header h2 {
  margin: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}
</style>
