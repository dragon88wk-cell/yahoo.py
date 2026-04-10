import os
import asyncio
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import telegram

# 1. 깃허브 금고에서 암호 불러오기 (기존과 동일)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_yahoo_finance_headlines():
    print("🔍 야후 파이낸스에서 최신 영문 기사 제목 수집 중...")
    url = "https://finance.yahoo.com/"
    
    # 야후는 보안이 꽤 까다롭습니다. 사람이 진짜 브라우저로 접속한 것처럼 속이는 강력한 헤더를 씁니다.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    # 야후 파이낸스의 주요 기사 제목은 보통 <h3> 태그에 담겨 있습니다.
    headlines = []
    for h3 in soup.find_all('h3'):
        title = h3.text.strip()
        # 너무 짧은 단어나 중복된 제목을 걸러내어 알짜배기만 담습니다.
        if title and len(title) > 15 and title not in headlines:
            headlines.append(title)
        if len(headlines) == 10:
            break

    if not headlines:
        return ["데이터를 불러오지 못했습니다. 야후의 크롤링 차단이 원인일 수 있습니다."]

    return headlines

async def send_telegram_msg(text):
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID, 
        text=text, 
        read_timeout=30, write_timeout=30, connect_timeout=30
    )

async def main():
    # 2. 영문 기사 제목 10개 수집
    headlines_list = get_yahoo_finance_headlines()
    context = "\n".join([f"- {h}" for h in headlines_list])

    # 3. 제미나이에게 번역 및 분석 지시 (글로벌 맞춤형)
    prompt = f"""
    당신은 베테랑 국제 경제 기자의 데스크 보고를 돕는 수석 번역 및 분석 어시스턴트입니다. 
    다음은 오늘자 야후 파이낸스(Yahoo Finance) 메인 화면의 주요 영문 기사 제목 10개입니다:

    {context}

    위 내용을 바탕으로 다음 형식의 글로벌 증시 브리핑을 작성하세요.

    1. [글로벌 마켓 무드]: 10개의 제목을 종합적으로 분석하여, 오늘 미 증시와 글로벌 경제를 관통하는 가장 중요한 이슈나 시장의 분위기를 3줄로 브리핑하세요.
    2. [주요 헤드라인 번역]: 10개의 영문 제목을 자연스럽고 전문적인 경제 기사 한국어 제목으로 번역하세요. (원문은 적지 말고 번역된 한국어만 리스트로 1번부터 10번까지 나열하세요)

    [중요 작성 규칙]
    - 응답 내용에 `**`, `*`, `_`, `#` 같은 마크다운(Markdown) 서식 기호는 절대로, 단 하나도 사용하지 마세요. (시스템 에러가 발생합니다)
    - 강조가 필요한 부분은 【 】 괄호나 🌎, 📰, 💡, 📈 같은 이모지를 활용하여 텍스트로만 깔끔하게 작성하세요.
    """

    print("🧠 제미나이가 영문 기사 번역 및 글로벌 시황 분석을 수행 중입니다...")
    response = model.generate_content(prompt)
    result_text = response.text

    # 4. 텔레그램 전송
    final_message = f"🌎 【야후 파이낸스 글로벌 모닝 브리핑】\n\n{result_text}"
    await send_telegram_msg(final_message)
    print("✅ 텔레그램 전송이 완료되었습니다!")

if __name__ == "__main__":
    asyncio.run(main())
