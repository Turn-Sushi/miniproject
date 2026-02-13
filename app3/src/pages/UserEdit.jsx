import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from "react-router"
import { useCookies } from "react-cookie"
import axios from "axios"

const UserEdit = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const close = () => navigate(-1)
  const [userNo, setUserNo] = useState("")
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [proNo, setProNo] = useState("")
  const [origin, setOrigin] = useState("")
  const [fileName, setFileName] = useState("")
  const [gender, setGender] = useState("")
  const [regDate, setRegDate] = useState("")
  const [modDate, setModDate] = useState("")
  const [cookies, setCookie, removeCookie] = useCookies(['userUp'])
  const [files, setFiles] = useState([])

  // URL을 변경하기 위한 선언 
  // 이녀석을 선언하면 env에 담을 수 있음 VITE_API_URL=http://localhost:8001
  // const API_URL = import.meta.env.VITE_API_URL
  
  const config ={
    headers: {
      "Content-Type": "multipart/form-data"
    }
  }

  // 등록할 프로필 선택 및 화면 출력
  const imgEvent = () => {
    const x = document.createElement("input")
    x.type = "file"
    x.accept = "image/*"

    x.addEventListener("change", function (event) {
      const file = event.target.files[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = function (e) {
          // 미리보기용 base64 저장
          setFileName(e.target.result)
          // 원본 파일명 저장
          setOrigin(file.name)
          // 파일 저장
          setFiles(Array.from(event.target.files))
        }
        
        reader.readAsDataURL(file)
      }
    })

    x.click()
  }

  // 회원 정보 수정 전 파일 업로드
  const fielUpload = async e => {
    e.preventDefault()
    console.log("프로필 등록 요청")
    const formData = new FormData();
    formData.append("userNo", userNo)
    console.log("userNo", userNo)
    files.forEach(file => formData.append("files", file))
    console.log("files", files)
    await axios.post("http://localhost:8001/uploadFile", formData, config)
    .then(res => {
      if(res.data.status) {
          console.log(res.data.status)
          // 회원정보 등록
          const newProNo = res.data.proNo
          setProNo(newProNo)
          // 회원정보 수정 시작
          submitE(newProNo)
        } else {
          alert(res.data.msg)
        }
    })
    .catch(err => console.error(err))
  }

  // 회원정보 수정
  const submitE = newProNo => {
    const params = { userNo, proNo: newProNo, name, email, gender, regDate, modDate }
    console.log(params)

    const userUp = {
      userNo: userNo,
      proNo: newProNo,
      name: name,
      email: email,
      gender: gender,
      regDate: regDate
    }
    // 쿠키 저장
    setCookie("userUp", window.btoa(encodeURI(JSON.stringify(userUp))))
    // 서버에 저장 요청
    axios.post("http://localhost:8001/userUpdate",{}, { withCredentials: true } )
      .then(res => alert(res.data.msg))
      .catch(err => console.error(err));

    navigate("/userview", {state:params})
  }

  useEffect(()=>{
    const data = location.state
    if (data === null) return close()
      setResult(data)
  }, [])

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
    <div className="container mt-3">
      <h1 className="display-1 text-center">회원정보 수정</h1>
      <div className="d-flex justify-content-center">
        {files.length > 0 ? (
          // 새로 선택한 이미지 (base64 미리보기)
          <img
            className="d-block rounded-circle img-thumbnail mt-3 border user_pt"
            src={fileName}
            alt={origin}
            id="preview"
            onClick={imgEvent}
          />
        ) : fileName ? (
          // 서버에 저장된 이미지
          <img
            className="d-block rounded-circle img-thumbnail mt-3 border user_pt"
            src={`http://localhost:8001/uploads/${fileName}`}
            alt={origin}
            id="preview"
            onClick={imgEvent}
          />
          // 이부분은 URL를 변수처리하는 방법
          // <img src={`${API_URL}/uploads/${fileName}`} />
        ) : (
          // 기본 이미지
          <img
            className="d-block rounded-circle img-thumbnail mt-3 border user_pt"
            src="/img01.jpg"
            alt="default"
            id="preview"
            onClick={imgEvent}
          />
        )}
      </div>
      <form onSubmit={fielUpload}>
        <div className="mb-3 mt-3">
          <label htmlFor="name" className="form-label">이름</label>
          <input type="text" className="form-control" id="name" placeholder="이름을 입력하세요." name="name"
              value={name} onChange={e=>setName(e.target.value)}  autoComplete='off' required={true} />
        </div>
        <div className="mb-3 mt-3">
          <label htmlFor="email" className="form-label">이메일</label>
          <input type="email" className="form-control" id="email" placeholder="이메일를 입력하세요." name="email"
              value={email} onChange={e=>setEmail(e.target.value)}  autoComplete='off' required={true} />
        </div>
        <div className="mb-3 mt-3">
          <label htmlFor="regDate" className="form-label">가입일</label>
          <input type="text" className="form-control" id="regDate" placeholder="YYYY-MM-DD" name="regDate" 
              disabled readOnly="readonly" defaultValue={regDate}/>
        </div>
        <div className="d-flex">
          <div className="p-2 flex-fill">
            <div className="form-check">
              <input type="radio" className="form-check-input" id="radio1" name="gender" value="1" 
                  checked={gender} onChange={()=>setGender(true)} />남성
              <label className="form-check-label" htmlFor="radio1"></label>
            </div>
          </div>
          <div className="p-2 flex-fill">
            <div className="form-check">
              <input type="radio" className="form-check-input" id="radio2" name="gender" value="2" 
                  checked={!gender} onChange={()=>setGender(false)} />여성
              <label className="form-check-label" htmlFor="radio2"></label>
            </div>
          </div>
        </div>
        <div className="d-flex">
          <div className="p-2 flex-fill d-grid">
            <button type="submit" className="btn btn-primary">저장</button>
          </div>
          <div className="p-2 flex-fill d-grid">
            <button type="button" className="btn btn-primary" onClick={close}>취소</button>
          </div>
        </div>
      </form>
    </div>
  )
}
export default UserEdit