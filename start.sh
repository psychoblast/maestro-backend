#\!/bin/bash
cd /home/tommy/maestro

echo ""
echo "  Maestro — AI Artist Team"
echo "  Open: http://localhost:8765"
echo "  export ANTHROPIC_API_KEY=sk-ant-... (if needed)"
echo ""

python3 -m uvicorn main:app --host 0.0.0.0 --port 8765 --reload
