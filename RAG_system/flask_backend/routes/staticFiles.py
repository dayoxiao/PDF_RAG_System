print("載入 static_bp")

from flask import Blueprint, send_from_directory

static_bp = Blueprint('static', __name__)

@static_bp.route('/api/figure_storage/<path:filename>', methods=['GET'])
def serve_figure(filename):
    """
    提供 figure_storage 目錄下的圖片文件
    
    Args:
        filename: 請求的文件名稱
        
    Returns:
        請求的文件內容
    """
    return send_from_directory('figure_storage', filename) 