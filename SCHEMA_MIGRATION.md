# 데이터베이스 스키마 마이그레이션 가이드

## 새로운 스키마 구조

프로젝트가 새로운 정규화된 데이터베이스 스키마로 업데이트되었습니다.

### 테이블 구조

1. **videos** - YouTube 비디오 정보
2. **users** - YouTube 사용자 정보
3. **categories** - 댓글 분류 카테고리
4. **comments** - YouTube 댓글 정보
5. **comment_analysis** - 댓글 분석 결과

## 주요 변경사항

### 1. 비디오 정보 저장
- YouTube API를 통해 비디오 제목, 채널명, 조회수, 좋아요 수 등 모든 정보를 수집
- `get_video_info()` 함수로 비디오 정보 수집

### 2. 사용자 정보 저장
- 각 댓글 작성자의 정보를 별도 테이블에 저장
- 프로필 이미지 URL 등 추가 정보 저장

### 3. 댓글 정보 확장
- YouTube 댓글 ID 저장
- 답글 수(reply_count) 저장
- 부모 댓글 ID 저장 (답글인 경우)

### 4. 분석 결과 저장
- 댓글 분석 결과를 별도 테이블에 저장
- 카테고리별 통계 조회 가능
- 신뢰도 점수 저장

## 카테고리 매핑

한글 카테고리 → 영문 카테고리:
- 정상 → normal
- 욕설 → profanity
- 혐오 → hate
- 광고/스팸 → spam
- 위험 → danger

## 데이터 저장 흐름

1. YouTube URL 입력
2. 비디오 정보 수집 (`get_video_info()`)
3. 댓글 수집 및 분석 (`get_comments()`)
4. DB 저장:
   - 비디오 정보 → `videos` 테이블
   - 사용자 정보 → `users` 테이블
   - 댓글 정보 → `comments` 테이블
   - 분석 결과 → `comment_analysis` 테이블

## 통계 조회 예시

```sql
-- 비디오별 댓글 통계
SELECT 
    v.title,
    COUNT(DISTINCT c.comment_id) as total_comments,
    COUNT(DISTINCT CASE WHEN ca.category_id = (SELECT category_id FROM categories WHERE category_name = 'profanity') THEN c.comment_id END) as profanity_count
FROM videos v
LEFT JOIN comments c ON v.video_id = c.video_id
LEFT JOIN comment_analysis ca ON c.comment_id = ca.comment_id
GROUP BY v.video_id;

-- 카테고리별 통계
SELECT 
    cat.category_name,
    COUNT(*) as count
FROM comment_analysis ca
JOIN categories cat ON ca.category_id = cat.category_id
GROUP BY cat.category_id;
```

## 기존 데이터 마이그레이션

기존 `youtube_comments` 테이블이 있다면, 다음 SQL로 마이그레이션할 수 있습니다:

```sql
-- 기존 데이터를 새 스키마로 마이그레이션 (예시)
INSERT INTO videos (video_id, title, channel_name, channel_id, published_at)
SELECT DISTINCT video_id, '', '', '', NOW()
FROM youtube_comments
ON DUPLICATE KEY UPDATE video_id = video_id;

-- 나머지 마이그레이션 로직은 데이터 구조에 맞게 작성 필요
```

