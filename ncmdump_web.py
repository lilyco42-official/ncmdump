#!/usr/bin/env python3
import os
import tempfile
from io import BytesIO
from flask import Flask, request, send_file, render_template_string
from ncmdump import NeteaseCloudMusicFile

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>网易云音乐 NCM 转 MP3</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
        }
        h1 { text-align: center; color: #333; margin-bottom: 30px; }
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s;
            cursor: pointer;
            position: relative;
        }
        .upload-area:hover { border-color: #667eea; background: #f8f9ff; }
        .upload-area.dragover { border-color: #667eea; background: #f0f3ff; }
        .upload-icon { font-size: 48px; margin-bottom: 15px; }
        .upload-text { color: #666; }
        #fileInput { display: none; }
        .btn {
            display: block;
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            display: none;
        }
        .result.success { background: #d4edda; color: #155724; }
        .result.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 NCM 转 MP3</h1>
        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📁</div>
            <div class="upload-text">点击或拖拽 NCM 文件到此处</div>
        </div>
        <input type="file" id="fileInput" accept=".ncm">
        <button class="btn" id="convertBtn" disabled>转换</button>
        <div class="result" id="result"></div>
    </div>
    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const convertBtn = document.getElementById('convertBtn');
        const result = document.getElementById('result');
        let selectedFile = null;

        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                handleFile(e.dataTransfer.files[0]);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleFile(e.target.files[0]);
            }
        });
        
        function handleFile(file) {
            if (!file.name.toLowerCase().endsWith('.ncm')) {
                showResult('请选择 NCM 格式文件', 'error');
                return;
            }
            selectedFile = file;
            convertBtn.disabled = false;
            convertBtn.textContent = '转换: ' + file.name;
            result.style.display = 'none';
        }
        
        convertBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            
            convertBtn.disabled = true;
            convertBtn.textContent = '转换中...';
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            try {
                const response = await fetch('/convert', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = selectedFile.name.replace('.ncm', '.mp3');
                    a.click();
                    URL.revokeObjectURL(url);
                    showResult('转换成功！文件已下载', 'success');
                } else {
                    const text = await response.text();
                    showResult('转换失败: ' + text, 'error');
                }
            } catch (err) {
                showResult('转换失败: ' + err.message, 'error');
            }
            
            convertBtn.disabled = false;
            convertBtn.textContent = '转换';
        });
        
        function showResult(msg, type) {
            result.textContent = msg;
            result.className = 'result ' + type;
            result.style.display = 'block';
        }
    </script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        return "No file selected", 400

    if not file.filename.lower().endswith(".ncm"):
        return "Please upload NCM file", 400

    try:
        with tempfile.NamedTemporaryFile(suffix=".ncm", delete=False) as tmp_input:
            tmp_input.write(file.read())
            tmp_input_path = tmp_input.name

        try:
            ncm = NeteaseCloudMusicFile(tmp_input_path)
            ncm.decrypt()

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_output:
                tmp_output_path = tmp_output.name

            ncm.dump_music(tmp_output_path)

            with open(tmp_output_path, "rb") as f:
                mp3_data = f.read()

            os.unlink(tmp_output_path)

            if len(mp3_data) == 0:
                return "Invalid NCM file - empty output", 400

            return send_file(
                BytesIO(mp3_data),
                mimetype="audio/mpeg",
                as_attachment=True,
                download_name=file.filename.replace(".ncm", ".mp3"),
            )
        finally:
            os.unlink(tmp_input_path)

    except Exception as e:
        return f"Conversion error: {str(e)}", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
