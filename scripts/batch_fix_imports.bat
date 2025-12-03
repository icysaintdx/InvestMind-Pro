@echo off
echo Starting batch import fix...
echo.

REM Fix all Python files in agents directory
powershell -Command "(Get-Content -Path 'agents\__init__.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\__init__.py'"
powershell -Command "(Get-Content -Path 'agents\analysts\fundamentals_analyst.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\analysts\fundamentals_analyst.py'"
powershell -Command "(Get-Content -Path 'agents\analysts\market_analyst.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\analysts\market_analyst.py'"
powershell -Command "(Get-Content -Path 'agents\analysts\social_media_analyst.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\analysts\social_media_analyst.py'"
powershell -Command "(Get-Content -Path 'agents\managers\research_manager.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\managers\research_manager.py'"
powershell -Command "(Get-Content -Path 'agents\managers\risk_manager.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\managers\risk_manager.py'"
powershell -Command "(Get-Content -Path 'agents\researchers\bear_researcher.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\researchers\bear_researcher.py'"
powershell -Command "(Get-Content -Path 'agents\researchers\bull_researcher.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\researchers\bull_researcher.py'"
powershell -Command "(Get-Content -Path 'agents\risk_mgmt\aggresive_debator.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\risk_mgmt\aggresive_debator.py'"
powershell -Command "(Get-Content -Path 'agents\risk_mgmt\conservative_debator.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\risk_mgmt\conservative_debator.py'"
powershell -Command "(Get-Content -Path 'agents\risk_mgmt\neutral_debator.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\risk_mgmt\neutral_debator.py'"
powershell -Command "(Get-Content -Path 'agents\trader\trader.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\trader\trader.py'"
powershell -Command "(Get-Content -Path 'agents\utils\agent_states.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\utils\agent_states.py'"
powershell -Command "(Get-Content -Path 'agents\utils\agent_utils.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\utils\agent_utils.py'"
powershell -Command "(Get-Content -Path 'agents\utils\memory.py' -Raw) -replace 'from backend.utils.logging_init', 'from backend.utils.logging_config' | Set-Content -Path 'agents\utils\memory.py'"

echo.
echo Import fix completed!
pause
