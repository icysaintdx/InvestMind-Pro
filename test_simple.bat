@echo off
cd /d d:\InvestMindPro
echo Running fallback integration test...
python -c "from backend.utils.llm_fallback_handler import get_fallback_handler; h=get_fallback_handler(); print('Fallback handler OK'); r=h._get_default_response('RISK', 'test'); print('Default response OK'); print('First 50 chars:', r['choices'][0]['message']['content'][:50])"
echo Test completed
pause
