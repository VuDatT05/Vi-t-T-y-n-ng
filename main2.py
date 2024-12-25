from flask import Flask, render_template, request, jsonify
import os
import json
import unicodedata
import sys

app = Flask(__name__)

# Xác định đường dẫn file khi chạy dưới dạng EXE
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS  # PyInstaller tạm thời giải nén các file
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn file từ điển
DEFAULT_DICTIONARY_PATH_VN_TN = os.path.join(application_path, 'taydictionary.json')
DEFAULT_DICTIONARY_PATH_TN_VN = os.path.join(application_path, 'vietdictionary.json')

def chuan_hoa_unicode(text):
    """Chuẩn hóa chuỗi Unicode."""
    return unicodedata.normalize('NFC', text.strip().lower()) if text else ""

def tai_tu_dien(path):
    """Tải từ điển."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return {}, f"Lỗi: {str(e)}"

def dich_cau(cau, tu_dien):
    """Dịch câu."""
    cau_chuan = chuan_hoa_unicode(cau)
    tu_da_dich = []
    tu_list = cau_chuan.split()

    i = 0
    while i < len(tu_list):
        found = False
        # Kiểm tra các cụm từ dài hơn trước (từ 2 từ trở lên)
        for j in range(len(tu_list), i, -1):
            cum_tu = " ".join(tu_list[i:j])
            tu_dich = tu_dien.get(cum_tu)
            if tu_dich:
                tu_da_dich.append(tu_dich if not isinstance(tu_dich, list) else tu_dich[0])
                i = j
                found = True
                break

        # Nếu không tìm thấy cụm từ dài, tra cứu từ đơn
        if not found:
            tu_dich = tu_dien.get(tu_list[i], tu_list[i])
            tu_da_dich.append(tu_dich if not isinstance(tu_dich, list) else tu_dich[0])
            i += 1

    return " ".join(tu_da_dich)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cau_goc = request.form.get('text_input', '')
        mode = request.form.get('mode', 'vn_to_tn')

        if mode == 'tn_to_vn':
            tu_dien, error_msg = tai_tu_dien(DEFAULT_DICTIONARY_PATH_TN_VN)
        else:
            tu_dien, error_msg = tai_tu_dien(DEFAULT_DICTIONARY_PATH_VN_TN)

        if error_msg:
            return jsonify({"ket_qua": error_msg})
        if not cau_goc.strip():
            return jsonify({"ket_qua": "Vui lòng nhập văn bản cần dịch."})

        ket_qua = dich_cau(cau_goc, tu_dien)
        return jsonify({"ket_qua": ket_qua})

    return render_template('index.html')

@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('q', '').strip().lower()
    mode = request.args.get('mode', 'vn_to_tn')

    if mode == 'tn_to_vn':
        tu_dien, error_msg = tai_tu_dien(DEFAULT_DICTIONARY_PATH_TN_VN)
    else:
        tu_dien, error_msg = tai_tu_dien(DEFAULT_DICTIONARY_PATH_VN_TN)

    if error_msg or not query:
        return jsonify({"suggestions": []})

    suggestions = [tu for tu in tu_dien.keys() if tu.startswith(query)]
    return jsonify({"suggestions": suggestions})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
