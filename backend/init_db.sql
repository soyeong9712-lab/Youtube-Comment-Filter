-- ==============================
-- YouTube 댓글 필터링 DB 초기화 스크립트 (새 스키마)
-- ==============================

-- 1. VIDEOS 테이블: YouTube 비디오 정보
CREATE TABLE IF NOT EXISTS videos (
    video_id VARCHAR(20) PRIMARY KEY COMMENT 'YouTube 비디오 ID',
    title VARCHAR(500) NOT NULL COMMENT '비디오 제목',
    channel_name VARCHAR(200) NOT NULL COMMENT '채널명',
    channel_id VARCHAR(50) NOT NULL COMMENT '채널 ID',
    view_count INT DEFAULT 0 COMMENT '조회수',
    like_count INT DEFAULT 0 COMMENT '좋아요 수',
    comment_count INT DEFAULT 0 COMMENT '댓글 수',
    published_at DATETIME NOT NULL COMMENT '게시일시',
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '수집일시',
    description TEXT COMMENT '비디오 설명',
    thumbnail_url VARCHAR(500) COMMENT '썸네일 URL',
    INDEX idx_channel_id (channel_id),
    INDEX idx_published_at (published_at),
    INDEX idx_collected_at (collected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='YouTube 비디오 정보';

-- 2. USERS 테이블: YouTube 사용자 정보
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY COMMENT 'YouTube 사용자 ID',
    username VARCHAR(200) NOT NULL COMMENT '사용자명',
    profile_image_url VARCHAR(500) COMMENT '프로필 이미지 URL',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='YouTube 사용자 정보';

-- 3. CATEGORIES 테이블: 댓글 분류 카테고리
CREATE TABLE IF NOT EXISTS categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '카테고리 ID',
    category_name VARCHAR(50) UNIQUE NOT NULL COMMENT '카테고리명',
    description VARCHAR(200) COMMENT '카테고리 설명',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='댓글 분류 카테고리';

-- 4. COMMENTS 테이블: YouTube 댓글 정보
CREATE TABLE IF NOT EXISTS comments (
    comment_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '댓글 ID',
    youtube_comment_id VARCHAR(100) UNIQUE NOT NULL COMMENT 'YouTube 댓글 ID',
    video_id VARCHAR(20) NOT NULL COMMENT '비디오 ID',
    user_id VARCHAR(50) NOT NULL COMMENT '사용자 ID',
    comment_text TEXT NOT NULL COMMENT '댓글 내용',
    like_count INT DEFAULT 0 COMMENT '좋아요 수',
    reply_count INT DEFAULT 0 COMMENT '답글 수',
    parent_comment_id VARCHAR(100) COMMENT '부모 댓글 ID (답글인 경우)',
    published_at DATETIME NOT NULL COMMENT '작성일시',
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '수집일시',
    is_reply BOOLEAN DEFAULT FALSE COMMENT '답글 여부',
    INDEX idx_video_id (video_id),
    INDEX idx_user_id (user_id),
    INDEX idx_published_at (published_at),
    INDEX idx_parent_comment (parent_comment_id),
    INDEX idx_is_reply (is_reply),
    FULLTEXT INDEX idx_comment_text (comment_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='YouTube 댓글 정보';

-- 5. COMMENT_ANALYSIS 테이블: 댓글 분석 결과
CREATE TABLE IF NOT EXISTS comment_analysis (
    analysis_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '분석 ID',
    comment_id BIGINT NOT NULL COMMENT '댓글 ID',
    category_id INT NOT NULL COMMENT '카테고리 ID',
    confidence_score FLOAT NOT NULL COMMENT '신뢰도 점수 (0-1)',
    analysis_result TEXT COMMENT '분석 결과 상세',
    model_version VARCHAR(50) COMMENT '사용된 모델 버전',
    analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '분석일시',
    INDEX idx_comment_id (comment_id),
    INDEX idx_category_id (category_id),
    INDEX idx_confidence_score (confidence_score),
    INDEX idx_analyzed_at (analyzed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='댓글 분석 결과';

-- 외래키 제약조건 추가
ALTER TABLE comments 
ADD CONSTRAINT fk_comments_video 
FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE;

ALTER TABLE comments 
ADD CONSTRAINT fk_comments_user 
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE comment_analysis 
ADD CONSTRAINT fk_analysis_comment 
FOREIGN KEY (comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE;

ALTER TABLE comment_analysis 
ADD CONSTRAINT fk_analysis_category 
FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE;

-- 초기 카테고리 데이터 삽입
INSERT IGNORE INTO categories (category_name, description) VALUES
('normal', '정상 댓글'),
('profanity', '욕설 댓글'),
('spam', '스팸 댓글'),
('hate', '혐오 댓글'),
('danger', '위험 댓글');
