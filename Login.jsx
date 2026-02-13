import React, { useState } from 'react';
import { api } from '@/utils/network.js';
import axios from 'axios';
import { useAuth } from '@/hooks/AuthProvider.jsx';
import { useNavigate } from 'react-router';

axios.defaults.withCredentials = true;

const Login = () => {
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [token, setToken] = useState("")
  const [userNo, setUserNo] = useState("")

  const navigate = useNavigate();
  // const { login } = useAuth();

  const reset = () => {
    setToken("")
    setUserNo("")
  }

  // const handleLogin = async () => {
  // try {
  //     const response = await api.post("/login", {email});
  //     if (response.data.status) {
  //         const { access_token, user_id } = response.data;
  //         login(access_token, user_id); 
  //         navigate("/");
  //     }
  // } catch (error) {
  //     alert(error.response?.data?.detail || "로그인 실패");
  // }
  // };

  // const event1 = e => {
  //   e.preventDefault()
  //   console.log("코드 발급", e.target.email.value)
  //   axios.post("http://localhost:8001/login", {email})
  //   .then(res => {
  //     console.log(res)
  //     if(res.data.status) {
  //       e.target.email.value = ""
  //       alert("인증번호 발송 완료")
  //     } else alert("입력하신 Email은 존재하지 않습니다.")
  //   })
  //   .catch(err => console.error(err))
  // }

  const event1 = async e => {
    e.preventDefault()
    console.log("코드 발급", e.target.email.value)
    try {
      const res = await axios.post(
        "http://localhost:8001/login",
        { email },
        { withCredentials: true }
      );

      if (res.data.status) {
        alert("인증번호 발송 완료");
      } else {
        alert("입력하신 Email은 존재하지 않습니다.");
      }
    } catch (err) {
      console.error(err);
      alert("서버 오류");
    }
  };//

  const event2 = async e => {
    e.preventDefault()
    console.log("토큰 발급", code)
    try {
    const res = await axios.post(
      "http://localhost:8001/code",
      { id: code },
      { withCredentials: true }
    );

    if (res.data.status) {
      setToken(res.data.access_token);
      alert("인증되었습니다.");
      setCode("");
    } else {
      alert("!!!!!!!!!!!!!!!!!!!!!!인증 실패!!!!!!!!!!!!!!!!!!!!!!");
    }
  } catch (err) {
    console.error(err);
  }
};

  // const event3 = () => {
  //   console.log("사용자 정보 요청")
  //   axios.post("http://localhost:8001/me", {}, 
  //     {headers: {"Authorization": `Bearer ${token}`}}
  //   ).then(res => {
  //     console.log(res)
  //     if(res.data.status) {
  //       const header = jwtDecode(token, { header: true })
  //       const now = Math.floor(Date.now() / 1000)
  //       if (header.exp && header.exp < now) {
  //         alert("인증코드가 만료되었습니다.")
  //         reset()
  //         return
  //       }        
  //       setUserNo(res.data.userNo)
  //       setEmail(res.data.email)
  //     } else alert("인증코드 생성 실패")
  //   })
  //   .catch(err => console.error(err))
  // }

  return (
    <div className="container mt-3 box_size">
		<h1 className="display-1 text-center">로그인</h1>
		<form onSubmit={event1}>
			<div className="mb-3 mt-3">
				<label htmlFor="email" className="form-label">이메일</label>
				<input type="email" 
        className="form-control" 
        id="email" 
        placeholder="이메일를 입력하세요." 
        name="email"
        value={email}
        onChange={e => setEmail(e.target.value)} 
        />
			</div>
			<div className="d-flex mb-4">
				<div className="p-2 flex-fill d-grid">
					<button type="submit" className="btn btn-primary">메일 발송</button>
				</div>
				<div className="p-2 flex-fill d-grid ">
					<button type="button" className="btn btn-primary" onClick={()=>navigate("/")}>취소</button>
				</div>
			</div>
		</form>
		<form onSubmit={event2}>
			<div className="mb-3 d-flex">
				<input 
          type="password" 
          className="form-control" 
          id="pwd" placeholder="인증번호를 입력하세요" 
          name="pwd" 
          value={code}
          onChange={e=>setCode(e.target.value)}
          />
				<button type="submit" className="w-25 btn btn-primary">인증</button>
			</div>
		</form>
	</div>
  )
}

export default Login