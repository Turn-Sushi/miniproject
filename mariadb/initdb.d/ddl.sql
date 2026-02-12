USE mini;

CREATE TABLE `mini`.`user_pr`(
	`pro_no`	INT(11)				NOT NULL	COMMENT '프로파일 번호'				AUTO_INCREMENT PRIMARY KEY,
	`user_no`	INT(11)				NOT NULL	COMMENT '회원 번호',
	`origin`	VARCHAR(100)		NOT NULL	COMMENT '저장 전 원본 파일이름',
	`ext`		VARCHAR(3)			NOT NULL	COMMENT '확장명ex).png, jpg, jpeg, bmp', 
	`fileName`	VARCHAR(100)		NOT NULL	COMMENT 'DB 저장시 변경된 이름',
	`cntType`	VARCHAR(20)			NOT NULL	COMMENT '파일 형식 ex) 이미지파일, 영상파일, exe파일등',
	`regDate`	DATETIME			NOT NULL	COMMENT '프로필 등록일자'				DEFAULT CURRENT_TIMESTAMP,
	`modDate`	DATETIME			NOT NULL	COMMENT '프로필 수정일자'				DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE `mini`.`user`(
	`user_no`	INT(11)				NOT NULL	COMMENT '회원 번호'					AUTO_INCREMENT PRIMARY KEY,
	`pro_no`	INT(11)				NULL	COMMENT '프로필 번호',
	`name`		VARCHAR(30)			NOT NULL	COMMENT '이름',
	`email`		VARCHAR(150)		NOT NULL	COMMENT '이메일',
	`gender`	BOOLEAN				NULL		COMMENT '성별(0:여자, 1:남자)',
	`delYn`		TINYINT(1)			NOT NULL	COMMENT '탈퇴여부(0:회원, 1: 탈퇴)'	DEFAULT FALSE,
	`regDate`	DATETIME			NOT NULL	COMMENT '회원등록일자'				DEFAULT CURRENT_TIMESTAMP,
	`modDate`	DATETIME			NOT NULL	COMMENT '회원정보수정일자'				DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT fk_userPr_user		FOREIGN KEY (pro_no) REFERENCES mini.user_pr(pro_no)
);

CREATE TABLE `mini`.`board`(
	`board_no`	INT(11)				NOT NULL	COMMENT '번호'						AUTO_INCREMENT PRIMARY KEY,
	`user_no`	INT(11)				NOT NULL	COMMENT '작성자(회원) 번호',
	`title`		VARCHAR(40)			NOT NULL	COMMENT '제목',
	`cnt`		VARCHAR(3000)		NULL		COMMENT '내용',
	`delYn`		TINYINT(1)			NOT NULL	COMMENT '삭제여부(0: 미삭제, 1: 삭제)'	DEFAULT FALSE,
	`regDate`	DATETIME			NOT NULL	COMMENT '게시글 등록일자'				DEFAULT CURRENT_TIMESTAMP,
	`modDate`	DATETIME			NOT NULL	COMMENT '게시글 수정일자'				DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT fk_user_board		FOREIGN KEY (user_no) REFERENCES `mini`.`user`(user_no)
);

CREATE TABLE `mini`.`board_cnt`(
	`cnt_no`	INT(11)				NOT NULL	COMMENT '댓글 번호'					AUTO_INCREMENT PRIMARY KEY,
	`board_no`	INT(11)				NOT NULL	COMMENT '게시판 번호',
	`user_no`	INT(11)				NOT NULL	COMMENT '작성자(회원) 번호',
	`cnt`		VARCHAR(1000)		NOT NULL	COMMENT '댓글 내용',
	`delYn`		TINYINT(1)			NOT NULL	COMMENT '삭제여부(0: 미삭제, 1: 삭제)'	DEFAULT FALSE,
	`regDate`	DATETIME			NOT NULL	COMMENT '댓글 등록일자'				DEFAULT CURRENT_TIMESTAMP,
	`modDate`	DATETIME			NOT NULL	COMMENT '댓글 수정일자'				DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT fk_board_boardCnt	FOREIGN KEY (board_no) REFERENCES `mini`.`board`(board_no),
	CONSTRAINT fk_user_boardCnt		FOREIGN KEY (user_no) REFERENCES `mini`.`user`(user_no)
);

CREATE TABLE `mini`.`login`(
	`user_no` 	INT(11)				NOT NULL COMMENT '회원 번호',
	`regDate` 	DATETIME			NOT NULL COMMENT '로그인일자'	DEFAULT CURRENT_TIMESTAMP
);

COMMIT;

USE mini;

INSERT into mini.`user_pr` (`user_no`, `origin`, `ext`, `fileName`, `cntType`) VALUE ('1','img01.jpg','jpg','img01.jpg','이미지');
INSERT into mini.`user` (`pro_no`, `name`, `email`, `gender`) VALUE ('1', '관리자', 'admin@gmail.com', '1');

INSERT into mini.`board` (`user_no`, `title`, `cnt`) VALUE ('1', '샘플을 만들었어요', '샘플을 만들었어요 만들었다구요 왜 안믿어요?');
INSERT into mini.`board` (`user_no`, `title`, `cnt`) VALUE ('1', '가영이는 귀염둥이에용 헤헷콩-!', '가영이는 귀염둥이에용 헤헷콩-!\n가영이는 귀염둥이에용 헤헷콩-!');
INSERT into mini.`board` (`user_no`, `title`, `cnt`) VALUE ('1', '샘플을 만들었어요', '샘플을 만들었어요');
INSERT into mini.`board` (`user_no`, `title`, `cnt`) VALUE ('1', '응애', '응애 응애 응애');
INSERT into mini.`board` (`user_no`, `title`, `cnt`) VALUE ('1', '누군가 자네는?', '누군가 자네는?\n이게 된다는 것인가?');

INSERT into mini.`board_cnt` (`board_no`, `user_no`, `cnt`) VALUE ('2', '1', '샘플을 만들었어요');
INSERT into mini.`board_cnt` (`board_no`, `user_no`, `cnt`) VALUE ('2', '1', '가영이는 귀염둥이에용 헤헷콩-!');
INSERT into mini.`board_cnt` (`board_no`, `user_no`, `cnt`) VALUE ('3', '1', '응애응애응애응애');
INSERT into mini.`board_cnt` (`board_no`, `user_no`, `cnt`) VALUE ('1', '1', '샘플을 만들었어요');
INSERT into mini.`board_cnt` (`board_no`, `user_no`, `cnt`) VALUE ('4', '1', '누군가 자네는?');
INSERT into mini.`board_cnt` (`board_no`, `user_no`, `cnt`) VALUE ('5', '1', '누군가 자네는?\n이게 된다는 것인가?');

COMMIT;
