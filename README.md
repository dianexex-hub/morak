# 가상온천 모락 (온라인판)

서버 없이 브라우저끼리 직접 연결되는(P2P) 메타버스 온천입니다.
같은 주소로 들어온 사람들이 한 "탕방"에 모입니다(방당 최대 12명, 넘치면 다음 방으로 자동 이동).

## 파일
- `index.html` — 온천 본체
- `trystero.mjs` — P2P 연결 라이브러리 (Trystero, MIT 라이선스)
- `.nojekyll` — GitHub Pages가 파일을 그대로 올리게 하는 빈 파일

## GitHub Pages로 무료 배포하기
1. GitHub에 로그인 → 오른쪽 위 `+` → **New repository**
2. 이름 예: `morak`, **Public** 선택 → Create repository
3. 새 저장소 화면에서 **uploading an existing file** 클릭 → 이 폴더의 파일 3개를 끌어다 놓기 → **Commit changes**
4. 저장소 **Settings → Pages** → Source: **Deploy from a branch**, Branch: `main` / `(root)` → Save
5. 1~2분 뒤 `https://<내아이디>.github.io/morak/` 주소가 생깁니다. 이 링크를 공유하면 끝.

## 테스트
- 한 컴퓨터에서 시험: 일반 창 하나 + 시크릿 창 하나로 같은 주소를 열기
- 네트워크 없이 같은 브라우저 탭끼리 시험: 주소 끝에 `?local` 붙이기

## 알아둘 점
- 비용: 0원. 호스팅은 GitHub Pages, 연결 중개는 공개 Nostr 릴레이를 씁니다. 실제 데이터(위치·좋다~!)는 브라우저끼리 직접 오가요.
- 회사·학교 망처럼 방화벽이 강한 곳에서는 일부 사람끼리 연결이 안 될 수 있어요(TURN 서버 없음).
- 저장되는 건 없어요. 지금 접속한 사람만 보입니다.
