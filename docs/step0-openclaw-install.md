# Step 0. OpenClaw 설치 및 초기 설정

## 개요
Azure Linux VM에 SSH 접속한 상태에서 OpenClaw를 설치하고 Telegram과 연결합니다.

> **전제 조건**: Ubuntu 24.04 LTS VM에 SSH 접속 완료

---

## 0-1. 환경 확인

```bash
# OS 확인
lsb_release -a

# Node.js 확인 (없으면 아래에서 설치)
node --version

# Python 확인
python3 --version
```

---

## 0-2. Node.js 설치 (없는 경우)

OpenClaw는 Node.js 기반입니다.

```bash
# Node.js 22.x LTS 설치
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# 설치 확인
node --version   # v22.x.x
npm --version
```

---

## 0-3. OpenClaw 설치

```bash
# npm global 경로 설정 (sudo 없이 설치하기 위해)
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# OpenClaw 설치
npm i -g openclaw

# 설치 확인
openclaw --version
# 출력 예: OpenClaw 2026.4.10 (44e5b62)
```

> 💡 **팁**: `which openclaw` 로 실행 경로를 반드시 확인해두세요.
> 나중에 cron 등록 시 이 경로가 필요합니다.
> 일반적으로 `/home/USERNAME/.npm-global/bin/openclaw` 입니다.

```bash
# 경로 기록해두기
which openclaw
```

---

## 0-4. Telegram 봇 생성

OpenClaw와 연결할 Telegram 봇을 먼저 만들어야 합니다.

1. Telegram에서 **@BotFather** 검색
2. `/newbot` 명령 입력
3. 봇 이름 입력 (예: `My Investment Bot`)
4. 봇 username 입력 (예: `my_investment_bot`) — `_bot`으로 끝나야 함
5. BotFather가 **Bot Token** 발급 → 복사해두기

```
예시 토큰 형식: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

> ⚠️ **주의**: 토큰은 외부에 절대 공개하지 마세요.

---

## 0-5. OpenClaw 초기 설정 (onboarding)

```bash
openclaw onboard
```

대화형 설정이 시작됩니다. 아래 항목을 순서대로 입력합니다:

1. **에이전트 이름** 설정 (예: `Claw`)
2. **AI 모델 선택**:
   - Anthropic Claude API 키 보유 → Anthropic 선택
   - Azure OpenAI 보유 → Microsoft Foundry 선택
   - GitHub Copilot 구독 → GitHub Copilot 선택
3. **Telegram 연결**:
   - Bot Token 입력 (0-4에서 받은 토큰)
4. **워크스페이스** 경로 설정 (기본값 사용 권장)

---

## 0-6. OpenClaw 서비스 실행 확인

```bash
# gateway 프로세스 실행 중인지 확인
ps aux | grep openclaw-gateway | grep -v grep

# 정상 출력 예:
# USERNAME  12345  0.5 12.1 22649992 481604 ?  Ssl  09:00  openclaw-gateway
```

실행 중이 아니면:
```bash
openclaw gateway --background
```

---

## 0-7. 전체 상태 확인

```bash
openclaw status
```

아래 항목이 모두 정상인지 확인:

```
Gateway     │ local · reachable
Telegram    │ ON · OK
```

> ⚠️ **Telegram이 OFF인 경우**:
> ```bash
> openclaw channels list          # 채널 설정 확인
> openclaw configure              # 재설정
> ```

---

## 0-8. Telegram Chat ID 확인

나중에 브리핑 전송에 필요한 본인의 Telegram Chat ID를 확인합니다.

**방법**: Telegram에서 본인의 OpenClaw 봇에게 아무 메시지나 전송한 뒤:

```bash
cat ~/.openclaw/agents/main/sessions/sessions.json \
  | python3 -m json.tool \
  | grep "telegram:direct"
```

출력 예:
```
"agent:main:telegram:direct:7733177955"
```

→ Chat ID = `7733177955` (본인 숫자로 기록해두기)

---

## 0-9. 스킬 목록 확인

```bash
openclaw skills list
```

`✓ ready` 상태의 스킬들이 보이면 설치 완료입니다.

---

✅ Step 0 완료 → [Step 1으로 이동](./step1-project-setup.md)
