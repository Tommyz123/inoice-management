@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Installation complete.
echo Please create a .env file with your Supabase credentials.
echo You can copy the .env.example file to .env and fill in the values.
pause
