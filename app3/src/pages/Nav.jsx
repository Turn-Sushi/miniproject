import { useState } from 'react'
import { useNavigate } from 'react-router'
import { useAuth } from '@hooks/AuthProvider.jsx'

const Nav = () => {
  const navigate = useNavigate();
  // AuthProvider의 value={{ isLogin, login, logout }} 와 이름을 맞춰야 함!
  const { isLogin, clearAuth } = useAuth();
  const [fileName, setFileName] = useState("")

  const handleLogout = () => {
    clearAuth();
    alert('로그아웃 되었습니다.');
    navigate('/');
  };

  return (
    <nav className="navbar navbar-expand-lg bg-body-tertiary">
      <div className="container-fluid position-relative">

        <a className="navbar-brand" href="/">TEAM3</a>
        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
          aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse mt-3 mt-lg-0" id="navbarNav">
          <div className="nav_box">
            <ul className="navbar-nav align-items-center gap-3 ms-auto" >
              {!isLogin ? (
                <>
                  <li className="nav-item"><a className="nav-a" href="/login">로그인</a></li>
                  <li className="nav-item"><a className="nav-a" href="/signup">회원가입</a></li>
                </>
              ) : (
                <>
                  <li className="nav-item">
                    <button className="nav-a btn btn-a" onClick={handleLogout}>로그아웃</button>
                  </li>
                  <li className="nav-item"><a className="nav-a" href="/userview">회원정보</a></li>
                  <li className="nav-item">
                    {/* 여기에 fileName을 불러와야함.... 현재 주석처리해둠 */}
                    {/* <img
                      src={
                        fileName
                        ? `${API_URL}/uploads/${fileName}`
                        : "/images/img01.jpg"
                      }
                      alt={comment.origin || "default"}
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = "/images/img01.jpg";
                      }}
                      className="border user_pt_nav mt-0 object-fit-cover rounded-circle"
                      style={{ width: '40px', height: '40px' }}
                      /> */}
                    <img
                      src="/images/img01.jpg"
                      className="border user_pt_nav mt-0 object-fit-cover rounded-circle"
                      style={{ width: '40px', height: '40px' }}
                    />
                  </li>
                </>
              )}
              {/* <li className="nav-item">
                  <img 
                    src="/images/img01.jpg"
                    className="border user_pt_nav mt-0 object-fit-cover rounded-circle" 
                    style={{ width: '40px', height: '40px' }}
                  />
                </li> */}
            </ul>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Nav;
