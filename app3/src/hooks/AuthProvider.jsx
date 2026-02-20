import { createContext, useContext, useState, useEffect } from "react"
import { useNavigate } from "react-router";
import Home from '@pages/Home.jsx'
import Login from '@pages/Login.jsx'
import SignUp from '@pages/SignUp.jsx'
import UserView from '@pages/UserView.jsx'
import UserEdit from '@pages/UserEdit.jsx'
import BoardAdd from '@pages/BoardAdd.jsx'
import BoardView from '@pages/BoardView.jsx'
import BoardEdit from '@pages/BoardEdit.jsx'

const NotFound = () => {
  return (
    <div className="text-center">
      {/* <h1>404</h1> */}
      <img src="/images/404.gif" alt="요청하신 페이지를 찾을 수 없습니다."/>
      {/* <p>요청하신 페이지를 찾을 수 없습니다.</p> */}
    </div>
  )
}

// 로그아웃 상태
const getPath1 = () => {
  return [
    {path: "/", element: <Home />},
    {path: "*", element: <NotFound />},
    {path: "login", element: <Login />},
    {path: "signup", element: <SignUp />},
    {path: "boardview/:no", element: <BoardView />},
  ]
}

// 로그인 상태
const getPath2 = () => {
  return [
    {path: "/", element: <Home />},
    {path: "*", element: <NotFound />},
    {path: "login", element: <Login />},
    {path: "signup", element: <SignUp />},
    {path: "userview", element: <UserView />},
    {path: "useredit", element: <UserEdit />},
    {path: "boardadd", element: <BoardAdd />},
    {path: "boardview/:no", element: <BoardView />},
    {path: "boardedit/:no", element: <BoardEdit />},
  ]
}

export const AuthContext = createContext()

const AuthProvider = ({children}) => {
  const [isPending, setIsPending] = useState(false)
  const [isLogin, setIsLogin] = useState(false)
  const navigate = useNavigate()

  const setAuth = status => {
    localStorage.setItem("user", "true");
    setIsLogin(true);
    navigate("/");
  }

  const clearAuth = () => {
    localStorage.removeItem("user")
    setIsLogin(false)
    navigate("/")
  }

  const [paths, setPaths] = useState(getPath1())
  useEffect(()=>{
    // 쿠키(access_token)나 localStorage 둘 중 하나라도 있으면 로그인으로 간주
    const hasToken = document.cookie.includes("access_token");
    const hasUserFlag = localStorage.getItem("user");
    if(hasToken || hasUserFlag) {
      setIsLogin(true)
      setPaths(getPath2())
    } else {
      setIsLogin(false)
      setPaths(getPath1())
    }
    setIsPending(true)
  }, [isLogin])

  return (
    <AuthContext.Provider value={{ paths, setAuth, clearAuth, isLogin, isPending }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

export default AuthProvider