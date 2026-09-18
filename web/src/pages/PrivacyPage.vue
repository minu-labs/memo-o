<template>
  <article class="section">
    <div class="wrap narrow prose">
      <h1>개인정보처리방침</h1>
      <p class="muted">시행일: {{ EFFECTIVE_DATE }}</p>

      <p>
        minulog(이하 "운영자")는 MemoO 다운로드 페이지(이하 "사이트")와 MemoO 프로그램(이하 "프로그램")을 운영하며,
        「개인정보 보호법」 등 관련 법령을 준수합니다. 본 방침은 사이트와 프로그램에서 개인정보가 어떻게 처리되는지 안내합니다.
      </p>

      <h2>1. 프로그램(MemoO)</h2>
      <p>
        프로그램은 <b>어떠한 개인정보도 수집하거나 전송하지 않습니다.</b> 녹음 파일, 변환된 텍스트, 설정 값은 모두
        사용자 PC의 <code>%LOCALAPPDATA%\MemoO</code> 폴더에만 저장되며, 프로그램은 인터넷에 연결하지 않습니다.
        운영자는 사용자의 녹음이나 텍스트에 접근할 수 없습니다. 저장된 데이터는 프로그램에서 삭제하거나,
        프로그램 제거 시 함께 삭제할 수 있습니다.
      </p>

      <h2>2. 사이트에서 처리하는 정보</h2>
      <p>운영자는 사이트에서 회원가입을 받지 않으며, 이름·연락처 등 개인정보를 직접 수집하지 않습니다. 다만 다음 정보가 자동으로 처리될 수 있습니다.</p>
      <ul>
        <li><b>접속 기록</b>: IP 주소, 브라우저 종류, 접속 시각 등 — 호스팅 사업자(Vercel Inc.)가 서비스 제공과 보안을 위해 처리합니다.</li>
        <li><b>쿠키 및 광고 식별자</b>: Google AdSense 광고 제공을 위해 Google 및 제3자 광고 사업자가 쿠키를 사용합니다.</li>
        <li><b>다운로드</b>: 설치 파일은 GitHub(GitHub, Inc.)에서 제공되며, 다운로드 시 GitHub의 개인정보처리방침이 적용됩니다.</li>
      </ul>

      <h2>3. 광고와 쿠키 (Google AdSense)</h2>
      <ul>
        <li>Google을 포함한 제3자 공급업체는 쿠키를 사용하여 사용자가 이 사이트나 다른 웹사이트를 방문한 기록을 바탕으로 광고를 게재합니다.</li>
        <li>Google은 광고 쿠키를 사용하여 사용자가 이 사이트 및 인터넷의 다른 사이트를 방문한 기록을 바탕으로 Google 및 파트너가 사용자에게 적절한 광고를 게재할 수 있도록 합니다.</li>
        <li>
          사용자는 <a href="https://adssettings.google.com" rel="noopener">Google 광고 설정</a>에서 맞춤 광고를 사용 중지할 수 있으며,
          <a href="https://www.aboutads.info/choices" rel="noopener">www.aboutads.info</a>에서 제3자 공급업체의 맞춤 광고용 쿠키를 사용 중지할 수 있습니다.
        </li>
        <li>
          Google이 데이터를 사용하는 방식은
          <a href="https://policies.google.com/technologies/partner-sites" rel="noopener">Google 파트너 사이트 데이터 사용 정책</a>에서 확인할 수 있습니다.
        </li>
        <li>브라우저 설정에서 쿠키 저장을 거부할 수 있으며, 이 경우에도 다운로드 등 사이트 이용에는 지장이 없습니다.</li>
      </ul>

      <h2>4. 보관 기간과 파기</h2>
      <p>
        운영자가 직접 보관하는 개인정보는 없습니다. 호스팅 및 광고 사업자가 처리하는 정보는 각 사업자의 방침에 따라 보관·파기됩니다.
      </p>

      <h2>5. 국외 이전</h2>
      <p>
        사이트 호스팅(Vercel Inc., 미국), 광고(Google LLC, 미국), 파일 배포(GitHub, Inc., 미국) 과정에서 접속 기록과 쿠키 정보가
        해당 사업자의 해외 서버에서 처리될 수 있습니다.
      </p>

      <h2>6. 이용자의 권리</h2>
      <p>
        이용자는 언제든지 쿠키 설정을 변경하거나 맞춤 광고를 거부할 수 있습니다. 개인정보와 관련한 문의는 아래 연락처로 보내주시면 지체 없이 답변드리겠습니다.
      </p>

      <h2>7. 문의처</h2>
      <ul>
        <li>운영자: minulog</li>
        <li v-if="CONTACT_EMAIL">이메일: <a :href="`mailto:${CONTACT_EMAIL}`">{{ CONTACT_EMAIL }}</a></li>
      </ul>

      <h2>8. 방침의 변경</h2>
      <p>본 방침이 변경되는 경우 시행일과 함께 이 페이지에 게시합니다.</p>

      <p><RouterLink to="/memo-o">← MemoO 다운로드 페이지로</RouterLink></p>
    </div>
  </article>
</template>

<script setup>
import { CONTACT_EMAIL } from '../config.js'
const EFFECTIVE_DATE = '2026년 9월 18일'
</script>
