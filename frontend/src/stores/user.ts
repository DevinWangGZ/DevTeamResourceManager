import { defineStore } from 'pinia'
import { ref } from 'vue'

interface UserInfo {
  id: number
  username: string
  email: string
  role: string
}

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null as UserInfo | null,
    token: '',
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.token,
  },
  
  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem('token', token)
    },
    
    setUserInfo(userInfo: UserInfo) {
      this.userInfo = userInfo
    },
    
    logout() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('token')
    },
  },
})
