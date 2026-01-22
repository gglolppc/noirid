import os

from dotenv import load_dotenv


merchant_code = os.getenv("TCO_MERCHANT_CODE", "")

print(merchant_code)

