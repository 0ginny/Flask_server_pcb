from flask import Flask, request, jsonify
from flask_cors import CORS  # CORS 패키지 임포트
import cx_Oracle
import json

app = Flask(__name__)

# CORS 설정 추가
CORS(app)  # 모든 도메인에 대해 CORS 허용
# 또는 특정 도메인에 대해서만 CORS를 허용하려면 아래와 같이 설정
# CORS(app, resources={r"/search": {"origins": "http://192.168.56.1:5501"}})

with open('oracle_config.json','r') as f:
    oracle_config = json.load(f)

# Oracle 연결 함수
def get_oracle_connection():
    return cx_Oracle.connect(
        oracle_config['user'],
        oracle_config['password'],
        oracle_config['dsn']
    )



@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    start_date = data.get('start')
    end_date = data.get('end')

    print("Start date:", start_date)
    print("End date:", end_date)

    if not start_date or not end_date:
        return jsonify({'error': 'Both start and end dates are required.'}), 400

    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()

        query = """
        SELECT 
            ps.PRODUCT_ID,
            ps.INSPECTION_START_TIME,
            ps.INSPECTION_COMPLETE_TIME,
            ps.IS_DEFECT,
            ins.ERROR_TYPE,
            ins.WIDTH,
            ins.HEIGHT
        FROM 
            PRODUCT_STATE ps
        JOIN 
            INSPECT_STATE ins ON ps.PRODUCT_ID = ins.PRODUCT_ID
        WHERE 
            ps.INSPECTION_START_TIME BETWEEN TO_DATE(:start_date, 'YYYY-MM-DD') AND TO_DATE(:end_date, 'YYYY-MM-DD')
        """

        # 바인드 변수를 전달할 때 명확하게 전달
        cursor.execute(query, start_date=start_date, end_date=end_date)

        rows = cursor.fetchall()

        print("Rows fetched from database:", rows)

        columns = [col[0].lower() for col in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]

        print("JSON response:", results)

        cursor.close()
        connection.close()

        return jsonify(results)

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print("Database error occurred:", error)
        return jsonify({'error': str(error)}), 500

if __name__ == '__main__':
    app.run(debug=True)