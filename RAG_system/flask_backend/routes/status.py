print("載入 system_status_bp")

from flask import Blueprint, jsonify
from datetime import datetime
import psutil

system_status_bp = Blueprint('system_status', __name__)

@system_status_bp.route('/api/status', methods=['GET'])
def get_status():
    try:
        # 獲取CPU和內存使用率
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        
        status = {
            'status': 'idle',  # 'idle', 'processing', 'error'
            'message': '系統就緒',
            'cpuUsage': cpu_usage,
            'memoryUsage': memory_usage,
            'lastUpdated': datetime.now().isoformat()
        }
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': f'獲取系統狀態時出錯: {str(e)}'}), 500
