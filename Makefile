install:   ; pip install -r requirements.txt && cd frontend && npm install
api:       ; uvicorn api.main:app --reload --port 8000
web:       ; cd frontend && npm run dev
test:      ; python -m pytest -q
check-web: ; cd frontend && npm run typecheck && npm run lint && npm run build
demo:      ; python scripts/run_cli.py data/samples/reunion_site_web.txt --date 2026-10-26
eval:      ; python scripts/evaluate.py --modes offline
docker:    ; docker compose up --build
