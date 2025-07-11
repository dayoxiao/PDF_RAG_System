from flask import Flask, jsonify
from flask_cors import CORS

from routes.upload import upload_bp
from routes.models import models_bp
from routes.collections import collections_bp
from routes.collectionStatus import status_bp
from routes.chat import chat_bp
from routes.status import system_status_bp
from routes.docRemove import delete_bp
from routes.knowledgeBases import kb_bp
from routes.knowledgeBasesDoc import docKB_bp
from routes.staticFiles import static_bp

from routes.util.qdrant_util import qdrant_DBConnector
vector_db = qdrant_DBConnector("預設向量數據庫", recreate=False)

app = Flask(__name__)
CORS(app)

@app.route('/')
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'Service is running',
        'version': '1.0.0'
    })

app.register_blueprint(system_status_bp)
app.register_blueprint(models_bp)
app.register_blueprint(collections_bp)
app.register_blueprint(status_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(delete_bp)
app.register_blueprint(kb_bp)
app.register_blueprint(docKB_bp)
app.register_blueprint(static_bp)
app.register_blueprint(upload_bp)

if __name__ == '__main__':
    #app.run(debug=True, port=5050)
    app.run(host='0.0.0.0', port=5050)