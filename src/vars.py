from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
JUNIT_JAR_VERSION = os.getenv('JUNIT_JAR_VERSION')
