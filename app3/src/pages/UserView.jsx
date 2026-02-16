import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from "react-router"
import { useCookies } from "react-cookie"
import axios from "axios"

const UserView = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const close = () => navigate("/")
  const [userNo, setUserNo] = useState("")
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [proNo, setProNo] = useState("")
  const [origin, setOrigin] = useState("")
  const [fileName, setFileName] = useState("")
  const [gender, setGender] = useState("")
  const [regDate, setRegDate] = useState("")
  const [modDate, setModDate] = useState("")
  const [cookies, setCookie, removeCookie] = useCookies(['userInfo'])

  // URL을 변경하기 위한 선언  
  const API_URL = import.meta.env.VITE_APP_FASTAPI_URL

  // 이미지 불러올때 미리 선언 해줌
  // 1. 서버에 저장된 이미지
  // 2. 기본 이미지
  const imageSrc = fileName ? `${API_URL}/uploads/${fileName}` : "/images/img01.jpg"

  const resignation = () => {
    const userDelYn = true
    console.log(userNo, userDelYn)

    const userInfo = {
      userNo: userNo,
      delYn: userDelYn,
    }
    // 쿠키 저장
    setCookie("userInfo", window.btoa(encodeURI(JSON.stringify(userInfo))))

    // 서버에 저장 요청
    axios.post(`${API_URL}/userDelYn`, {}, { withCredentials: true })
      .then(res => alert(res.data.msg))
      .catch(err => console.error(err));
  }

  const submitE = e => {
    e.preventDefault()
    const params = { userNo, name, email, gender, regDate, modDate, proNo, origin, fileName }
    console.log(params)
    navigate("/userEdit", { state: params })
  }

  // 더미코드이므로 화면 연결시 해당 코드는 삭제 또는 주석 처리 부탁드립니다.
  useEffect(()=>{
    const selectUser = {
      email: "admin@gmail.com",
      user_no: 1,
    }
    // 쿠키 저장
    setCookie("selectUser", window.btoa(encodeURI(JSON.stringify(selectUser))))

    axios.post(`${API_URL}/selUser`,{}, { withCredentials: true } )
    .then(res => {
      if (res.data.status) {
        console.log(res.data.status)
        setResult(res.data.status)
      } else {
        alert(res.data.msg)
      }
    })
    .catch(err => console.error(err))
    .finally(() => console.log("완료"));
  }, [])

  // 더미 코드 삭제 또는 주석 처리시, 해당 코드 주석을 풀고 사용 필수~
  // 단, 여기서 email과 user_no 값이 필요
  // useEffect(() => {
  //   const data = location.state
  //   console.log(location.state)
  //   console.log(data.user)
  //   if (data === null) close()
  //   else {
  //     const selectUser = {
  //       email: data.email,
  //       user_no: data.user,
  //     }
  //     // 쿠키 저장
  //     setCookie("selectUser", window.btoa(encodeURI(JSON.stringify(selectUser))))

  //     axios.post(`${API_URL}/selUser`, {}, { withCredentials: true })
  //       .then(res => {
  //         if (res.data.status) {
  
  //           console.log(res.data.status)
  //           setResult(res.data.status)
  //         } else {
  //           alert(res.data.msg)
  //         }
  //       })
  //       .catch(err => console.error(err))
  //       .finally(() => console.log("완료"));
  //   }
  // }, [])

 const setResult = data => {
    setUserNo(data.userNo)
    setName(data.name)
    setEmail(data.email)
    setGender(data.gender)
    setProNo(data.proNo)
    setOrigin(data.origin)
    setFileName(data.fileName)
    setRegDate(data.regDate)
    setModDate(data.modDate)
  }

  return (
    <div className="container mt-3 position-relative">
      <h1 className="display-1 text-center">회원정보</h1>
      <div>
        {/* onError는 uploads에 관련 이미지가 없을경우 예외처리해주는 부분 */}
        {/* 예외처리는 기본 이미지 불러오기 */}
        <img
          className="border user_pt"
          src={imageSrc}
          alt={origin || "default"}
          id="preview"
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = "/images/img01.jpg";
          }}
        />
      </div>

      <form onSubmit={submitE}>
        <div>
          <div className="mb-3 mt-3">
            <label htmlFor="name" className="form-label">이름</label>
            <input type="text" className="form-control" id="name" name="name"
              readOnly="readonly" defaultValue={name} />
          </div>
          <div className="mb-3 mt-3">
            <label htmlFor="email" className="form-label">이메일</label>
            <input type="email" className="form-control" id="email" name="email"
              readOnly="readonly" defaultValue={email} />
          </div>
          <div className="mb-3 mt-3">
            <label htmlFor="regDate" className="form-label">가입일</label>
            <input type="text" className="form-control" id="regDate" name="regDate"
              readOnly="readonly" defaultValue={regDate} />
          </div>
          <div className="mb-3 mt-3">
            <label htmlFor="modDate" className="form-label">회원정보 수정일</label>
            <input type="text" className="form-control" id="modDate" name="modDate"
              readOnly="readonly" defaultValue={modDate} />
          </div>

          <div className="d-flex">
            <div className="p-2 flex-fill">
              <div className="form-check">
                <input type="radio" className="form-check-input" id="radio1" name="gender" value="1"
                  checked={gender} disabled readOnly="readonly" />남성
                <label className="form-check-label" htmlFor="radio1"></label>
              </div>
            </div>
            <div className="p-2 flex-fill">
              <div className="form-check">
                <input type="radio" className="form-check-input" id="radio2" name="gender" value="2"
                  checked={!gender} disabled readOnly="readonly" />여성
                <label className="form-check-label" htmlFor="radio2"></label>
              </div>
            </div>
          </div>
        </div>
        <div className="d-flex">
          <div className="p-2 flex-fill d-grid">
            <button type="button" className="btn btn-primary" onClick={close}>취소</button>
          </div>
          <div className="p-2 flex-fill d-grid">
            <button type="submit" className="btn btn-primary">수정</button>
          </div>
          <div className="p-2 flex-fill d-grid">
            <button type="button" className="btn btn-primary" onClick={resignation}>탈퇴</button>
          </div>
        </div>
      </form>
    </div>
  )
}

export default UserView