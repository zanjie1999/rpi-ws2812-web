# coding=UTF-8

# ws2812b 灯带控制
# RGB!
# Sparkle
# Ver 2.0

import time
import threading
import board
import neopixel
from flask import Flask, jsonify
app = Flask(__name__)

ledNum = 30

pixels = neopixel.NeoPixel(board.D10, ledNum, brightness=0.5, auto_write=True, pixel_order=neopixel.GRB)
rainbowRuning = False

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="zh-cn">
<head>
    <meta charset="utf-8" name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, minimum-scale=1.0, maximum-scale=1.0"/>
    <title>RGB!</title>
    <script src="https://cdn.bootcss.com/jquery/1.12.4/jquery.min.js"></script>
    <style>
    input {height: 80px;}
    button {height: 80px;}
    </style>
</head>
<body>
    <h2>选择一个颜色</h2>
    <input type="color" id="color" style="width: 100px;"> <button style="width: 60px;" onclick="setall()">设置</button><br><br>
    <h4>范围控制:</h4>
    <button onclick="index.value='1-5'" style="width: 55px;">1-5</button> <button onclick="index.value='6-24'" style="width: 55px;">6-24</button> <button onclick="index.value='25-30'" style="width: 55px;">25-30</button><br><br>
    <input placeholder="灯序号或范围" id="index" style="width: 90px;"> <button style="width: 60px;" onclick="setone()">设置</button><br><br>
    <h4>模式:</h4>
    <button onclick="color.value='#000000';setall()" style="width: 55px;">关</button> <button onclick="color.value='#ffffcc';setall()" style="width: 55px;">白</button> <button onclick="color.value='#020202';setall()" style="width: 55px;">夜灯</button> <button onclick="rainbow()" style="width: 55px;">彩虹</button><br><br>
<script>
    function rainbow() {
        $.get("/rainbow", function (d) {
                if (!d.success) {
                    $('#msg').html(d.msg);
                }
                console.log(d.rainbowRuning);
        });
    }
    function setall() {
        var hex = $("#color").val().replace(/#/, "");
        console.log(hex);
        $.get("/setall/" + hex, function (d) {
                if (!d.success) {
                    $('#msg').html(d.msg);
                }
        });
    }
    function setone(){
        var hex = $("#color").val().replace(/#/, "");
        var index = $("#index").val();
        if (index === ''){
            alert("请填写 灯序号 或 范围");
            return;
        }
        console.log(hex)
        $.get("/setone/" + index + "/" + hex, function (d) {
                if (!d.success) {
                    $('#msg').html(d.msg);
                }
        });
    }
</script>
</body>
</html>
    '''

@app.route('/setall/<hex>')
def setall(hex):
    global rainbowRuning
    if (rainbowRuning):
        rainbowRuning = False
        pixels.auto_write = True

    c = colorCovert("#" + hex)
    print("#" + hex, c)
    pixels.fill(c)
    return jsonify({
        'success': True
    })

@app.route('/setone/<index>/<hex>')
def setone(index, hex):
    global rainbowRuning
    if (rainbowRuning):
        rainbowRuning = False
        pixels.auto_write = True
    
    c = colorCovert("#" + hex)
    print(index, "#" + hex, c)
    if '-' in index:
        l = index.split('-')
        l[0] = int(l[0])
        l[1] = int(l[1])
        if l[0] > 0 and l[1] <= ledNum:
            for i in range(l[0]-1, l[1]):
                pixels[i] = c
        else:
            return jsonify({
                'success': False,
                'msg':'超出范围'
            })
    else:
        index = int(index)
        if index in range(1, ledNum+1):
            pixels[index-1] = c
        else:
            return jsonify({
                'success': False,
                'msg':'超出范围'
            })

    
    return jsonify({
        'success': True
    })

@app.route('/rainbow')
def rainbow():
    global rainbowRuning
    if (rainbowRuning):
        print('Rainbow Stop')
        rainbowRuning = False
        pixels.auto_write = True
    else:
        print('Rainbow Start')
        rainbowRuning = True
        pixels.auto_write = False
        tRainbow = threading.Thread(target=rainbowCycle)
        tRainbow.start()

    return jsonify({
        'success': True,
        'rainbowRuning': rainbowRuning
    })

def colorCovert(value):
    digit = list(map(str, range(10))) + list("abcdef")
    if isinstance(value, tuple):
        string = '#'
        for i in value:
            a1 = i // 16
            a2 = i % 16
            string += digit[a1] + digit[a2]
        return string
    elif isinstance(value, str):
        value = value.lower()
        a1 = digit.index(value[1]) * 16 + digit.index(value[2])
        a2 = digit.index(value[3]) * 16 + digit.index(value[4])
        a3 = digit.index(value[5]) * 16 + digit.index(value[6])
        return (a1, a2, a3)

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos*3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos*3)
        g = 0
        b = int(pos*3)
    else:
        pos -= 170
        r = 0
        g = int(pos*3)
        b = int(255 - pos*3)
    return (r, g, b)

def rainbowCycle():
    global rainbowRuning
    while True:
        for j in range(255):
            for i in range(ledNum):
                pixel_index = (i * 256 // ledNum) + j
                pixels[i] = wheel(pixel_index & 255)
                if not rainbowRuning:
                    return
            pixels.show()
            time.sleep(0.001)

def keepJob():
    global pixels
    if not rainbowRuning:
        pixels.write()
    time.sleep(60)


pixels.fill((2,2,2))
tKeep = threading.Thread(target=keepJob)
tKeep.start()

app.run('0.0.0.0', 8082, True, use_reloader=False)
