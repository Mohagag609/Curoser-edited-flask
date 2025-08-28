from app import app
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)