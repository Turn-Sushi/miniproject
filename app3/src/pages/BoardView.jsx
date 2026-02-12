import { useLocation, useNavigate } from "react-router"
import { useEffect, useState } from "react"
import { api } from "@utils/network"

const Board_view = () => {
    const navigate = useNavigate()
    const { state } = useLocation()
    const loginUser = JSON.parse(localStorage.getItem("user"))
    const [board, setBoard] = useState({
        title: "",
        name: "",
        cont: "",
        regDate: "",
        no: null
    })

    const [comments, setComments] = useState([])
    const [commentText, setCommentText] = useState("")
    const [editingId, setEditingId] = useState(null)
    const [editText, setEditText] = useState("")

    const onsubmit = e => e.preventDefault()

    /* ---------------- 게시글 수정 이동 ---------------- */
    const goEdit = (boardId) => {
        Cookies.set("boardNo", btoa(JSON.stringify({ no: boardId })))
        navigate("/board_edit")
    }

    /* ---------------- 게시글 삭제 ---------------- */
    const delet = () => {
        api.delete(`/board/${board.board_no}`, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem("access_token")}`
            }
        })
            .then(res => {
                if (res.data.success) {
                    alert("삭제 완료")
                    navigate("/")
                } else {
                    alert("삭제 실패")
                }
            })
    }

    /* ---------------- 게시글 로드 ---------------- */
    const loadBoard = () => {
        api.get(`/board/${state.no}`)
            .then(res => {
                if (res.data.status) {setBoard(res.data.data)}
            })
    }
    /* ---------------- 댓글 로드 ---------------- */
    const loadComments = () => {
        api.get(`/comment?board_no=${state.no}`)
            .then(res => {
                if (res.data.status) {
                    setComments(res.data.data)
                }
            })
    }
    useEffect(() => {
        if (!state?.no) {
            alert("잘못된 접근입니다")
            navigate("/")
            return
        }
        loadBoard()
        loadComments()
    }, [])

    /* ---------------- 댓글 작성 ---------------- */
    const submitComment = () => {
        if (!commentText.trim()) {
            alert("댓글을 입력하세요")
            return
        }
        api.post("/comment", {
            board_no: state.no,
            cnt: commentText
        }, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem("access_token")}`
            }
        }).then(() => {
            setCommentText("")
            loadComments()
        })
    }

    /* ---------------- 댓글 삭제 ---------------- */
    const deleteComment = (id) => {
        if (!window.confirm("삭제하시겠습니까?")) return
        api.delete(`/comment/${id}`, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem("access_token")}`
            }
        }).then(() => loadComments())
    }

    /* ---------------- 댓글 수정 ---------------- */
    const startEdit = (comment) => {
        setEditingId(comment.cnt_no)
        setEditText(comment.cnt)
    }

    const submitEdit = (id) => {
        api.put(`/comment/${id}`, {cnt: editText}, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem("access_token")}`
            }
        }).then(() => {
            setEditingId(null)
            loadComments()
        })
    }

    return (
        <div className="container mt-3">
            <h1 className="display-1 text-center">게시글 상세</h1>

            <form onSubmit={onsubmit}>
                <div className="mb-3 mt-3">
                    <label className="form-label">제목</label>
                    <input type="text" className="form-control" value={board.title} readOnly />
                </div>

                <div className="mb-3 mt-3">
                    <label className="form-label">작성자</label>
                    <input type="text" className="form-control" value={board.name} readOnly />
                </div>

                <div className="mb-3 mt-3">
                    <label className="form-label">작성날짜</label>
                    <input type="text" className="form-control" value={board.regDate} readOnly />
                </div>

                <div className="mb-3 mt-3">
                    <label className="form-label">내용</label>
                    <textarea className="form-control h-50" rows="10" value={board.cnt} readOnly />
                </div>
            </form>

            <div className="d-flex">
                <div className="p-2 flex-fill d-grid">
                    <button type="button" onClick={() => goEdit(board.board_no)} className="btn btn-primary">수정</button>
                </div>
                <div className="p-2 flex-fill d-grid">
                    <button onClick={delet} className="btn btn-primary">삭제</button>
                </div>
                <div className="p-2 flex-fill d-grid">
                    <button onClick={() => navigate(-1)} className="btn btn-primary">취소</button>
                </div>
            </div>

            {/* ================= 댓글 작성 ================= */}
            <div className="comment-box mb-4 mt-5">
                <div className="d-flex">
                    <div className="flex-grow-1 mt-3 position-relative">
                        <input type="text" className="form-control comment-input" maxLength="3000" placeholder="댓글을 입력하세요" 
                        value={commentText} onChange={(e) => setCommentText(e.target.value)} />
                    </div>
                    <button className="btn btn-success btn-sm mx-2 mt-3" onClick={submitComment}>등록</button>
                </div>
            </div>
            {/* ================= 댓글 목록 ================= */}
            <div>
                {comments.map(comment => (
                    comment.delYn === 1 ? (<div key={comment.cnt_no} className="comments my-3 w-100 pb-2 text-muted">삭제된 댓글입니다.</div>
                    ) : (
                    <div key={comment.cnt_no} className="comments my-3 w-100 pb-2">
                        <div className="d-flex align-items-start">
                        <img src="/img01.jpg" className="rounded-circle me-3" width="50" height="50" alt="profile"/>
                        <div className="flex-grow-1">
                            <div className="d-flex justify-content-between align-items-center">
                            <div className="fw-bold">{comment.name}</div>
                            {loginUser?.user_id == comment.user_no && (
                                <div>
                                    <button className="btn btn-outline-secondary btn-sm me-1" onClick={() => startEdit(comment)}>수정</button>
                                    <button className="btn btn-outline-danger btn-sm" onClick={() => deleteComment(comment.cnt_no)}>삭제</button>
                                </div>
                            )}
                            </div>
                            {editingId === comment.cnt_no ? (
                                <div className="mt-2 d-flex">
                                <input className="form-control me-2" value={editText} 
                                onChange={(e) => setEditText(e.target.value)}/>
                                <button className="btn btn-success btn-sm" onClick={() => submitEdit(comment.cnt_no)}>저장</button>
                            </div>
                            ) : (
                            <>
                                <div className="mt-1">{comment.cnt}</div>
                                <div className="text-muted small my-1">
                                {comment.regDate}
                                </div>
                            </>
                            )}
                        </div>
                        </div>
                    </div>
                    )
                ))}
            </div>
        </div>
    )
}

export default Board_view
