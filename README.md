uvicorn app.main:app --reload
uvicorn app.main:clipcatch_app --host 0.0.0.0 --port $PORT
ssh -i .\LightsailDefaultKey-eu-central-1.pem bitnami@3.79.188.77



