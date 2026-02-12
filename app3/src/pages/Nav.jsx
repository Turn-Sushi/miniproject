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
        <nav className="navbar navbar-expand-lg bg-body-tertiary">
		<div className="container-fluid position-relative">
			<a className="navbar-brand" href="./index.html">TEAM2</a>
			<div className="d-flex">
			<img src="./src/img01.jpg" className="border user_pt_nav01 mt-1 object-fit-cover" />
			<button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
				aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
				<span className="navbar-toggler-icon"></span>
			</button>
			</div>
			<div className="collapse navbar-collapse w-100" id="navbarNav">
				<div className="nav_box">
					<ul className="navbar-nav mt-2 me-auto">
						<li className="nav-item ">
							<a className="nav-link" href="/login">로그인</a>
						</li>
						<li className="nav-item">
							<a className="nav-link" href="/">로그아웃</a>
						</li>
						<li className="nav-item">
							<a className="nav-link" href="/signup">회원가입</a>
						</li>
						<li className="nav-item">
							<a className="nav-link" href="../user/user_view.html">회원정보</a>
						</li>
					</ul>
					<img src="./src/img01.jpg" className="border user_pt_nav mt-1 object-fit-cover" />
				</div>
			</div>
		</div>
	</nav>
    );
};

export default Nav;