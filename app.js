const agents=[

{
name:"김현수",
img:"agent1.png",
city:"동관",
score:[92,88,91,95,90,94]
},

{
name:"Alex Chen",
img:"agent2.png",
city:"상하이",
score:[87,84,88,89,86,87]
}

]

function show(id){

document.querySelectorAll(".screen")
.forEach(s=>s.style.display="none")

document.getElementById(id).style.display="block"

}

window.onload=function(){

setTimeout(function(){

document.getElementById("splash").style.display="none"

show("home")

loadAgents()

},2000)

}

function goHome(){
show("home")
}

function loadAgents(){

let list=document.getElementById("agentList")

list.innerHTML=""

agents.forEach((a,i)=>{

list.innerHTML+=`

<div class="agentCard" onclick="openProfile(${i})">

<img src="${a.img}">

<div>

<h3>${a.name}</h3>

<p>${a.city}</p>

</div>

</div>

`

})

}

function openProfile(i){

show("profile")

let a=agents[i]

profileImg.src=a.img
profileName.innerText=a.name

profileDesc.innerHTML=`

위치 : ${a.city}

언어 : 한국어 / 영어

전문 :
공장 실사
공급망 조사
바이어 미팅

수행 미션 : 120+

성공률 : 97%

`

new Chart(agentRadar,{
type:'radar',
data:{
labels:["정확도","속도","소통","전문성","보고","신뢰"],
datasets:[{
data:a.score,
backgroundColor:"rgba(59,130,246,0.4)"
}]
}
})

}

function createMission(){

show("escrow")

}

function client(text){
return `<div class="chat client"><div class="bubble">${text}</div></div>`
}

function agent(text){
return `<div class="chat agent"><div class="bubble">${text}</div></div>`
}

function startChat(){

show("chat")

let c=document.getElementById("chatbox")

c.innerHTML=""

setTimeout(()=>{c.innerHTML+=client("안녕하세요\n공장 실사 요청드립니다")},1000)

setTimeout(()=>{c.innerHTML+=agent("현재 공장으로 이동 중입니다\n30분 후 도착 예정입니다")},3000)

setTimeout(()=>{c.innerHTML+=client("생산라인 가동 여부\n작업 인원\n창고 재고 확인 부탁드립니다")},6000)

setTimeout(()=>{c.innerHTML+=agent("네 확인 후 보고드리겠습니다")},8000)

setTimeout(()=>{c.innerHTML+=agent("현장 도착했습니다")},10000)

setTimeout(()=>{c.innerHTML+=`<img src="factory.png">`},12000)

setTimeout(()=>{c.innerHTML+=agent("현재 생산라인 2개 가동 중입니다\n작업 인원 약 15명 확인됩니다")},15000)

setTimeout(()=>{c.innerHTML+=client("자동화 설비인지 확인 부탁드립니다")},18000)

setTimeout(()=>{c.innerHTML+=agent("반자동 생산라인입니다\n포장 공정은 수작업입니다")},21000)

setTimeout(()=>{c.innerHTML+=agent("창고 재고 약 2주 분량 확인됩니다")},24000)

setTimeout(()=>{c.innerHTML+=agent("AI 분석 결과\n정상 공장 확률 91%")},27000)

setTimeout(()=>{

c.innerHTML+=`
<button onclick="openRating()">
미션 종료
</button>
`

},30000)

}

function openRating(){
show("rating")
}

function finishMission(){

alert("평가가 제출되었습니다")

goHome()

}