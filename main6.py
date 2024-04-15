import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import openai
import pyperclip
from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일에서 환경 변수를 불러옵니다.
openai.api_key = os.getenv('OPENAI_API_KEY')

# 세션 상태 변수 초기화
if 'summary' not in st.session_state:
    st.session_state['summary'] = ''
if 'english_summary' not in st.session_state:
    st.session_state['english_summary'] = ''
if 'clipboard_content' not in st.session_state:
    st.session_state['clipboard_content'] = ''

def extract_text(url):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)
    try:
        author_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.author__name > a'))
        )
        author_name = author_element.text
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.post__title > a'))
        )
        title_text = title_element.text
        content_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.tiptap.ProseMirror'))
        )
        content_text = content_element.text
    finally:
        driver.quit()
    return title_text, author_name, content_text

def summarize_text(content, author_type, author_name, title_text):
    # 제목과 본문 내용을 프롬프트에 추가합니다.
    prompt = f"제목: {title_text}\n\n{content}"

    # 저자 정보가 "다른 사람"일 경우, 저자의 이름을 프롬프트에 추가합니다.
    if author_type == "다른 사람":
        prompt += f"\n\n저자: {author_name}님이 작성한 글입니다."
    else:
        prompt += "\n\n본인이 작성한 글입니다."

    # 소셜 미디어 요약 요청을 프롬프트에 추가합니다.
    prompt += "\n\n이 글을 페이스북과 링크드인에 적합하게 요약해주세요. 요약은 캐쥬얼한 어투로, 3-5줄 내에서 작성하고, 사용된 AI툴이나 노코드툴에 대한 언급과 이모지 2개를 포함해주세요."

    # AI 모델을 통해 요약문을 생성합니다.
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    summary = response['choices'][0]['message']['content'].strip()

    # 요약문 끝에 추가적인 정보를 덧붙입니다.
    summary += f"\n\n{'본인이 작성한 글입니다.' if author_type == '본인' else f'{author_name}님이 작성한 글입니다.'}"
    
    return summary


def translate_to_english(text):
    prompt = f"Please translate the following Korean text to English:\n\n{text}"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    translated_text = response['choices'][0]['message']['content'].strip()
    return translated_text


st.title('SNS에 AI 작성글 쉽게 공유하기🌎')
st.write('공유하고 싶은 지피터스 게시글 링크를 입력하면 - 바로 SNS에 공유할 수 있는 요약문을 제공해드립니다. 페북과 링크드인에 바로 AI 게시글을 공유해보세요! 💪 ')
url = st.text_input('지피터스 게시글 url을 입력하세요:')
# 수평 라디오 버튼을 위한 CSS 스타일링
st.markdown("""
    <style>
        div.row-widget.stRadio > div {
            flex-direction: row;
        }
        label {
            display: inline-block;
            padding: 0 10px;
        }
    </style>
    """, unsafe_allow_html=True)

# URL 입력이 있는 경우에만 라디오 버튼을 활성화
disabled_state = not url  # URL이 비어있으면 True, 그렇지 않으면 False

author_type = st.radio("작성자 선택", ("본인", "다른 사람"), index=1, disabled=disabled_state)

def copy_to_clipboard(text1, text2):
    combined_text = f"{text1}\n\n{text2}"
    pyperclip.copy(combined_text)


if url and author_type and st.button("SNS 업로드용 요약문 만들기"):
    with st.spinner('요약 중입니다...'):
        title_text, author_name, content_text = extract_text(url)
        summary = summarize_text(content_text, author_type, author_name, title_text)
        english_summary = translate_to_english(summary)
    st.success('요약이 완료되었습니다! SNS용 요약문이 클립보드에 복사되었습니다. 바로 붙여넣기 하시면 됩니다.')
    st.session_state.summary = summary
    st.session_state.english_summary = english_summary
    copy_to_clipboard(summary, english_summary)  # 자동으로 클립보드에 복사
    st.markdown("#### SNS업로드용 요약 💝")
    st.markdown(st.session_state.summary)

    st.markdown("#### 영문 버전 요약 🇺🇸")
    with st.spinner('영어로 번역 중입니다...'):
        st.markdown(st.session_state.english_summary)

    # # 클립보드에 복사 버튼
    # copy_button = st.button("한글 & 영문 요약 복사하기")

    # if copy_button:
    #     combined_text = f"{st.session_state.summary}\n\n{st.session_state.english_summary}"
    #     st.markdown(f'''
    #         <script>
    #             var copyText = `{combined_text}`;
    #             navigator.clipboard.writeText(copyText).then(function() {{
    #                 console.log('Text copied to clipboard');
    #             }}, function(err) {{
    #                 console.error('Could not copy text: ', err);
    #             }});
    #         </script>
    #     ''', unsafe_allow_html=True)
    #     st.success("한글과 영문 요약이 클립보드에 복사되었습니다!")
    
    # Facebook, LinkedIn, 트위터(X) 공유 버튼은 외부 링크로 직접 리다이렉트
    fb_url = f"https://www.facebook.com/sharer/sharer.php?u={url}"
    linkedin_url = f"https://www.linkedin.com/shareArticle?mini=true&url={url}"
    twitter_url = f"https://twitter.com/intent/tweet?url={url}"

    # HTML을 사용하여 새 탭에서 링크를 열도록 설정
    facebook_link = f'<a href="{fb_url}" target="_blank">Facebook에서 공유</a>'
    linkedin_link = f'<a href="{linkedin_url}" target="_blank">LinkedIn에서 공유</a>'
    twitter_link = f'<a href="{twitter_url}" target="_blank">트위터(X)에서 공유</a>'

    st.markdown(facebook_link, unsafe_allow_html=True)
    st.markdown(linkedin_link, unsafe_allow_html=True)
    st.markdown(twitter_link, unsafe_allow_html=True)

    st.markdown("---") 
    st.markdown(f"#### 게시글 전문")
    st.markdown(f"#### {title_text}")
    st.markdown(f"##### {author_name}")
    st.markdown(content_text)
