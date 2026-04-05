# automation project
## 개요
**네트워크 환경에서 데이터 파이프라인 구축**
***
많은 화학회사의 품질관리자들은 화학 분석 계측기로 검출한 피분석원(anayte)을 규격에 맞춰 관리하길 원한다. 적시에 계측기 또는 공정 이상 여부를 발견하고 적소에 대응 방안을 하달하길 바란다. 특히 계측기 부분에 있어 기기의 유지보수가 관건이다. 이 프로젝트는 여기서 출발했다. 서버의 컴퓨터는 네트워크의 분석장비들의 raw data를 확인하고 검출된 피분석원들이 정규분포를 따른다고 가정하여 데이터로 확인하되 이를 벗어났을 때 적절한 조치를 취할 수 있도록 보고서를 발송한다.<br/>
  
  

## 기능
`generate.data.py`<br/>
		계측기에서 생성되는 raw data 시뮬레이션 - 주어진 기간 동안에 발생한 데이터들을 csv파일로 생성<br/>
`watcher.py`<br/>
		신규 raw data 감지 - 다수의 계측기에서 생성된 파일들을 실시간으로 감지하여 서버의 raw.data폴더에 저장<br/>
`processed.data.py`<br/>
		raw data 정제 - 주요 데이터가 규격에 벗어나는지 또는 결측치인지 판단하여 기록  

## 구조 - 폴더 및 네트워크
<img width="960" height="540" alt="Image" src="https://github.com/user-attachments/assets/f57432b3-fe81-4e5a-8a05-25a2b30141d4" />  

## 기술스택
![Python](https://img.shields.io/badge/Python-3.12.3-blue?style=plastic&logo=Python&logoColor=3776AB) ![PostgreSQL](https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white) ![GIT](https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white)
