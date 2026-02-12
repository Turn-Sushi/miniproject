import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import { BrowserRouter, Routes, Route } from "react-router";
import { AuthProvider } from '../hooks/AuthProvider.jsx';
import Home from '@pages/Home.jsx'
import Nav from '@pages/Nav.jsx'
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
      <h1>404</h1>
      <p>페이지를 찾을 수 없습니다.</p>
    </div>
  )
}

const App = () => {
  const paths = [
    {path: "/", element: <Home />},
    {path: "*", element: <NotFound />},
    {path: "login", element: <Login />},
    {path: "signup", element: <SignUp />},
    {path: "userview", element: <UserView />},
    // {path="/boardview/:no" element: <BoardView />,
    {path: "useredit", element: <UserEdit />},
    {path: "boardadd", element: <BoardAdd />},
    {path: "boardview/:no", element: <BoardView />},
    {path: "boardedit", element: <BoardEdit />},
  ]
  return (
    <BrowserRouter>
      <AuthProvider>
        <Nav />
        <Routes>
          { paths?.map((v, i) => <Route key={i} path={v.path} element={v.element} />) }
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App