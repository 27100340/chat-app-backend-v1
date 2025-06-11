from mangum import Mangum
from main import app

# Create mangum handler
handler = Mangum(app)