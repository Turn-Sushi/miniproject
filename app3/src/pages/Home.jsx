import { useEffect, useState } from "react"
import { useNavigate } from "react-router"
import { api } from "@utils/network" 

const Home = () => {
  const navigate = useNavigate()
  const [boards, setBoards] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get("/board")
      .then(res => {
        if (res.data.status) {
          setBoards(res.data.data)
        } else {
          alert("게시글을 불러오지 못했습니다")
        }
      })
      .catch(err => {
        console.error(err)
        alert("서버 오류")
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="text-center mt-5">로딩 중...</div>
  }

  return (
    <div className="container mt-4">
      <h1 className="display-5 text-center mb-4">게시판</h1>

      <table className="table table-hover">
        <thead className="table-light">
          <tr>
            <th style={{ width: "10%" }}>번호</th>
            <th>제목</th>
            <th style={{ width: "20%" }}>작성일</th>
          </tr>
        </thead>
        <tbody>
          {boards.length === 0 && (
            <tr>
              <td colSpan="3" className="text-center">
                게시글이 없습니다
              </td>
            </tr>
          )}

          {boards.map(board => (
            <tr
              key={board.board_no}
              style={{ cursor: "pointer" }}
              onClick={() =>
                navigate("/board_view", {
                  state: { no: board.board_no }
                })
              }
            >
              <td>{board.board_no}</td>
              <td>{board.title}</td>
              <td>{board.regDate}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default Home