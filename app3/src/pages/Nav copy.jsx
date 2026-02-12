import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/AuthProvider.jsx';

const Nav = () => {
    const navigate = useNavigate();
    // AuthProvider의 value={{ isLogin, login, logout }} 와 이름을 맞춰야 함!
    const { isLogin, logout } = useAuth(); 

    const handleLogout = () => {
        logout();
        alert('로그아웃 되었습니다.');
        navigate('/');
    };

    return (
        <nav className="navbar navbar-expand-lg bg-dark navbar-dark mb-4">
            <div className="container-fluid">
                <Link className="navbar-brand" to="/">TEAM3</Link>
                {/* collapse를 빼고 d-flex를 넣어서 무조건 보이게 수정했습니다 */}
                {!isLogin ? ( 
                            <>
                                
                            </>
                        ) : (
                            <div className="d-flex">   
                                <img src="../img01.jpg" className="border user_pt_nav01 mt-1 object-fit-cover" />
                                <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
                                    aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                                    <span className="navbar-toggler-icon"></span>
                                </button>
                            </div>
                        )}
                
                <div className="d-flex" id="navbarNav">
                    <ul className="navbar-nav flex-row gap-3">
                        {!isLogin ? ( 
                            <>
                                <li className="nav-item"><Link className="nav-link" to="/login">로그인</Link></li>
                                <li className="nav-item"><Link className="nav-link" to="/signup">회원가입</Link></li>
                            </>
                        ) : (
                            <>
                                <li className="nav-item">
                                    <button className="nav-link btn btn-link" style={{textDecoration:'none'}} onClick={handleLogout}>로그아웃</button>
                                </li>
                                <li className="nav-item"><Link className="nav-link" to="/UserView">회원정보</Link></li>
                                {/* <div className="d-flex">   
                                    <img src="../img01.jpg" className="border user_pt_nav01 mt-1 object-fit-cover" />
                                    <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
                                        aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                                        <span className="navbar-toggler-icon"></span>
                                    </button>
                                </div> */}
                            </>
                        )}
                    </ul>
                </div>
            </div>
        </nav>
    );
};

export default Nav;