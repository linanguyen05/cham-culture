from flask import Flask, render_template

app = Flask(__name__)

# 1. Trang chủ (Tổng quan)
@app.route("/")
@app.route("/learn.html") # Thêm dòng này để bấm link learn.html không bị lỗi
def home():
    return render_template("learn.html")

# 2. Trang Nguồn gốc
@app.route('/nguon-goc.html')
def nguon_goc():
    return render_template('nguon-goc.html')

# 3. Trang Dân số
@app.route('/dan-so.html')
def dan_so():
    return render_template('dan-so.html')

# 4. Trang Ngôn ngữ
@app.route('/ngon-ngu.html')
def ngon_ngu():
    return render_template('ngon-ngu.html')

# 5. Trang Khu vực
@app.route('/khu-vuc.html')
def khu_vuc():
    return render_template('khu-vuc.html')
# LUÔN ĐỂ DÒNG NÀY Ở CUỐI CÙNG
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)   
