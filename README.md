# stock_car v2

杩欐槸涓€涓熀浜?`Streamlit` 鐨勬柊鑳芥簮杞﹁偂绁ㄥ垎鏋愮郴缁?v1銆?
## 1. 鎭㈠杩愯鐜

寤鸿浣跨敤 Python `3.10.x`銆傚綋鍓嶄粨搴撳凡纭鍙敤鐗堟湰涓?`Python 3.10.8`銆?
Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. 閰嶇疆瀵嗛挜

椤圭洰涓殑 AI 鍒嗘瀽鍔熻兘浼氳鍙?`Streamlit secrets`銆?
鍏堝垱寤洪厤缃枃浠?

```powershell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

鐒跺悗鎶?`.streamlit/secrets.toml` 閲岀殑 `DEEPSEEK_API_KEY` 鏀规垚浣犺嚜宸辩殑 key銆?
濡傛灉涓嶉厤缃紝椤甸潰浠嶅彲鍚姩锛屼絾 AI 瀵硅瘽鍔熻兘浼氬洜鏃犳晥 key 澶辫触銆?
## 3. 鍚姩椤圭洰

```powershell
streamlit run app.py
```

榛樿浼氬湪鏈満娴忚鍣ㄦ墦寮€涓€涓?`Streamlit` 椤甸潰銆?
## 3.1 v2 鍚姩鏂瑰紡

v2 寮€濮嬪皢鍚庣鎷嗗垎涓?FastAPI 鏈嶅姟锛屽惎鍔ㄦ椂闇€瑕佸厛鍚姩鍚庣锛屽啀鍚姩鍓嶇銆?

鍚庣:

`powershell
.\.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
`

鍓嶇:

`powershell
.\.venv\Scripts\python -m streamlit run app.py
`

濡傛灉鍚庣鍦板潃涓嶆槸榛樿鐨?http://127.0.0.1:8000锛屽彲浠ュ湪 .streamlit/secrets.toml 涓坊鍔?BACKEND_BASE_URL銆?
## 4. 杩愯鏃剁敓鎴愮殑鏈湴鏂囦欢

杩欎簺鏂囦欢鏈潵灏变笉搴旇鎻愪氦鍒?git锛?
- `.venv/`
- `__pycache__/`
- `.streamlit/`
- `*.db`

鍏朵腑 `stock_data.db` 浼氬湪棣栨杩愯鏃惰嚜鍔ㄥ垱寤猴紝涓嶉渶瑕佹墜宸ユ仮澶嶃€?
## 5. 宸茬煡娉ㄦ剰浜嬮」

- `Prophet` 鍦?Windows 棣栨瀹夎鍙兘杈冩參銆?- `AkShare` 渚濊禆鑱旂綉鎷夊彇鑲＄エ涓庢柊闂绘暟鎹€?- 椤圭洰婧愮爜閲屽瓨鍦ㄩ儴鍒嗕腑鏂囩紪鐮佹樉绀哄紓甯革紝浣嗕笉褰卞搷褰撳墠鍏堟仮澶?v1 杩愯锛涘悗缁仛 v2 鏃跺缓璁粺涓€杞负 UTF-8銆?

